from flask import Blueprint, request, jsonify
from db import connect_manger
from routes.auth_required import admin_required
import bcrypt
from pydantic import BaseModel, Field
from typing import Optional, Literal
from routes.helpers import (
    get_one, get_all, empty_str_to_none,
    name_fm, phone_fm, NotFoundError)

table = "`Staff`"
select_col = ("staff_id", "staff_no", "name", "phone", "dept", "is_active")

dept_options = Literal["CS", "管理層", "清潔部門"] 
role_options = Literal["admin", "staff"]

class type_create(BaseModel):
    name: str = Field(pattern=name_fm)
    phone: Optional[str] = Field(default=None, pattern=phone_fm)
    dept: dept_options
    is_active: bool = Field(default=True)
    _ = empty_str_to_none("phone")
    
class type_update(BaseModel):
    name: Optional[str] = Field(default=None, pattern=name_fm)
    phone: Optional[str] = Field(default=None, pattern=phone_fm)
    dept: Optional[dept_options] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)
    _ = empty_str_to_none("phone")
    
class type_create_account(BaseModel):
    role: role_options


staff_bp = Blueprint("staff", __name__)


@staff_bp.route("/staff", methods = ["get"])
@admin_required
def show_all_staff():
    with connect_manger() as cursor:
        result = get_all(cursor, table, select_col)
        return result


@staff_bp.route("/staff/<int:staff_id>", methods = ["get"])
@admin_required
def show_one_staff(staff_id):
    with connect_manger() as cursor:
        result = get_one(cursor, table, select_col, "staff_id", staff_id)
        return result


@staff_bp.route("/staff", methods = ["post"])
@admin_required
def create_staff():
    data_chk = type_create(**request.get_json())
    data = data_chk.model_dump(exclude_unset=True)
    with connect_manger() as cursor:
        cols = ', '.join(data.keys())
        s_num = ", ".join(["%s"] * len(data.values()))
        cursor.execute(f"insert into {table} ({cols}) values ({s_num})",
                        tuple(data.values()))
        num = cursor.lastrowid
        staff_no = f'CS-{num:06d}'
        cursor.execute(f"update {table} set staff_no = %s where staff_id = %s", (staff_no, num))

        return jsonify({"message": "create successed", "staff_no": staff_no}), 201
    
 
@staff_bp.route("/staff/<int:staff_id>", methods = ["put"])
@admin_required
def update_staff(staff_id):
    data_chk = type_update(**request.get_json())
    data = data_chk.model_dump(exclude_unset=True)
    with connect_manger() as cursor:
        # check staff_id exists
        _ = get_one(cursor, table, select_col, "staff_id", staff_id)

        cols = ', '.join([f"{key} = %s" for key in data.keys()])
        cursor.execute(f"update {table} set {cols} where staff_id = %s", tuple(data.values()) + (staff_id, ))
        if cursor.rowcount == 0:
            return jsonify({"message": "Not any update", "staff_id": staff_id}), 200
        return jsonify({"message": "update successed", "staff_id": staff_id}), 200


@staff_bp.route("/staff/<int:staff_id>/account", methods = ["post"])
@admin_required
def create_new_acc(staff_id):
    '''
    Transaction checklist：
    1. Staff ID exist
    2. Staff is active
    3. 不可以是清潔部門
    '''
    data_chk = type_create_account(**request.get_json())
    data = data_chk.model_dump()
    with connect_manger() as cursor:
        # check staff not account
        cursor.execute("select staff_id from `login_info` where staff_id = %s", (staff_id, ))
        existing = cursor.fetchone()
        if existing:
            raise NotFoundError("Account already exists")

        # check staff dept, staff is active
        cursor.execute("select * from `Staff` where staff_id = %s", (staff_id, ))
        user = cursor.fetchone()
        if user["dept"] == "清潔部門":
            raise ValueError("清潔人員不能建立帳號")
        if not user["is_active"]:
            raise ValueError("Employee already quit")
            
        pw = "test123"
        pw_hash = bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())
        cursor.execute("""
                        insert into `login_info` (staff_id, pw_hash, role) 
                        values (%s, %s, %s)
                        """, (staff_id, pw_hash, data["role"]))
        return jsonify({"message": "create successed\n Please remind staff change the password",
                        "staff_no": user["staff_no"], "password": "test123"}), 200
