#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
version=$(sed -n 's/^version = "\([^"]*\)"/\1/p' "$root/pyproject.toml")
out="$root/dist/openpatrol-$version-source.zip"
mkdir -p "$root/dist"
cd "$root"
git archive --format=zip --prefix="openpatrol-$version/" -o "$out" HEAD
sha256sum "$out" > "$out.sha256"
printf '%s\n' "$out"
