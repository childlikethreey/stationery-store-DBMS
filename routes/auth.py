from flask import Blueprint, request, jsonify, session
from db import connect_manger
from routes.auth_required import login_required
import bcrypt
from pydantic import BaseModel, Field
from routes.helpers import staff_no_fm, NotFoundError


class login_info(BaseModel):
    staff_no: str = Field(pattern=staff_no_fm)
    pw: str

class update_pw(BaseModel):
    old_pw: str
    new_pw: str = Field(min_length=7)


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods = ["post"])
def staff_login():
    data_chk = login_info(**request.get_json())
    data = data_chk.model_dump()
    with connect_manger() as cursor:
        cursor.execute(
            """
            select staff_id, is_active, pw_hash, role
            from `Staff` join `login_info` using (staff_id)
            where staff_no = %s
            """, (data["staff_no"], ))
        user = cursor.fetchone()

        if not user:
            raise NotFoundError("ID doesn't exist")
        if not bcrypt.checkpw(data["pw"].encode("utf-8"), user["pw_hash"].encode("utf-8")):
            raise ValueError("wrong staff no or password")
        if not user["is_active"]:
            raise ValueError("Employee already quit")

        session["staff_id"] = user["staff_id"]
        session["role"] = user["role"]

        return jsonify({"message": "login successed", "staff_no": data["staff_no"], "role": user["role"]}), 200
        

@auth_bp.route("/logout", methods = ["post"])
@login_required
def staff_logout():
    session.clear()
    return jsonify({"message": "logout"}), 200


@auth_bp.route("/account", methods = ["patch"])
@login_required
def change_pw():
    data_chk = update_pw(**request.get_json())
    data = data_chk.model_dump()
    
    with connect_manger() as cursor:
        cursor.execute("select * from `login_info` where staff_id = %s", (session["staff_id"], ))
        user = cursor.fetchone()

        if not bcrypt.checkpw(data["old_pw"].encode("utf-8"), user["pw_hash"].encode("utf-8")):
            raise ValueError("wrong staff no or password")
        if data["old_pw"] == data["new_pw"]:
            raise ValueError("new password cannnot same as old password")
            
        temp = bcrypt.hashpw(data["new_pw"].encode("utf-8"), bcrypt.gensalt())
        cursor.execute("update `login_info` set pw_hash = %s where staff_id = %s", (temp, session["staff_id"]))
        return jsonify({"message": "change password successed"}), 200
    