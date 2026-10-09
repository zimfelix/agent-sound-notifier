#!/bin/sh
# Compile against the installed IDE, without downloading an IDE SDK or Gradle.
set -eu
cd "$(dirname "$0")"
ide=${PYCHARM_HOME:-/Applications/PyCharm.app/Contents}
jdk=${JAVA_HOME:-$ide/jbr/Contents/Home}
[ -x "$jdk/bin/javac" ] || { echo 'Set JAVA_HOME to a JDK (21+).' >&2; exit 1; }
[ -d "$ide/lib" ] || { echo 'Set PYCHARM_HOME to the IDE Contents directory.' >&2; exit 1; }
classpath=$(find "$ide/lib" "$ide/plugins/terminal/lib" -name '*.jar' -print | paste -sd: -)
rm -rf build
mkdir -p build/classes build/agent-project-status/lib
"$jdk/bin/javac" --release 21 -encoding UTF-8 -cp "$classpath" -d build/classes src/agent/notifier/*.java
cp -R resources/* build/classes/
# JBR includes javac but not always jar; use Python's standard ZIP implementation.
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
build = Path('build')
with ZipFile(build / 'agent-project-status/lib/agent-project-status.jar', 'w', ZIP_DEFLATED) as jar:
    for p in sorted((build / 'classes').rglob('*')):
        if p.is_file(): jar.write(p, p.relative_to(build / 'classes'))
with ZipFile(build / 'agent-project-status.zip', 'w', ZIP_DEFLATED) as archive:
    for p in sorted((build / 'agent-project-status').rglob('*')):
        if p.is_file(): archive.write(p, p.relative_to(build))
print((build / 'agent-project-status.zip').resolve())
PY
