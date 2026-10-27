import os
import subprocess
from pathlib import Path
from app.core.config import get_settings

s = get_settings()

env = os.environ.copy()
env["MYSQL_PWD"] = s.db_password

output = Path("/tmp/workforce_backup.sql")

result = subprocess.run(
    [
        "mysqldump",
        "-h", s.db_host,
        "-P", str(s.db_port),
        "-u", s.db_user,
        "--single-transaction",
        "--no-tablespaces",
        s.db_name,
    ],
    env=env,
    stdout=output.open("wb"),
    stderr=subprocess.PIPE,
    text=True,
)

if result.returncode != 0:
    output.unlink(missing_ok=True)
    print("Backup failed:")
    print(result.stderr)
    raise SystemExit(result.returncode)

print(f"Backup created: {output}")
print(f"Backup size: {output.stat().st_size} bytes")
