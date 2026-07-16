from datetime import date as date_type, datetime
import mysql.connector
from flask import Blueprint, request, jsonify
from db import connect_manger
from routes.auth_required import login_required
from routes.commonly_used import get_one
from pydantic import BaseModel, ValidationError, Field
from typing import Optional

table = "Order_details"
order_exist_col = ("order_id", "staff_id")
select_col = ("goods_id", "pro_id", "unit", "price", "amount")

class type_create_detail(BaseModel):
    goods_id: int = Field(gt=0)
    pro_id: Optional[int] = Field(default=None, gt=0)
    unit: int = Field(default=0, ge=0)

class type_update_detail(BaseModel):
    goods_id: Optional[int] = Field(default=None, gt=0)
    pro_id: Optional[int] = Field(default=None, gt=0)
    unit: Optional[int] = Field(default=None, ge=0)


def chk_goods_id(cursor, goods_id: int) -> tuple | None:
    cursor.execute("select * from `Invertory` where goods_id = %s", (goods_id, ))
    result = cursor.fetchone()
    if not result:
        return (jsonify({"error": "This goods ID doesn't exist"}), 404)
    return None


def get_unit_price(cursor, goods_id: int, pro_id: int | None) -> tuple:
    if pro_id is not None:
        cursor.execute(
            "select price from `Promotion_details` where pro_id = %s and goods_id = %s",
            (pro_id, goods_id)
        )
        row = cursor.fetchone()
        if not row:
            return None, (jsonify({"error": "This promotion doesn't apply to this goods"}), 400)

        cursor.execute("select start_date, end_date from `Promotion` where pro_id = %s", (pro_id, ))
        promo = cursor.fetchone()
        if not promo:
            return None, (jsonify({"error": "This promotion ID doesn't exist"}), 404)
        now = datetime.now()
        if not (promo["start_date"] <= now <= promo["end_date"]):
            return None, (jsonify({"error": "This promotion is not active"}), 400)

        return row["price"], None

    cursor.execute("select price from `Invertory` where goods_id = %s", (goods_id, ))
    row = cursor.fetchone()
    return row["price"], None


def recalc_order_amount(cursor, order_id):
    cursor.execute(
        "select coalesce(sum(amount), 0) as total from `Order_details` where order_id = %s",
        (order_id, )
    )
    total = cursor.fetchone()["total"]
    cursor.execute("select discount from `Order` where order_id = %s", (order_id, ))
    discount = cursor.fetchone()["discount"]
    total -= discount or 0
    cursor.execute("update `Order` set amount = %s where order_id = %s", (total, order_id))


order_detail_bp = Blueprint("order_details", __name__)


@order_detail_bp.route("/order/<int:order_id>/details", methods = ["get"])
@login_required
def show_details(order_id):
    with connect_manger() as cursor:
        try:
            # firm order_id exist & role limit
            _, error1 = get_one(cursor, "Order", order_exist_col, "order_id", order_id, True)
            if error1: return error1

            cursor.execute(f"select {', '.join(select_col)} from {table} where order_id = %s", (order_id, ))
            result = cursor.fetchall()
            return jsonify(result), 200
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500


@order_detail_bp.route("/order/<int:order_id>/details", methods = ["post"])
@login_required
def add_detail(order_id):
    try:
        detail_chk = type_create_detail(**request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400
    data = detail_chk.model_dump()

    with connect_manger() as cursor:
        try:
            # firm order_id exist & role limit
            _, error1 = get_one(cursor, "Order", order_exist_col, "order_id", order_id, True)
            if error1: return error1

            # firm goods_id exist
            error2 = chk_goods_id(cursor, data["goods_id"])
            if error2: return error2

            cursor.execute(
                "select * from `Order_details` where order_id = %s and goods_id = %s",
                (order_id, data["goods_id"])
            )
            if cursor.fetchone():
                return jsonify({"error": "ID already exists"}), 400

            # 單價：促銷價格優先於貨品定價，而不是直接輸入
            price, error3 = get_unit_price(cursor, data["goods_id"], data["pro_id"])
            if error3: return error3

            # 庫存是否足夠
            cursor.execute("select quantity from `Invertory` where goods_id = %s", (data["goods_id"], ))
            stock = cursor.fetchone()["quantity"]
            if stock < data["unit"]:
                return jsonify({"error": "Not enough stock"}), 400

            amount = data["unit"] * price
            data.update({"price": price, "amount": amount, "order_id": order_id})
            s_sum = ", ".join(["%s"] * len(data.values()))
            cursor.execute(
                f"insert into `Order_details` ({', '.join(data.keys())}) values ({s_sum})",
                tuple(data.values())
            )
            cursor.execute(
                "update `Invertory` set quantity = quantity - %s where goods_id = %s",
                (data["unit"], data["goods_id"])
            )

            recalc_order_amount(cursor, order_id)
            return jsonify({"message": "create successed"}), 201
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500


@order_detail_bp.route("/order/<int:order_id>/details/<int:goods_id>", methods = ["put"])
@login_required
def update_detail(order_id, goods_id):
    try:
        detail_chk = type_update_detail(**request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400
    data = detail_chk.model_dump(exclude_unset=True)

    with connect_manger() as cursor:
        try:
            # firm order_id exist & role limit
            _, error1 = get_one(cursor, "Order", order_exist_col, "order_id", order_id, True)
            if error1: return error1

            cursor.execute(
                "select goods_id, pro_id, unit, price from `Order_details` where order_id = %s and goods_id = %s",
                (order_id, goods_id)
            )
            old = cursor.fetchone()
            if not old:
                return jsonify({"error": "ID doesn't exist"}), 404

            if "goods_id" in data:
                error2 = chk_goods_id(cursor, data["goods_id"])
                if error2: return error2

            if data:
                new_goods_id = data.get("goods_id", old["goods_id"])
                new_pro_id = data["pro_id"] if "pro_id" in data else old["pro_id"]
                new_unit = data.get("unit", old["unit"])

                # goods_id 或 pro_id 有變動時，單價要重新取
                if "goods_id" in data or "pro_id" in data:
                    new_price, error3 = get_unit_price(cursor, new_goods_id, new_pro_id)
                    if error3: return error3
                    data["price"] = new_price
                else:
                    new_price = old["price"]

                diff = new_unit - old["unit"]
                if diff > 0:
                    cursor.execute("select quantity from `Invertory` where goods_id = %s", (new_goods_id, ))
                    stock = cursor.fetchone()["quantity"]
                    if stock < diff:
                        return jsonify({"error": "Not enough stock"}), 400

                data["amount"] = new_unit * new_price

                cols = ", ".join(f"{key} = %s" for key in data.keys())
                cursor.execute(
                    f"update `Order_details` set {cols} where order_id = %s and goods_id = %s",
                    tuple(data.values()) + (order_id, goods_id)
                )

                if diff != 0:
                    cursor.execute(
                        "update `Invertory` set quantity = quantity - %s where goods_id = %s",
                        (diff, new_goods_id)
                    )

                recalc_order_amount(cursor, order_id)

            return jsonify({"message": "update successed"}), 200
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500


@order_detail_bp.route("/order/<int:order_id>/details/<int:goods_id>", methods = ["delete"])
@login_required
def delete_detail(order_id, goods_id):
    with connect_manger() as cursor:
        try:
            # firm order_id exist & role limit
            _, error1 = get_one(cursor, "Order", order_exist_col, "order_id", order_id, True)
            if error1: return error1

            cursor.execute(
                "select unit from `Order_details` where order_id = %s and goods_id = %s",
                (order_id, goods_id)
            )
            old = cursor.fetchone()
            if not old:
                return jsonify({"error": "ID doesn't exist"}), 404

            cursor.execute(
                "delete from `Order_details` where order_id = %s and goods_id = %s",
                (order_id, goods_id)
            )
            cursor.execute(
                "update `Invertory` set quantity = quantity + %s where goods_id = %s",
                (old["unit"], goods_id)
            )

            recalc_order_amount(cursor, order_id)
            return jsonify({"message": "delete successed"}), 200
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500
