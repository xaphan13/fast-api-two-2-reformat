from base_dir_path import DIR_CWD, BASE_DIR
from config_log import logFC
# from app11.config_log import ConfigLogger
# logFC = ConfigLogger.getLogger("FileStdout", "main")

from app11.core import get_app_fastapi
import uvicorn

from app11.run_task.router_task import tasks_route
from app11.example_simple.router_ex_simple import ex_simple_route
from app11.example_db.router_ex_user import ex_user_route
from app11.example_db.router_ex_post import ex_post_route
from app11.example_many_db.router_many import ex_many_route
from app11.example_many_db.router_assoc import ex_assoc_route
from app11.run_task.temp_router_task import temp_route


app = get_app_fastapi()  # FastAPI()  # app = FastAPI()


# подключаем здесь все роутеры
app.include_router(temp_route)
app.include_router(tasks_route)
app.include_router(ex_simple_route)
app.include_router(ex_user_route)
app.include_router(ex_post_route)
app.include_router(ex_many_route)
app.include_router(ex_assoc_route)


def main():
    logFC.info(f"Base dir path :\n{DIR_CWD=} \n{BASE_DIR=}")

    """запуск через uvicorn"""
    logFC.info(f"'Start' FastApi = {app}")

    uvicorn.run(app, host="0.0.0.0", port=8000)

    logFC.warning(
        "end '-------------------FastApi 11 - main()' '---------------------------' \n\n\n\n"
        "'********************************************************************************'"
    )


if __name__ == "__main__":
    main()
