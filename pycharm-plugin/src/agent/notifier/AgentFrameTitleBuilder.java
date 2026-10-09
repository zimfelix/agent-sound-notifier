package agent.notifier;

import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.openapi.wm.impl.FrameTitleBuilder;

/** Keep project window titles independent of the selected editor or terminal.
 * Terminal tab titles remain enabled; AgentTitleProvider supplies project totals.
 */
public final class AgentFrameTitleBuilder extends FrameTitleBuilder {
  @Override public String getProjectTitle(Project project) {
    return project.getName();
  }

  @Override public String getFileTitle(Project project, VirtualFile file) {
    return "";
  }
}
