import os
import tempfile
import unittest
from pathlib import Path

from spiderx.db.mysql_config import get_mysql_config, load_env_values


class MysqlConfigTest(unittest.TestCase):
    def test_loads_mysql_config_from_env_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "DB_HOST=127.0.0.1",
                        "DB_PORT=3307",
                        "DB_USER=test_user",
                        "DB_PASSWORD=test_password",
                        "DB_NAME=test_database",
                    ]
                ),
                encoding="utf-8",
            )

            config = get_mysql_config(env_path)

        self.assertEqual(
            config,
            {
                "host": "127.0.0.1",
                "port": 3307,
                "user": "test_user",
                "password": "test_password",
                "database": "test_database",
                "charset": "utf8mb4",
            },
        )

    def test_environment_variables_override_env_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "DB_HOST=from_file",
                        "DB_PORT=3306",
                        "DB_USER=file_user",
                        "DB_PASSWORD=file_password",
                        "DB_NAME=file_database",
                    ]
                ),
                encoding="utf-8",
            )

            previous = os.environ.get("DB_HOST")
            os.environ["DB_HOST"] = "from_environment"
            try:
                values = load_env_values(env_path)
            finally:
                if previous is None:
                    os.environ.pop("DB_HOST", None)
                else:
                    os.environ["DB_HOST"] = previous

        self.assertEqual(values["DB_HOST"], "from_environment")


if __name__ == "__main__":
    unittest.main()
