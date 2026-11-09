#!/usr/bin/env bash
# レシピJSONから macOS の .app を作って dist/ に zip で置く。
set -euo pipefail

SPEC="${1:-specs/hello.json}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

rm -rf build/app dist
mkdir -p build/app dist

python3 scripts/render.py "$SPEC" build/app
set -a
# shellcheck disable=SC1091
. build/app/meta.env
set +a

APP="build/app/$APP_NAME.app"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp build/app/Info.plist "$APP/Contents/Info.plist"

echo "==> ${APP_NAME} v${VERSION} をコンパイル (macOS ${MIN_MACOS}+)"

# Apple Silicon
swiftc -parse-as-library -O \
  -target "arm64-apple-macos${MIN_MACOS}" \
  build/app/main.swift -o build/app/bin-arm64

# Intel（失敗しても続行 = arm64 のみで配布）
if swiftc -parse-as-library -O \
  -target "x86_64-apple-macos${MIN_MACOS}" \
  build/app/main.swift -o build/app/bin-x86_64 2> build/app/x86.log; then
  lipo -create build/app/bin-arm64 build/app/bin-x86_64 -output "$APP/Contents/MacOS/$SLUG"
  echo "==> universal (arm64 + x86_64)"
else
  cp build/app/bin-arm64 "$APP/Contents/MacOS/$SLUG"
  echo "::warning::Intel 版のビルドに失敗。arm64 のみで続行します"
fi
chmod +x "$APP/Contents/MacOS/$SLUG"

# ad-hoc 署名（証明書なしで動く最小構成）
codesign --force --sign - "$APP" >/dev/null 2>&1 || echo "::warning::codesign 失敗"
codesign --verify --deep --strict "$APP" && echo "==> 署名OK (ad-hoc)"

ZIP="dist/${SLUG}-${VERSION}-macos.zip"
ditto -c -k --sequesterRsrc --keepParent "$APP" "$ZIP"
( cd dist && shasum -a 256 "$(basename "$ZIP")" > "$(basename "$ZIP").sha256" )

echo "==> できあがり: $ZIP ($(du -h "$ZIP" | cut -f1))"
ls -lh dist
