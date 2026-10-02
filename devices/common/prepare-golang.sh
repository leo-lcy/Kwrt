#!/bin/bash
set -euo pipefail

# The preferred kiddin9 feed supplies the Go host compiler. Packages in both
# feeds include helpers from feeds/packages/lang/golang, so copy the entire
# matching tree before installing packages and regenerate the packages index.
golang_source="feeds/kiddin9/golang"
golang_destination="feeds/packages/lang/golang"

for golang_file in golang-values.mk golang-package.mk golang-host-build.mk \
                   golang-version.mk golang-build.sh golang/Makefile \
                   golang-bootstrap/Makefile; do
    if [ ! -f "$golang_source/$golang_file" ]; then
        echo "Missing Go feed file: $golang_source/$golang_file" >&2
        exit 1
    fi
done

golang_version=$(sed -n 's/^GO_DEFAULT_VERSION:=//p' "$golang_source/golang-values.mk")
if [[ ! "$golang_version" =~ ^[0-9]+\.[0-9]+$ ]] || \
   [ ! -f "$golang_source/golang$golang_version/Makefile" ]; then
    echo "Go feed default version has no matching compiler: $golang_version" >&2
    exit 1
fi

rsync -a --delete "$golang_source/" "$golang_destination/"
./scripts/feeds update -i packages
echo "Go compiler and package helpers aligned to kiddin9 Go $golang_version"
