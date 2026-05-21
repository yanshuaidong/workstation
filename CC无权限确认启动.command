#!/bin/zsh
# 专用启动器（不是「随便打开 cc」）：
# - 先 cd 到本脚本所在仓库根目录，再启动；
# - 固定使用 Node 22（nvm use 22)；
# - 使用 --dangerously-skip-permissions（Bypass Permissions，运行命令前不再逐项问你）。
# 若仍出现 Bypass 免责声明：在用户级 ~/.claude/settings.json 设置
# skipDangerousModePermissionPrompt（项目内配置无效）。
# macOS 首次双击若被拦截：系统设置 → 隐私与安全性 → 仍要打开。

set -e

cd "$(dirname "$0")" || exit 1

export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [[ -s "$NVM_DIR/nvm.sh" ]]; then
  # shellcheck source=/dev/null
  . "$NVM_DIR/nvm.sh"
else
  echo "未找到 nvm（期望路径: $NVM_DIR/nvm.sh）" >&2
  exit 1
fi

nvm use 22

exec claude --dangerously-skip-permissions
