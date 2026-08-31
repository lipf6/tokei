#!/bin/bash
# Tokei fork 一键发布：打包 → GitHub Release → 下载校验。
# 用法：./release.sh [--notes "版本说明"]
set -euo pipefail
cd "$(dirname "$0")"

REPO="lipf6/tokei"
NOTES="${2:-}"
[ "${1:-}" = "--notes" ] || NOTES=""

VERSION="$(sed -nE 's/.*releaseTag = "v([^"]+)".*/\1/p' Tokei/Sources/Tokei/Updater.swift | head -n 1)"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "❌ 无法从 Updater.swift 读取版本号"; exit 1; }
TAG="v$VERSION"
echo "==> 目标版本: $TAG"

BRANCH="$(git branch --show-current)"
[ -n "$BRANCH" ] || { echo "❌ 游离 HEAD，先切到分支"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "❌ 工作区有未提交改动,先提交再发布"; exit 1
fi
git fetch -q origin "$BRANCH"
[ -z "$(git log HEAD..origin/$BRANCH --oneline)" ] || { echo "❌ 本地落后 origin/$BRANCH"; exit 1; }
[ -z "$(git log origin/$BRANCH..HEAD --oneline)" ] || { echo "❌ 有未 push 的提交"; exit 1; }
if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
    echo "❌ $REPO 已存在 $TAG"; exit 1
fi

echo "==> 打包"
# 公开发布固定 ad-hoc 签名：发布产物不能取决于构建机上恰好装了哪张个人证书。
( cd Tokei && TOKEI_CODESIGN_IDENTITY=- ./package.sh )
DMG="Tokei/Tokei.dmg"
[ -f "$DMG" ] || { echo "❌ DMG 未生成"; exit 1; }
LOCAL_SHA="$(shasum -a 256 "$DMG" | awk '{print $1}')"
echo "==> 本地 DMG sha256: $LOCAL_SHA"

echo "==> 创建 GitHub Release"
gh release create "$TAG" "$DMG#Tokei.dmg" --repo "$REPO" \
    --target "$BRANCH" --title "$TAG" --notes "${NOTES:-Release $TAG}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
gh release download "$TAG" --repo "$REPO" --pattern Tokei.dmg --dir "$TMP_DIR"
REMOTE_SHA="$(shasum -a 256 "$TMP_DIR/Tokei.dmg" | awk '{print $1}')"
[ "$REMOTE_SHA" = "$LOCAL_SHA" ] || { echo "❌ GitHub Release DMG 校验失败"; exit 1; }
echo "✅ $TAG 已发布到 ${REPO}，DMG sha256 校验一致"
