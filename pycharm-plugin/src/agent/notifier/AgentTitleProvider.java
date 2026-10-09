package agent.notifier;

import com.intellij.openapi.Disposable;
import com.intellij.openapi.application.ApplicationManager;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.project.ProjectManager;
import com.intellij.openapi.util.Disposer;
import com.intellij.openapi.wm.impl.TitleInfoProvider;
import com.intellij.util.concurrency.AppExecutorUtil;
import kotlin.Unit;
import kotlin.jvm.functions.Function1;
import org.jetbrains.plugins.terminal.TerminalOptionsProvider;
import org.jetbrains.plugins.terminal.settings.TerminalApplicationTitleShowingMode;

import java.nio.file.Path;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

/** Each open project frame subscribes, including inactive macOS window tabs. */
public final class AgentTitleProvider implements TitleInfoProvider, Disposable {
  private record Subscription(Project project, Function1<? super TitleInfoProvider, Unit> callback) {}
  private final CopyOnWriteArrayList<Subscription> subscriptions = new CopyOnWriteArrayList<>();
  private volatile Map<Project, String> titles = Map.of();
  private volatile boolean disposed;
  private final ScheduledFuture<?> timer;

  public AgentTitleProvider() {
    var app = ApplicationManager.getApplication();
    Disposer.register(app, this);
    app.invokeLater(() -> {
      if (disposed || app.isDisposed()) return;
      enableAgentTabTitles();
    });
    // Native macOS frames need the global title topic even when no custom-header
    // listener subscribes. Do not tie polling to terminal focus or subscriptions.
    timer = AppExecutorUtil.getAppScheduledExecutorService().scheduleWithFixedDelay(this::refresh, 0, 1, TimeUnit.SECONDS);
  }

  @Override public boolean isActive(Project project) { return !getValue(project).isEmpty(); }
  @Override public String getValue(Project project) {
    return titles.getOrDefault(project, "");
  }
  @Override public String getBorderlessPrefix() { return " · "; }
  @Override public String getBorderlessSuffix() { return ""; }

  @Override public synchronized void addUpdateListener(Project project, Disposable parent,
      Function1<? super TitleInfoProvider, Unit> callback) {
    enableAgentTabTitles();
    Subscription subscription = new Subscription(project, callback);
    subscriptions.add(subscription);
    Disposer.register(parent, () -> remove(subscription));
    notifyOnUi();
  }

  private static void enableAgentTabTitles() {
    // This setting controls TERMINAL tabs, not just project frames. Disabling it
    // hides the OSC status dots even though the cache and project totals work.
    var options = TerminalOptionsProvider.getInstance();
    options.setApplicationTitleShowingMode(TerminalApplicationTitleShowingMode.ALWAYS);
    options.setShowApplicationTitle(true);
  }

  private synchronized void remove(Subscription subscription) {
    subscriptions.remove(subscription);
  }

  private void refresh() {
    if (disposed) return;
    try {
      Map<Path, ProjectStatus.Counts> next = ProjectStatus.read(ProjectStatus.cacheDirectory(),
        pid -> ProcessHandle.of(pid).map(ProcessHandle::isAlive).orElse(false));
      Map<Project, String> nextTitles = new java.util.HashMap<>();
      for (Project project : ProjectManager.getInstance().getOpenProjects()) {
        String base = project.getBasePath();
        if (!project.isDisposed() && base != null) {
          nextTitles.put(project, ProjectStatus.titleFor(next, Path.of(base)));
        }
      }
      if (!nextTitles.equals(titles)) {
        titles = Map.copyOf(nextTitles);
        notifyOnUi();
      }
    } catch (RuntimeException ignored) { /* an inaccessible cache/process must not stop subsequent updates */ }
  }

  private void notifyOnUi() {
    var app = ApplicationManager.getApplication();
    if (app.isDisposed()) return;
    app.invokeLater(() -> {
      if (disposed || app.isDisposed()) return;
      for (Subscription subscription : subscriptions) {
        if (!subscription.project().isDisposed()) subscription.callback().invoke(this);
      }
      // Also refresh the native frame titles; terminal focus is deliberately irrelevant.
      app.getMessageBus().syncPublisher(TitleInfoProvider.TOPIC).configurationChanged();
    });
  }

  @Override public synchronized void dispose() {
    disposed = true;
    timer.cancel(false);
    subscriptions.clear();
    titles = Map.of();
  }
}
