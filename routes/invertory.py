from flask import Blueprint, request, jsonify
from db import connect_manger
from routes.auth_required import login_required, admin_required
from pydantic import BaseModel, Field
from typing import Optional
from routes.helpers import (
    get_one, get_all, empty_str_to_none,
    goods_name_fm)

table = "`Invertory`"
select_col = ("*", )

class type_create(BaseModel):
    name: str = Field(pattern=goods_name_fm)
    price: int = Field(default=0, ge=0)
    sup_id: int = Field(ge=0)
    stop_purchase: bool = Field(default=False)
  
class type_update(BaseModel):
    name: Optional[str] = Field(default=None, pattern=goods_name_fm)
    price: Optional[int] = Field(default=None, ge=0)
    sup_id: Optional[int] = Field(default=None, ge=0)
    stop_purchase: Optional[bool] = Field(default=None)


inv_bp = Blueprint("invertory", __name__)


@inv_bp.route("/inv", methods = ["get"])
@login_required
def show_all_goods():
    with connect_manger() as cursor:
        result = get_all(cursor, table, select_col)
        return result


@inv_bp.route("/inv/<int:goods_id>", methods = ["get"])
@login_required
def show_one_goods(goods_id):
    with connect_manger() as cursor:
        result = get_one(cursor, table, select_col, "goods_id", goods_id)
        return result


@inv_bp.route("/inv", methods = ["post"])
@admin_required
def create_goods():
    data_chk = type_create(**request.get_json())
    data = data_chk.model_dump(exclude_unset=True)

    with connect_manger() as cursor:
        # firm sup_id exist
        _ = get_one(cursor, "`Supplier`", ("*", ), "sup_id", data["sup_id"])

        cols = ", ".join(data.keys())
        s_num = ", ".join(["%s"] * len(data.values()))
        cursor.execute(f"insert into {table} ({cols}) values ({s_num})", tuple(data.values()))
        num = cursor.lastrowid
        return jsonify({"message": "create successed", "goods_id": num}), 201


@inv_bp.route("/inv/<int:goods_id>", methods = ["put"])
@admin_required
def update_goods(goods_id):
    data_chk = type_update(**request.get_json())
    data = data_chk.model_dump(exclude_unset=True)

    with connect_manger() as cursor:
        # firm goods_id exist, sup_id exist
        _ = get_one(cursor, table, select_col, "goods_id", goods_id)
        if "sup_id" in data:
            _ = get_one(cursor, "`Supplier`", ("*", ), "sup_id", data["sup_id"])
            
        cols = ", ".join([f"{key} = %s" for key in data.keys()])
        cursor.execute(f"update {table} set {cols} where goods_id = %s", 
                       tuple(data.values()) + (goods_id, ))
        if cursor.rowcount == 0:
            return jsonify({"message": "Not any update", "goods_id": goods_id}), 200
        return jsonify({"message": "update successed", "goods_id": goods_id}), 200
