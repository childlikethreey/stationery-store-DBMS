from datetime import date as date_type
import mysql.connector
from flask import Blueprint, request, jsonify, session
from db import connect_manger
from routes.auth_required import login_required
from routes.commonly_used import get_one
from pydantic import BaseModel, ValidationError, Field
from typing import Optional

table = "Purchase_details"
pur_exist_col = ("pu_id", "staff_id")
select_col= ("goods_id", "unit", "price", "amount")

class type_create_detail(BaseModel):
    goods_id: int
    unit: int = Field(default=0, ge=0)
    price: int = Field(default=0, ge=0)

class type_update_detail(BaseModel):
    goods_id: Optional[int] = Field(default=None, gt=0)
    unit: Optional[int] = Field(default=None, ge=0)
    price: Optional[int] = Field(default=None, ge=0)


def chk_goods_id(cursor, goods_id: int) -> tuple | None:
    cursor.execute("select * from `Invertory` where goods_id = %s", (goods_id, ))
    result = cursor.fetchone()
    if not result:
        return (jsonify({"error": "This goods ID doesn't exist"}), 404)
    if result["stop_purchase"]:
        return (jsonify({"error": "This goods has stopped purchase"}), 400)
    return None


def recalc_purchase_amount(cursor, pu_id):
    cursor.execute(
        "select coalesce(sum(amount), 0) as total from `Purchase_details` where pu_id = %s",
        (pu_id, )
    )
    total = cursor.fetchone()["total"]
    cursor.execute("select discount from `Purchase` where pu_id = %s", (pu_id, ))
    discount = cursor.fetchone()["discount"]
    total -= discount or 0
    cursor.execute("update `Purchase` set amount = %s where pu_id = %s", (total, pu_id))


pur_detail_bp = Blueprint("purchase_details", __name__)


@pur_detail_bp.route("/pur/<int:pu_id>/details", methods = ["get"])
@login_required
def show_details(pu_id):
    with connect_manger() as cursor:
        try:
            # firm pu_id exist & role limit
            _, error1 = get_one(cursor, table, pur_exist_col, "pu_id", pu_id, True)
            if error1: return error1

            cursor.execute(f"select {', '.join(select_col)} from {table} where pu_id = %s", (pu_id, ))
            result = cursor.fetchall()
            return jsonify(result), 200
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500


@pur_detail_bp.route("/pur/<int:pu_id>/details", methods = ["post"])
@login_required
def add_detail(pu_id):
    try:
        detail_chk = type_create_detail(**request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400
    data = detail_chk.model_dump()

    with connect_manger() as cursor:
        try:
            # firm pu_id exist & role limit
            _, error1 = get_one(cursor, table, pur_exist_col, "pu_id", pu_id, True)
            if error1: return error1

            # firm goods_id exist & not stop purchase
            error2 = chk_goods_id(cursor, data["goods_id"])
            if error2: return error2

            cursor.execute(
                "select * from `Purchase_details` where pu_id = %s and goods_id = %s",
                (pu_id, data["goods_id"])
            )
            if cursor.fetchone():
                return jsonify({"error": "ID already exists"}), 400

            amount = data["unit"] * data["price"]
            data.update({"amount": amount, "pu_id": pu_id})
            s_sum = ", ".join(["%s"] * len(data.values()))
            cursor.execute(
                f"insert into `Purchase_details` ({', '.join(data.keys())}) values ({s_sum})",
                tuple(data.values())
            )
            cursor.execute(
                "update `Invertory` set quantity = quantity + %s where goods_id = %s",
                (data["unit"], data["goods_id"])
            )

            recalc_purchase_amount(cursor, pu_id)
            return jsonify({"message": "create successed"}), 201
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500


@pur_detail_bp.route("/pur/<int:pu_id>/details/<int:goods_id>", methods = ["put"])
@login_required
def update_detail(pu_id, goods_id):
    try:
        detail_chk = type_update_detail(**request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400
    data = detail_chk.model_dump(exclude_unset=True)

    with connect_manger() as cursor:
        try:
            # firm pu_id exist & role limit
            _, error1 = get_one(cursor, table, pur_exist_col, "pu_id", pu_id, True)
            if error1: return error1

            cursor.execute(
                "select unit, price from `Purchase_details` where pu_id = %s and goods_id = %s",
                (pu_id, goods_id)
            )
            old = cursor.fetchone()
            if not old:
                return jsonify({"error": "ID doesn't exist"}), 404

            if "goods_id" in data:
                error2 = chk_goods_id(cursor, data["goods_id"])
                if error2: return error2

            if data:
                new_unit = data.get("unit", old["unit"])
                new_price = data.get("price", old["price"])
                data["amount"] = new_unit * new_price

                cols = ", ".join(f"{key} = %s" for key in data.keys())
                cursor.execute(
                    f"update `Purchase_details` set {cols} where pu_id = %s and goods_id = %s",
                    tuple(data.values()) + (pu_id, goods_id)
                )

                diff = new_unit - old["unit"]
                if diff != 0:
                    cursor.execute(
                        "update `Invertory` set quantity = quantity + %s where goods_id = %s",
                        (diff, goods_id)
                    )

                recalc_purchase_amount(cursor, pu_id)

            return jsonify({"message": "update successed"}), 200
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500


@pur_detail_bp.route("/pur/<int:pu_id>/details/<int:goods_id>", methods = ["delete"])
@login_required
def delete_detail(pu_id, goods_id):
    with connect_manger() as cursor:
        try:
            # firm pu_id exist & role limit
            _, error1 = get_one(cursor, table, pur_exist_col, "pu_id", pu_id, True)
            if error1: return error1

            cursor.execute(
                "select unit from `Purchase_details` where pu_id = %s and goods_id = %s",
                (pu_id, goods_id)
            )
            old = cursor.fetchone()
            if not old:
                return jsonify({"error": "ID doesn't exist"}), 404

            cursor.execute(
                "delete from `Purchase_details` where pu_id = %s and goods_id = %s",
                (pu_id, goods_id)
            )
            cursor.execute(
                "update `Invertory` set quantity = quantity - %s where goods_id = %s",
                (old["unit"], goods_id)
            )

            recalc_purchase_amount(cursor, pu_id)
            return jsonify({"message": "delete successed"}), 200
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500