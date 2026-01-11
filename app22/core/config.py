import os
from dotenv import load_dotenv


# загружает переменные окружения из файла *.env
load_dotenv("./app22/local.env")


# logger settings
LOG_DIR = os.environ.get("LOG_DIR")
LOG_FILE = os.environ.get("LOG_FILE")


# logger settings
FILES_DIR = os.environ.get("FILES_DIR")


# root_path --> FastAPI(root_path=OPEN_API_PREFIX)
OPEN_API_PREFIX = os.environ.get("OPEN_API_PREFIX")


# настройки для базы данных
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")

# ------------- postgresql+psycopg2://postgres:password@192.168.1.73:7011/post_db ----------- #
# DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_URL = f"sqlite:///./app22/test_fast_api.db"

# DATABASE_URL_ASYNC = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_URL_ASYNC = f"sqlite+aiosqlite:///.app22/test_fast_api.db"
