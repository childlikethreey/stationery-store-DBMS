from flask import Blueprint, request, jsonify
from routes.auth_required import login_required, admin_required
from db import connect_manger
from pydantic import BaseModel, Field, ValidationError
from typing import Optional
from routes.helpers import (
    get_one, get_all, empty_str_to_none,
    coname_fm, name_fm, phone_fm)

table = "`Supplier`"
select_col = ("*", )

class type_create(BaseModel):
    co_name: str = Field(pattern=coname_fm)
    contact_name: Optional[str] = Field(default=None, pattern=name_fm)
    phone: str = Field(pattern=phone_fm)
    _ = empty_str_to_none("contact_name")

class type_update(BaseModel):
    co_name: Optional[str] = Field(default=None, pattern=coname_fm)
    contact_name: Optional[str] = Field(default=None, pattern=name_fm)
    phone: Optional[str] = Field(default=None, pattern=phone_fm)
    _ = empty_str_to_none("contact_name")


sup_bp = Blueprint("supplier", __name__)


@sup_bp.route("/sup", methods = ["get"])
@login_required
def show_all_supplier():
    with connect_manger() as cursor:
        result = get_all(cursor, table, select_col)
        return result


@sup_bp.route("/sup/<int:sup_id>", methods = ["get"])
@login_required
def show_one_supplier(sup_id):
    with connect_manger() as cursor:
        result = get_one(cursor, table, select_col, "sup_id", sup_id)
        return result


@sup_bp.route("/sup", methods = ["post"])
@login_required
def create_new_supplier():
    data_chk = type_create(**request.get_json())
    data = data_chk.model_dump(exclude_unset=True)

    with connect_manger() as cursor:
        cols = ", ".join(data.keys())
        s_num = ", ".join(["%s"] * len(data.values()))
        cursor.execute(f"insert into {table} ({cols}) values ({s_num})", tuple(data.values()))
        num = cursor.lastrowid
        return jsonify({"message": "create successed", "sup_id": num}), 201


@sup_bp.route("/sup/<int:sup_id>", methods = ["put"])
@admin_required
def update_supplier(sup_id):
    data_chk = type_update(**request.get_json())
    data = data_chk.model_dump(exclude_unset=True)

    with connect_manger() as cursor:
        # check sup_id exist
        _ = get_one(cursor, table, select_col, "sup_id", sup_id)

        cols = ", ".join([f"{key} = %s" for key in data.keys()])
        cursor.execute(f"update {table} set {cols} where sup_id = %s", 
                       tuple(data.values()) + (sup_id, ))
        if cursor.rowcount == 0:
            return jsonify({"message": "Not any update", "sup_id": sup_id}), 200
        return jsonify({"message": "update successed", "sup_id": sup_id}), 200