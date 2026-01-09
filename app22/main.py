from app22.config_log import ConfigLogger
import uvicorn

from app22.core import get_app_fastapi
from app22.http_request_routers.router_api_request import api_request

# from app22.http_request_routers.router_new_tasks import new_router
from app22.not_async_examples.router_crud_many import not_async_many_crud
from app22.async_many_sql.router_many_async_one import new_many_async_one
from app22.async_many_sql.router_many_async_two import new_many_async_two
from app22.async_many_sql.router_aCrud_one import new_many_aCrud_one
from app22.join_tables.router_join_one import join_one_r
from app22.reader_project.router_reader_one import reader_aCrud_one
from app22.reader_project.router_reader_two import reader_aCrud_two


logFC = ConfigLogger.get_logger("FileStdout", "main22")


app = get_app_fastapi()  # FastAPI()  # app = FastAPI()


# подключаем здесь все роутеры
# app.include_router(new_router)
app.include_router(api_request)
app.include_router(not_async_many_crud)
app.include_router(new_many_async_one)
app.include_router(new_many_async_two)
app.include_router(new_many_aCrud_one)
app.include_router(join_one_r)
app.include_router(reader_aCrud_one)
app.include_router(reader_aCrud_two)


def main():
    """запуск через uvicorn"""
    logFC.info(f"'Start' FastApi 22 = {app}")  # logFC.info(f"'Start' {app}")

    uvicorn.run(app, host="0.0.0.0", port=9000)
    logFC.info(f"'Stop' FastApi 22 = {app}\n'****************************'\n\n")


if __name__ == "__main__":
    main()
