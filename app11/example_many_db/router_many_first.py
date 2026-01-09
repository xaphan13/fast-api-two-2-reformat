from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Type

from app11.db_core.db_conf import SessionDB
from sqlalchemy.orm import Session

from app11.example_many_db.except_many_db import MyApiRouterMany
from app11.example_many_db.schema_many_db import OrderResp, OrderGetQuery, OrderUpdateBody, OrderCreateBody

from app11.example_many_db.model_many_db import Order


ex_many_route_f = APIRouter(route_class=MyApiRouterMany, prefix="/ex_many", tags=["ex_many"])


# Dep-ends Order  ***********************************************************************
def get_order(query: OrderGetQuery = Depends(), db: Session = Depends(SessionDB.get_db)):
    query_dict = {key: value for key, value in query.dict().items() if value is not None}
    order: Optional[Order] = db.query(Order).filter_by(**query_dict).first()
    if order:
        return order
    raise HTTPException(status_code=422, detail=f"Order with {query_dict} not found")


# adding Order to the database **********************************************************
@ex_many_route_f.post("/add_order", response_model=OrderResp, status_code=200)
def add_order(body: OrderCreateBody, db: Session = Depends(SessionDB.get_db)):
    new_order: Order = Order(**body.dict())
    db.add(new_order)
    db.commit()
    return new_order


# updating Order from the database *****************************************************
@ex_many_route_f.put("/update_order", response_model=OrderResp)
def update_order(body: OrderUpdateBody, db: Session = Depends(SessionDB.get_db), order: Order = Depends(get_order)):
    update = body.dict(exclude_none=True).items()
    [setattr(order, name, value) for name, value in update if value != ""]
    db.commit()
    return order


# requesting Order from the database *****************************************************
@ex_many_route_f.get("/get_order", response_model=OrderResp, status_code=200)
def get_order(order: Order = Depends(get_order)):
    return order


# requesting list of users from the database ********************************************
@ex_many_route_f.get("/get_order_all", response_model=list[OrderResp], status_code=200)
def get_users_list_query(db: Session = Depends(SessionDB.get_db)):
    orders: list[Type[Order]] = db.query(Order).order_by(Order.id).all()
    return orders


# deleting Order from the database *****************************************************
@ex_many_route_f.delete("/delete_order", response_model=OrderResp)
def delete_order(order: Order = Depends(get_order), db: Session = Depends(SessionDB.get_db)):
    db.delete(order)
    db.commit()
    return order


# ***************************************************************************************
# Product requesting to dataBase ================================================
# ---------------------------------------------------------------------------------------
