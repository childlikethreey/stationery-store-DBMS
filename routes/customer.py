from flask import Blueprint, request, jsonify, session
from db import connect_manger
from routes.auth_required import login_required
from pydantic import BaseModel, Field
from typing import Optional
from routes.helpers import (
    get_one, get_all, empty_str_to_none,
    coname_fm, name_fm, phone_fm, staff_no_fm, AuthError)

table = "`Customer`"
select_col = ("cust_id", "cust_no", "co_name", "contact_name", "C.phone", "staff_no")
select_table = "`Customer` C join `Staff` using (staff_id)"

class type_create(BaseModel):
    co_name: str = Field(pattern=coname_fm)
    contact_name: Optional[str] = Field(default=None, pattern=name_fm)
    phone: str = Field(pattern=phone_fm)
    staff_no: str = Field(pattern=staff_no_fm)
    _ = empty_str_to_none("contact_name")

class type_update(BaseModel):
    co_name: Optional[str] = Field(default=None, pattern=coname_fm)
    contact_name: Optional[str] = Field(default=None, pattern=name_fm)
    phone: Optional[str] = Field(default=None, pattern=phone_fm)
    staff_no: Optional[str] = Field(default=None, pattern=staff_no_fm)
    _ = empty_str_to_none("contact_name")


cust_bp = Blueprint("customer", __name__)


@cust_bp.route("/cust", methods = ["get"])
@login_required
def show_all_customer():
    with connect_manger() as cursor:
        # check role limit
        result = get_all(cursor, select_table, select_col, True)
        return result


@cust_bp.route("/cust/<int:cust_id>", methods = ["get"])
@login_required
def show_one_customer(cust_id):
    with connect_manger() as cursor:
        # check role limit
        result = get_one(cursor, select_table, select_col, "cust_id", cust_id, True)
        return result


@cust_bp.route("/cust", methods = ["post"])
@login_required
def create_customer():
    data_chk = type_update(**request.get_json())
    data = data_chk.model_dump(exclude_unset=True)

    with connect_manger() as cursor:
        # check staff_id exist, staff_id active
        user = get_one(cursor, "`Staff`", ("*", ), "staff_no", data["staff_no"], False)
        if not user["is_active"]:
            raise ValueError("Employee already quit")

        del data["staff_no"]
        data["staff_id"] = user["staff_id"]
        cols = ", ".join(data.keys())
        s_num = ", ".join(["%s"] * len(data.values()))
        cursor.execute(f"insert into {table} ({cols}) values ({s_num})", tuple(data.values()))
            
        num = cursor.lastrowid
        cust_no = f"K{num:06d}"
        cursor.execute(f"update {table} set cust_no = %s where cust_id = %s", (cust_no, num))
        return jsonify({"message": "create successed", "cust_no": cust_no}), 201


@cust_bp.route("/cust/<int:cust_id>", methods = ["put"])
@login_required
def update_customer(cust_id):
    data_chk = type_update(**request.get_json())
    data = data_chk.model_dump(exclude_unset=True)

    with connect_manger() as cursor:
        # check cust_id exist, role limit
        _ = get_one(cursor, select_table, select_col, "cust_id", cust_id, True)

        # check staff_id exist, staff_id active
        if "staff_no" in data:
            user = get_one(cursor, "`Staff`", ("*", ), "staff_no", data["staff_no"], False)
            if not user["is_active"]:
                raise ValueError("Employee already quit")
            # staff cannot update staff_id
            if session["role"] == "staff":
                    raise AuthError("You cannot change the staff_no")
            else:
                del data["staff_no"]
                data["staff_id"] = user["staff_id"]

        cols = ", ".join([f"{key} = %s" for key in data.keys()])
        cursor.execute(f"update {table} set {cols} where cust_id = %s", 
                        tuple(data.values()) + (cust_id, ))
        if cursor.rowcount == 0:
            return jsonify({"message": "Not any update", "cust_id": cust_id}), 200
        return jsonify({"message": "update successed", "cust_id": cust_id}), 200
