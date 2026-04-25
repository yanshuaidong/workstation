#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
STAMP_FILE="$VENV_DIR/.requirements-installed"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "========================================"
echo "automysqlback 本地开发启动"
echo "目录: $SCRIPT_DIR"
echo "========================================"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "错误: 未找到 $PYTHON_BIN，请先安装 Python 3。"
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "检测到首次运行，正在创建虚拟环境..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

NEEDS_INSTALL=0

if [ ! -f "$STAMP_FILE" ]; then
  NEEDS_INSTALL=1
fi

if [ "$REQUIREMENTS_FILE" -nt "$STAMP_FILE" ]; then
  NEEDS_INSTALL=1
fi

if ! python -c "import flask" >/dev/null 2>&1; then
  NEEDS_INSTALL=1
fi

if [ "$NEEDS_INSTALL" -eq 1 ]; then
  echo "正在安装或更新后端依赖..."
  python -m pip install --upgrade pip
  python -m pip install -r "$REQUIREMENTS_FILE"
  touch "$STAMP_FILE"
else
  echo "依赖已就绪，跳过安装。"
fi

echo "正在启动后端服务..."
echo "访问地址: http://127.0.0.1:7001"
echo "按 Ctrl+C 可停止服务"
echo

exec python start.py
