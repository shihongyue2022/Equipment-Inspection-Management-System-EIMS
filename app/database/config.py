import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / '.env')


def _is_enabled(value):
    return str(value).lower() in ('1', 'true', 'yes', 'on')

# Docker の MySQL に合わせる
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', '3307')),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'rootpass'),
    'database': os.environ.get('DB_NAME', 'inspection_db'),
    'charset': 'utf8mb4',
    'ssl': _is_enabled(os.environ.get('DB_SSL', 'false')),
}
