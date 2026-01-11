from fastapi import APIRouter, Depends
from typing import Type

from sqlalchemy import Column
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app11.example_many_db.except_many_db import MyApiRouterMany
from app11.config_log import ConfigLogger
from app11.db_core.db_conf import SessionDB

from app11.example_many_db.model_many_db import Order, Product, OrderProductAssociation
from app11.example_many_db.crud_many import order_db, product_db

from app11.example_many_db.schema_many_db import (
    OrderResp,
    ProductResp,
    OrderRespWithProducts,
    OrderRespWithProductsDetails,
)

logFC = ConfigLogger.get_logger("FileStdout")


ex_assoc_route = APIRouter(route_class=MyApiRouterMany, prefix="/ex_assoc", tags=["ex_assoc"])


# requesting list all Orders and Products from the database *****************************
@ex_assoc_route.get("/get_big_all", response_model=dict[str, list[OrderResp] | list[ProductResp]])
def get_big_all(db: Session = Depends(SessionDB.get_db)):
    order_by_list_o: list[Column[Order]] = [Order.id, Order.promocode]
    orders: list[Type[Order]] = order_db.get_record_all(db, order_by_list_o)
    order_by_list_p: list[Column[Product]] = [Product.name, Product.price]
    products: list[Type[Product]] = product_db.get_record_all(db, order_by_list_p)
    return {"ord": orders, "prod": products}


# deleting Order and Products from the database *****************************************
@ex_assoc_route.delete("/delete_big_all", response_model=dict[str, dict[str, int]])
def delete_big_all(db: Session = Depends(SessionDB.get_db)):
    orders: dict[str, int] = order_db.delete_all_for(db, True)
    products: dict[str, int] = product_db.delete_all_for(db, True)
    return {"ord": orders, "prod": products}


# adding Orders and Products to the database ********************************************
@ex_assoc_route.post("/add_big", response_model=dict[str, str])
def add_big(db: Session = Depends(SessionDB.get_db)) -> dict[str, str]:
    order_db.delete_all_for(db)
    product_db.delete_all_for(db)

    list_ord = [{"promocode": "first"}, {"promocode": "second"}, {"promocode": "third"}]

    list_prod = [
        {"name": "111", "description": "111aaa", "price": 100},
        {"name": "222", "description": "222bbb", "price": 200},
        {"name": "333", "description": "333ccc", "price": 300},
        {"name": "444", "description": "444ddd", "price": 400},
        {"name": "555", "description": "555eee", "price": 500},
        {"name": "666", "description": "666fff", "price": 600},
        {"name": "777", "description": "777ggg", "price": 700},
        {"name": "888", "description": "888hhh", "price": 800},
    ]

    logFC.info(f"add_big : list_ord = {list_ord}")

    [product_db.add_dict_record(product, db, True) for product in list_prod]

    [order_db.add_dict_record(order, db, True) for order in list_ord]

    return {"insert": "all", "ord": f"{len(list_ord)}", "prod": f"{len(list_prod)}"}


# append Products to Orders *************************************************************
@ex_assoc_route.get("/products_append", response_model=dict[str, str] | None | list[OrderRespWithProducts])
def products_append(db: Session = Depends(SessionDB.get_db)):
    prod_list: list[Type[Product]] = product_db.get_record_all(db)
    prod_dict = {product.name: product for product in prod_list}
    try:
        order1: Order = order_db.get_record_dict_none({"promocode": "first"}, db)
        if order1 is not None:
            order1.products.append(prod_dict.get("111"))
            order1.products.append(prod_dict.get("222"))

        order2: Order = order_db.get_record_dict_none({"promocode": "second"}, db)
        if order2 is not None:
            order2.products = [prod_dict.get("333"), prod_dict.get("444")]

        order3: Order = order_db.get_record_dict_none({"promocode": "third"}, db)
        if order3 is not None:
            order3.products.extend([prod_dict.get("555"), prod_dict.get("666")])
            order3.products.extend([prod_dict.get("777"), prod_dict.get("888")])

        db.commit()
        db.refresh(order1)
        db.refresh(order2)
        db.refresh(order3)
    except IntegrityError as _exc:
        return {"ERROR": "IntegrityError", "DB": "not commit"}
    return [order1, order2, order3]


# append OrderProductAssociation to Order ***********************************************
@ex_assoc_route.get("/assoc_append", response_model=dict[str, str] | None | list[OrderRespWithProductsDetails])
def assoc_append(db: Session = Depends(SessionDB.get_db)):
    prod_list: list[Type[Product]] = product_db.get_record_all(db)
    prod_dict = {product.name: product for product in prod_list}
    try:
        order1: Order = order_db.get_record_dict_none({"promocode": "first"}, db)
        if order1 is not None:
            or_pr1 = OrderProductAssociation(count=1, unit_price=1000, product=prod_dict.get("111"))
            order1.products_details.append(or_pr1)
            or_pr2 = OrderProductAssociation(count=2, unit_price=2000, product=prod_dict.get("222"))
            order1.products_details.append(or_pr2)

        order2: Order = order_db.get_record_dict_none({"promocode": "second"}, db)
        if order2 is not None:
            or_pr3 = OrderProductAssociation(count=3, unit_price=3000, product=prod_dict.get("333"))
            or_pr4 = OrderProductAssociation(count=4, unit_price=4000, product=prod_dict.get("444"))
            order2.products_details = [or_pr3, or_pr4]

        order3: Order = order_db.get_record_dict_none({"promocode": "third"}, db)
        if order3 is not None:
            or_pr5 = OrderProductAssociation(count=5, unit_price=5000, product=prod_dict.get("555"))
            or_pr6 = OrderProductAssociation(count=6, unit_price=6000, product=prod_dict.get("666"))
            or_pr7 = OrderProductAssociation(count=7, unit_price=7000, product=prod_dict.get("777"))
            or_pr8 = OrderProductAssociation(count=8, unit_price=8000, product=prod_dict.get("888"))
            order3.products_details.extend([or_pr5, or_pr6])
            order3.products_details.extend([or_pr7, or_pr8])

        db.commit()
        db.refresh(order1)
        db.refresh(order2)
        db.refresh(order3)
    except IntegrityError as _exc:
        return {"ERROR": "IntegrityError", "DB": "not commit"}
    return [order1, order2, order3]


# remove Products from Orders ***********************************************************
@ex_assoc_route.put("/remove", response_model=dict[str, str] | list[OrderResp | None])
def remove(db: Session = Depends(SessionDB.get_db)):
    prod_list: list[Type[Product]] = product_db.get_record_all(db)
    prod_dict = {product.name: product for product in prod_list}
    try:
        order1: Order = order_db.get_record_dict_none({"promocode": "first"}, db)
        if order1 is not None:
            order1.products.remove(prod_dict.get("111"))
            order1.products.remove(prod_dict.get("222"))

        order2: Order = order_db.get_record_dict_none({"promocode": "second"}, db)
        if order2 is not None:
            order2.products.remove(prod_dict.get("333"))
            order2.products.remove(prod_dict.get("444"))

        order3: Order = order_db.get_record_dict_none({"promocode": "third"}, db)
        if order3 is not None:
            order3.products.remove(prod_dict.get("555"))
            order3.products.remove(prod_dict.get("666"))
            order3.products.remove(prod_dict.get("777"))
            order3.products.remove(prod_dict.get("888"))

        db.commit()
        db.refresh(order1)
        db.refresh(order2)
        db.refresh(order3)
    except ValueError as _exc:
        return {"ERROR": "ValueError", "DB": "not commit"}
    return [order1, order2, order3]
