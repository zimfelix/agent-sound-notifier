package agent.notifier;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.function.LongPredicate;

/** Local, read-only snapshot. No IDE dependencies so the real filesystem boundary is testable. */
public final class ProjectStatus {
  public record Counts(int working, int done) {
    public String title() {
      int total = working + done;
      if (total == 0) return "";
      if (done == 0) return working + " running";
      return done + "/" + total + " finished" + (working == 0 ? "" : " · " + working + " running");
    }
  }

  public static Path cacheDirectory() {
    String override = System.getenv("AGENT_STATUS_STATE_DIR");
    if (override != null && !override.isBlank()) return Path.of(override);
    String xdg = System.getenv("XDG_CACHE_HOME");
    Path cache = xdg == null || xdg.isBlank() ? Path.of(System.getProperty("user.home"), ".cache") : Path.of(xdg);
    return cache.resolve("agent-sound-notifier");
  }

  public static Map<Path, Counts> read(Path cache, LongPredicate alive) {
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
                if (pid <= 1 || !alive.test(pid)) continue;
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
