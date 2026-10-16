package agent.notifier;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/** Local, read-only snapshot. No IDE dependencies so the real filesystem boundary is testable. */
public final class ProjectStatus {
  public record Counts(int working, int done) {
    public String title() {
      int total = working + done;
      if (total == 0) return "";
      if (done == 0) return "⚪ " + working + " running";
      return "🟡 " + done + "/" + total + " finished" + (working == 0 ? "" : " · ⚪ " + working + " running");
    }
  }

  /**
   * A session counts only while its agent process still owns the terminal it reported from. A closed tab
   * leaves `claude` running without a terminal ("??"), and a reused PID belongs to another terminal or none.
   */
  public interface Sessions { boolean live(long pid, String tty); }

  /** One `ps` call per refresh, only when the cache contains entries to check. */
  public static Sessions fromPs() {
    return new Sessions() {
      private Map<Long, String> ttys;
      @Override public boolean live(long pid, String tty) {
        if (ttys == null) ttys = parsePs(runPs());
        return tty.equals(ttys.get(pid));
      }
    };
  }

  static Map<Long, String> parsePs(String output) {
    Map<Long, String> ttys = new HashMap<>();
    for (String line : output.split("\n")) {
      String[] fields = line.strip().split("\\s+");
      if (fields.length != 2) continue;
      try { ttys.put(Long.parseLong(fields[0]), fields[1]); }
      catch (NumberFormatException ignored) { /* header or garbage */ }
    }
    return ttys;
  }

  private static String runPs() {
    try {
      Process ps = new ProcessBuilder("/bin/ps", "-A", "-o", "pid=,tty=").redirectErrorStream(true).start();
      String output = new String(ps.getInputStream().readAllBytes());
      return ps.waitFor(2, TimeUnit.SECONDS) && ps.exitValue() == 0 ? output : "";
    } catch (IOException e) {
      return "";
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      return "";
    }
  }

  public static Path cacheDirectory() {
    String override = System.getenv("AGENT_STATUS_STATE_DIR");
    if (override != null && !override.isBlank()) return Path.of(override);
    String xdg = System.getenv("XDG_CACHE_HOME");
    Path cache = xdg == null || xdg.isBlank() ? Path.of(System.getProperty("user.home"), ".cache") : Path.of(xdg);
    return cache.resolve("agent-sound-notifier");
  }

  public static Map<Path, Counts> read(Path cache, Sessions sessions) {
    Map<Path, Counts> result = new HashMap<>();
    if (!Files.isDirectory(cache)) return Map.of();
    try (var dirs = Files.list(cache)) {
      for (Path dir : dirs.filter(Files::isDirectory).toList()) {
        try {
          Path root = canonical(Path.of(Files.readString(dir.resolve(".project")).strip()));
          int working = 0, done = 0;
          try (var entries = Files.list(dir)) {
            for (Path entry : entries.filter(p -> !p.getFileName().toString().startsWith(".") && Files.isRegularFile(p)).toList()) {
              try {
                String[] fields = Files.readString(entry).strip().split("\\s+");
                if (fields.length != 3 || !(fields[2].equals("Pi") || fields[2].equals("Claude"))) continue;
                long pid = Long.parseLong(fields[1]);
                if (pid <= 1 || !sessions.live(pid, entry.getFileName().toString())) continue;
                if (fields[0].equals("working")) working++;
                else if (fields[0].equals("done")) done++;
              } catch (IOException | IllegalArgumentException ignored) { /* replaced or invalid entry */ }
            }
          }
          result.put(root, new Counts(working, done));
        } catch (IOException | IllegalArgumentException ignored) { /* incomplete/old cache directory */ }
      }
    } catch (IOException ignored) { /* unavailable cache: clear stale UI, don't disturb the IDE */ }
    return Map.copyOf(result);
  }

  public static Path canonical(Path path) {
    try { return path.toRealPath(); }
    catch (IOException ignored) { return path.toAbsolutePath().normalize(); }
  }

  public static String titleFor(Map<Path, Counts> snapshot, Path project) {
    Path base = canonical(project);
    // A project opened below a Git root shares that root's agents; prefer the closest root.
    return snapshot.entrySet().stream().filter(e -> base.startsWith(e.getKey()))
      .max(java.util.Comparator.comparingInt(e -> e.getKey().getNameCount()))
      .map(e -> e.getValue().title()).orElse("");
  }
}
