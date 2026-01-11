from fastapi import APIRouter, Query, Path, Depends
from typing_extensions import Annotated

from app11.config_log import ConfigLogger
from app11.example_simple.schema_ex_simple import SimpleRespSchema, SimpleReqSchema, ModelName


logFC = ConfigLogger.get_logger("FileStdout")


ex_simple_route = APIRouter(prefix="/ex_simple", tags=["Example simple"])


@ex_simple_route.get("/simpleGet1", response_model=SimpleRespSchema, status_code=201)
def simpleGet1(amount: int = 1, x: int = 2, y: int = 3):
    result = amount + x + y
    logFC.info(f"simpleGet1 : {amount} + {x} + {y} = {result}")
    return SimpleRespSchema(x=1, y=2, result=result)


@ex_simple_route.post("/simplePost1", response_model=SimpleRespSchema, status_code=202)
def simplePost1(body: SimpleReqSchema, url_query: int = 2):
    result = 1 + url_query
    logFC.info(f"simplePost1 : [{body}] : 1 + {url_query} = {result}")
    return SimpleRespSchema(**body.dict(exclude={"amount"}), result=result)


@ex_simple_route.put("/simplePost2/{url_path}", response_model=SimpleRespSchema, status_code=202)
def simplePost2(body: SimpleReqSchema, url_path: ModelName, url_query: int = 4):
    result = 1 + url_query + url_path
    logFC.info(f"simplePost2 : [{body}] : 1 + {url_query} + [{url_path.value}] = {result}")
    logFC.info(f"url_path Enum : [{url_path}] : {url_path.x.value} : {url_path.y.value} : {url_path.value}")
    return SimpleRespSchema(**body.dict(exclude={"amount"}), result=result)


def get_url_path(url_path: Annotated[int, Path(title="path parameter", ge=1, le=9)]) -> int:
    return url_path


@ex_simple_route.patch("/simplePost3/{url_path}", response_model=SimpleRespSchema, status_code=202)
def simplePost3(body: SimpleReqSchema, depends_value: int = Depends(get_url_path)):
    result = 1 + depends_value
    logFC.info(f"simplePost3 : [{body}] : 1 + {depends_value} = {result}")
    return SimpleRespSchema(**body.dict(exclude={"amount"}), result=result)


@ex_simple_route.delete("/simplePost4", response_model=SimpleRespSchema, status_code=202)
def simplePost4(body: SimpleReqSchema, url_query: int = Query(2, ge=1, le=9)):
    result = 1 + url_query
    logFC.info(f"simplePost4 : [{body}] : 1 + {url_query} = {result}")
    return SimpleRespSchema(**body.dict(exclude={"amount"}), result=result)
