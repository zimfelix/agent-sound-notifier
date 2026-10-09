package agent.notifier;

import com.intellij.openapi.project.Project;
import java.lang.reflect.Proxy;
import java.nio.file.Files;
import java.nio.file.Path;

/** Exercise the real IDE title-builder API without launching or changing an IDE. */
public final class AgentFrameTitleBuilderTest {
  public static void main(String[] args) throws Exception {
    var builder = new AgentFrameTitleBuilder();
    for (String name : new String[]{"learning-sandbox", "agentic-harness-v6"}) {
      var project = (Project) Proxy.newProxyInstance(Project.class.getClassLoader(),
        new Class<?>[]{Project.class}, (proxy, method, values) -> {
          if (method.getName().equals("getName")) return name;
          throw new AssertionError("Unexpected project access: " + method.getName());
        });
      if (!builder.getProjectTitle(project).equals(name)) throw new AssertionError("Project name changed");
      if (!builder.getFileTitle(project, null).isEmpty()) throw new AssertionError("Selected file leaks into title");
      String title = builder.getProjectTitle(project) + " " + new ProjectStatus.Counts(1, 2).title();
      if (!title.equals(name + " 2/3 finished · 1 running")) throw new AssertionError(title);
    }
    String xml = Files.readString(Path.of("resources/META-INF/plugin.xml"));
    if (!xml.contains("serviceInterface=\"com.intellij.openapi.wm.impl.FrameTitleBuilder\"")
        || !xml.contains("serviceImplementation=\"agent.notifier.AgentFrameTitleBuilder\" overrides=\"true\"")) {
      throw new AssertionError("Project-only title builder must override the IDE service");
    }
    System.out.println("PASS: IDE title builder (project name only, no selected file/terminal, finished/running format, plugin wiring)");
  }
}
