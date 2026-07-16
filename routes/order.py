from datetime import date as date_type
import mysql.connector
from flask import Flask, Blueprint, request, jsonify
from db import get_connection, connect_manger
from routes.auth_required import login_required, admin_required
from routes.commonly_used import get_Seq_no, get_all, get_one
from pydantic import BaseModel, ValidationError, Field
from typing import Optional, Literal

table = "Order"
select_col1 = ("order_no", "date", "amount", "status", "order_id")
select_col2 = ("order_no", "date", "reason", "discount", "amount", "status", "staff_id", "cust_id")

STATUS_OPTIONS = Literal["processing", "shipped", "completed", "cancelled"]

class type_create(BaseModel):
    date: date_type = Field(default_factory=date_type.today)
    reason: Optional[str] = None
    discount: Optional[int] = Field(default=None, ge=0)
    staff_id: int = Field(gt=0)
    cust_id: int = Field(gt=0)

class type_update(BaseModel):
    date: Optional[date_type] = Field(default=None)
    reason: Optional[str] = None
    discount: Optional[int] = Field(default=None, ge=0)
    status: Optional[STATUS_OPTIONS] = Field(default=None)
    staff_id: Optional[int] = Field(default=None, gt=0)
    cust_id: Optional[int] = Field(default=None, gt=0)

def chk_staff_id(cursor, staff_id: int) -> tuple | None:
    cursor.execute("select * from `Staff` where staff_id = %s", (staff_id, ))
    result = cursor.fetchone()
    if not result:
        return (jsonify({"error": "This employee ID doesn't exist"}), 404)
    if not result["is_active"]:
        return (jsonify({"error": "This employee already quit"}), 400)
    return None

def chk_cust_id(cursor, cust_id: int) -> tuple | None:
    cursor.execute("select * from `Customer` where cust_id = %s", (cust_id, ))
    result = cursor.fetchone()
    if not result:
        return (jsonify({"error": "This customer ID doesn't exist"}), 404)
    return None


order_bp = Blueprint("order", __name__)


# 可以顯示訂單的基本資料
@order_bp.route("/order", methods = ["get"])
@login_required
def show_all_order():
    with connect_manger() as cursor:
        try:
            result = get_all(cursor, table, select_col1, True)
            return result
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500


# 可以顯示訂單的基本資料（ONE）
@order_bp.route("/order/<int:order_id>", methods = ["get"])
@login_required
def show_one_order(order_id):
    with connect_manger() as cursor:
        try:
            order, error = get_one(cursor, table, select_col1, "order_id", order_id, True)
            if error:
                return error
            else:
                return jsonify(order), 200
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500


@order_bp.route("/order", methods = ["post"])
@login_required
def create_order():
    try:
        order_chk = type_create(**request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400
    order_data = order_chk.model_dump()

    with connect_manger() as cursor:
        try:
            # firm staff_id exist & working
            error1 = chk_staff_id(cursor, order_data["staff_id"])
            if error1: return error1

            # firm cust_id exist
            error2 = chk_cust_id(cursor, order_data["cust_id"])
            if error2: return error2

            # 折扣跟折扣原因要嘛一起有要嘛一起沒有
            if (order_data["reason"] is None) != (order_data["discount"] is None):
                return jsonify({"error": "折扣與折扣原因必須同時填寫或同時留空"}), 400

            '''
            "transaction checklist"
            會rollback：
            1. 負責職員是否是在職 -> chk done
            2. 因為要取下來成為新訂單的編號，sequences 要扣起來
            需要處理的：
            1. seqquences取下來之後用要加一才能用
            2. 訂單編號格式為 “INV-YEARXXXXXX”
            '''
            # 新訂單的編號
            year = order_data["date"].year
            num = get_Seq_no(cursor, "Order", year)

            # 訂單編號格式為 “INV-YEARXXXXXX”
            order_no = f"INV-{year}{num:06d}"
            order_data.update({"order_no": order_no, "amount": 0})
            s_sum = ", ".join(["%s"] * len(order_data.values()))
            cursor.execute(f"insert into `Order` ({', '.join(order_data.keys())}) values ({s_sum})",
                           tuple(order_data.values()))
            return jsonify({"message": "create successed"}), 201

        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500


@order_bp.route("/order/<int:order_id>", methods = ["put"])
@login_required
def update_order(order_id):
    try:
        order_chk = type_update(**request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400
    order_data = order_chk.model_dump(exclude_unset=True)

    with connect_manger() as cursor:
        try:
            # firm order_id exist, role limit
            old_order, error3 = get_one(cursor, table, select_col2, "order_id", order_id, True)
            if error3: return error3

            if "staff_id" in order_data:
                error1 = chk_staff_id(cursor, order_data["staff_id"])
                if error1: return error1

            if "cust_id" in order_data:
                error2 = chk_cust_id(cursor, order_data["cust_id"])
                if error2: return error2

            # 折扣跟折扣原因要嘛一起有要嘛一起沒有
            final_reason = order_data.get("reason", old_order["reason"])
            final_discount = order_data.get("discount", old_order["discount"])
            if (final_reason is None) != (final_discount is None):
                return jsonify({"error": "折扣與折扣原因必須同時填寫或同時留空"}), 400

            if order_data.get("status") == "cancelled" and old_order["status"] != "processing":
                return jsonify({"error": "只有處理中的訂單可以被取消"}), 400

            if order_data:
                cols = ", ".join(f"{key} = %s" for key in order_data.keys())
                cursor.execute(f"update `Order` set {cols} where order_id = %s",
                           tuple(order_data.values()) + (order_id, ))

            return jsonify({"message": "update successed"}), 200

        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500
