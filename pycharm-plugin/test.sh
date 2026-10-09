#!/bin/sh
set -eu
cd "$(dirname "$0")"
ide=${PYCHARM_HOME:-/Applications/PyCharm.app/Contents}
jdk=${JAVA_HOME:-$ide/jbr/Contents/Home}
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT HUP INT TERM
"$jdk/bin/javac" --release 21 -encoding UTF-8 -d "$out" src/agent/notifier/ProjectStatus.java tests/ProjectStatusTest.java
"$jdk/bin/java" -cp "$out" agent.notifier.ProjectStatusTest ../hooks/agent-status.sh
classpath=$(find "$ide/lib" "$ide/plugins/terminal/lib" -name '*.jar' -print | paste -sd: -)
"$jdk/bin/javac" --release 21 -encoding UTF-8 -cp "$out:$classpath" -d "$out" src/agent/notifier/AgentFrameTitleBuilder.java tests/AgentFrameTitleBuilderTest.java
"$jdk/bin/java" -cp "$out:$classpath" agent.notifier.AgentFrameTitleBuilderTest
