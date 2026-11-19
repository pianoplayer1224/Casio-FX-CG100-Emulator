#!/bin/sh
# Keep the git-tracked copy of the emulator's MicroPython changes in step with
# the build tree. emu/micropython/ is upstream MicroPython v1.9.4 with its own
# .git, so the outer repo ignores it; what we changed lives here instead:
#
#     emu/port/cg100/          the cg100 port (a copy of micropython/ports/cg100)
#     emu/patches/py-cg100.patch   the core changes (git diff of micropython/py)
#
# Edit in emu/micropython as before, then:
#
#     emu/port.sh save      copy the port and regenerate the patch (before committing)
#     emu/port.sh check     say whether the tracked copy differs from the build tree
#     emu/port.sh restore   fresh clone: fetch v1.9.4, apply the patch, copy the port in;
#                           then run emu/build.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
MP="$HERE/micropython"
SNAP="$HERE/port/cg100"
PATCH="$HERE/patches/py-cg100.patch"
UPSTREAM="${MICROPYTHON_URL:-https://github.com/micropython/micropython.git}"
TAG=v1.9.4

# build outputs and the inner repo's own ignore file stay out of the copy
copy() {
  mkdir -p "$2"
  rsync -a --delete \
    --exclude=/build/ --exclude=/build-*/ \
    --exclude='/micropython' --exclude='/micropython.map' \
    --exclude='/micropython.new*' --exclude='/micropython_*' \
    --exclude=/.gitignore \
    "$1/" "$2/"
}

case "$1" in
  save)
    copy "$MP/ports/cg100" "$SNAP"
    git -C "$MP" diff -- py > "$PATCH"
    echo "saved port to emu/port/cg100 and core changes to emu/patches/py-cg100.patch"
    ;;
  check)
    status=0
    tmp="$(mktemp -d)"
    trap 'rm -rf "$tmp"' EXIT
    copy "$MP/ports/cg100" "$tmp/cg100"
    diff -r --no-dereference "$SNAP" "$tmp/cg100" >/dev/null || {
      echo "port differs:"; diff -rq --no-dereference "$SNAP" "$tmp/cg100" | sed "s|$tmp/cg100|micropython/ports/cg100|; s|$HERE/||"; status=1; }
    git -C "$MP" diff -- py | cmp -s - "$PATCH" || { echo "core patch differs from micropython/py"; status=1; }
    [ $status = 0 ] && echo "tracked copy matches the build tree" || echo "run emu/port.sh save"
    exit $status
    ;;
  restore)
    if [ ! -d "$MP/.git" ]; then
      git clone --branch "$TAG" --depth 1 "$UPSTREAM" "$MP"
    fi
    if git -C "$MP" diff --quiet -- py; then
      git -C "$MP" apply "$PATCH"
    else
      echo "micropython/py already has changes; not applying the patch"
    fi
    copy "$SNAP" "$MP/ports/cg100"
    cp "$MP/ports/unix/.gitignore" "$MP/ports/cg100/.gitignore"
    echo "restored; now run emu/build.sh"
    ;;
  *)
    sed -n '2,14p' "$0"; exit 2 ;;
esac
