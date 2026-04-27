"""Shared MySQL configuration loader for spiderx services."""

import os
from pathlib import Path
from typing import Dict, Mapping, Optional, Union


ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
REQUIRED_KEYS = ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME")


def _parse_env_file(env_path: Union[str, Path]) -> Dict[str, str]:
    path = Path(env_path)
    if not path.exists():
        raise FileNotFoundError(f"未找到环境变量文件: {path}")

    values: Dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        values[key] = value

    return values


def load_env_values(env_path: Optional[Union[str, Path]] = None) -> Dict[str, str]:
    """Load values from the repo-level .env file, with process env overrides."""
    values = _parse_env_file(env_path or ENV_PATH)
    for key, value in os.environ.items():
        if key.startswith("DB_"):
            values[key] = value
    return values


def get_mysql_config(
    env_path: Optional[Union[str, Path]] = None,
    *,
    charset: str = "utf8mb4",
) -> Dict[str, Union[str, int]]:
    """Return a pymysql-compatible config dict from .env."""
    values: Mapping[str, str] = load_env_values(env_path)
    missing_keys = [key for key in REQUIRED_KEYS if not values.get(key)]
    if missing_keys:
        raise RuntimeError(
            f"缺少数据库环境变量: {', '.join(missing_keys)}，请检查 {env_path or ENV_PATH}"
        )

    try:
        port = int(values["DB_PORT"])
    except ValueError as exc:
        raise ValueError(f"DB_PORT 必须是整数: {values['DB_PORT']}") from exc

    return {
        "host": values["DB_HOST"],
        "port": port,
        "user": values["DB_USER"],
        "password": values["DB_PASSWORD"],
        "database": values["DB_NAME"],
        "charset": charset,
    }
