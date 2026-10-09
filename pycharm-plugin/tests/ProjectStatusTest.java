package agent.notifier;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;

/** Runs the real shell writer and Java reader with isolated projects and fake terminal devices. */
public final class ProjectStatusTest {
  private static Path temp, cache, dev, script, one, two;
  private static void equal(Object actual, Object expected) {
    if (!actual.equals(expected)) throw new AssertionError("expected " + expected + ", got " + actual);
  }
  private static void report(String action, String agent, String tty, Path project) throws Exception {
    var builder = new ProcessBuilder("/bin/sh", script.toString(), action, agent,
      Long.toString(ProcessHandle.current().pid()), project.toString(), tty);
    builder.environment().put("AGENT_STATUS_STATE_DIR", cache.toString());
    builder.environment().put("AGENT_STATUS_DEV_DIR", dev.toString());
    equal(builder.start().waitFor(), 0);
  }
  private static String title(Path project) {
    return ProjectStatus.titleFor(ProjectStatus.read(cache, pid -> ProcessHandle.of(pid).map(ProcessHandle::isAlive).orElse(false)), project);
  }
  public static void main(String[] args) throws Exception {
    script = Path.of(args[0]).toAbsolutePath();
    temp = Files.createTempDirectory("notifier-plugin-test-").toRealPath();
    cache = temp.resolve("cache");
    dev = Files.createDirectories(temp.resolve("dev"));
    one = Files.createDirectories(temp.resolve("one"));
    two = Files.createDirectories(temp.resolve("two"));
    try {
      for (String tty : new String[]{"ttys001", "ttys002", "ttys003", "ttys004"}) Files.writeString(dev.resolve(tty), "");
      equal(title(one), "");
      report("start", "Pi", "ttys001", one);
      equal(title(one), "1 running");
      report("start", "Claude", "ttys002", one);
      report("start", "Pi", "ttys003", one);
      report("stop", "Pi", "ttys001", one);
      report("stop", "Claude", "ttys002", one);
      equal(title(one), "2/3 finished · 1 running");
      equal(title(one.resolve("subdirectory")), "2/3 finished · 1 running");
      report("stop", "Pi", "ttys003", one);
      equal(title(one), "3/3 finished");
      report("start", "Pi", "ttys003", one);
      equal(title(one), "2/3 finished · 1 running");
      report("start", "Claude", "ttys004", two);
      equal(title(two), "1 running");
      equal(title(one), "2/3 finished · 1 running");
      equal(title(temp.resolve("one-other")), "");
      Path dir;
      try (var paths = Files.list(cache)) {
        dir = paths.filter(p -> { try { return Files.readString(p.resolve(".project")).strip().equals(one.toString()); }
          catch (Exception e) { return false; } }).findFirst().orElseThrow();
      }
      Files.writeString(dir.resolve("dead"), "working 999999999 Pi\n");
      Files.writeString(dir.resolve("invalid"), "working nope Pi\n");
      Files.writeString(dir.resolve(".entry.partial"), "working " + ProcessHandle.current().pid() + " Pi\n");
      equal(title(one), "2/3 finished · 1 running");
      equal(ProjectStatus.titleFor(ProjectStatus.read(cache, pid -> false), one), "");
      Files.writeString(dir.resolve("ttys003"), "working ");
      equal(title(one), "2/2 finished");
      Files.delete(dir.resolve(".project"));
      equal(title(one), "");
      equal(title(two), "1 running");
      System.out.println("PASS: shell → cache → project titles (start/stop/restart, three sessions, independent projects, dead/malformed/atomic entries, unavailable metadata)");
    } finally {
      try (var paths = Files.walk(temp)) {
        for (Path p : paths.sorted(Comparator.reverseOrder()).toList()) Files.deleteIfExists(p);
      }
    }
  }
}
