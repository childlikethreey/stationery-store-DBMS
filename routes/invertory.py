import mysql.connector
from flask import Flask, Blueprint, request, jsonify
from db import get_connection
from routes.auth_required import login_required, admin_required
from routes.commonly_used import goods_name_fm
from pydantic import BaseModel, ValidationError, Field
from typing import Optional
'''
col_and_fm = {
    "name": goods_name_fm
}
'''
# required_col = ("name", "sup_id")
# all_col = ("name", "quantity", "price", "sup_id", "stop_purchase")

class inv_type_create(BaseModel):
    name: str = Field(pattern=goods_name_fm)
    price: int = 0
    sup_id: int
    stop_purchase: bool = False

class inv_type_update(BaseModel):
    name: Optional[str] = Field(default=None, pattern=goods_name_fm)
    price: Optional[int] = Field(default=None, ge=0)
    sup_id: Optional[int] = None
    stop_purchase: Optional[bool] = None

def get_one_goods(cursor, goods_id: int) -> tuple | None:
    cursor.execute("select * from `Invertory` where goods_id = %s", (goods_id, ))
    goods = cursor.fetchone()
    if not goods:
        return None, (jsonify({"error": "This goods doesn't exist"}), 404)
    return goods, None


inv_bp = Blueprint("invertory", __name__)

@inv_bp.route("/inv", methods = ["get"])
@login_required
def show_all_goods():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("select * from `Invertory`")
        result = cursor.fetchall()
        return jsonify(result), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()


@inv_bp.route("/inv/<int:goods_id>", methods = ["get"])
@login_required
def show_one_goods(goods_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        goods, error = get_one_goods(cursor, goods_id)
        if error:return error
        return jsonify(goods), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()


@inv_bp.route("/inv", methods = ["post"])
@admin_required
def create_goods():
    try:
        chk = inv_type_create(**request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400
    data = chk.model_dump()
    val = {key: data.get(key) for key in data}

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # firm sup_id exist
        cursor.execute("select * from `Supplier` where sup_id = %s", (val["sup_id"], ))
        sup = cursor.fetchone()
        if not sup:
            return jsonify({"error": "This supplier doesn't exist"}), 404
        
        columns = []
        values = []
        for a, b in val.items():
            if b is None:
                continue
            columns.append(a)
            values.append(b)
        s_num = ", ".join(["%s"] * len(values))
        cursor.execute(f"insert into `Invertory` ({', '.join(columns)}) values ({s_num})", tuple(values))        
        conn.commit()
        return jsonify({"message": "create successed"}), 201
        
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close() 


@inv_bp.route("/inv/<int:goods_id>", methods = ["put"])
@admin_required
def update_goods(goods_id):
    try:
        chk = inv_type_update(**request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400
    data = chk.model_dump()
    val = {key: data.get(key) for key in data}

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # firm goods_id, sup_id exist
        _, error = get_one_goods(cursor, goods_id)
        if error:return error
        if val["sup_id"]:
            cursor.execute("select * from `Supplier` where sup_id = %s", (val["sup_id"], ))
            sup = cursor.fetchone()
            if not sup:
                return jsonify({"error": "This supplier doesn't exist"}), 404
        
        columns = []
        values = []
        for a, b in val.items():
            if b is None:
                continue
            columns.append(f"{a} = %s")
            values.append(b)
        values.append(goods_id)
        
        cursor.execute(f"update `Invertory` set {", ".join(columns)} where goods_id = %s", tuple(values))        
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"message": "Not any update", "goods_id": goods_id}), 400
        return jsonify({"message": "update successed"}), 200
        
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close() 