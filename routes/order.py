from datetime import date as date_type
import re
from flask import Blueprint, request, jsonify, session
from db import connect_manger
from routes.auth_required import login_required, admin_required
from pydantic import BaseModel, Field
from typing import Optional, Literal
from routes.helpers import (
    get_Seq_no, get_all, get_one, empty_str_to_none,
    staff_no_fm, AuthError, NotFoundError)

cust_no_fm = re.compile(r"^K\d{6}$")

table = "`Order`"
select_col = ("order_id", "order_no", "date", "amount", "status")
table_details = "`Order_details`"

status_options = Literal["processing", "shipped", "completed", "cancelled"]


class type_create_detail(BaseModel):
    goods_id: int = Field(gt=0)
    unit: int = Field(gt=0)


class type_create(BaseModel):
    date: date_type = Field(default_factory=date_type.today)
    reason: Optional[str] = Field(default=None)
    discount: Optional[int] = Field(default=None, ge=0)
    staff_no: str = Field(pattern=staff_no_fm)
    cust_no: str = Field(pattern=cust_no_fm)
    details: list[type_create_detail] = Field(min_length=1)
    _ = empty_str_to_none("reason", "discount")


class type_update(BaseModel):
    date: Optional[date_type] = Field(default=None)
    reason: Optional[str] = None
    discount: Optional[int] = Field(default=None, ge=0)
    staff_no: Optional[str] = Field(default=None, pattern=staff_no_fm)
    cust_no: Optional[str] = Field(default=None, pattern=cust_no_fm)
    status: Optional[status_options] = Field(default=None)
    details: Optional[list[type_create_detail]] = Field(default=None, min_length=1)
    _ = empty_str_to_none("reason", "discount")


order_bp = Blueprint("order", __name__)


def _apply_detail(cursor, order_id, item):
    """檢查庫存、寫入 Order_details、扣庫存，回傳這筆明細金額"""
    cursor.execute("select * from `Invertory` where goods_id = %s for update", (item["goods_id"],))
    goods = cursor.fetchone()
    if not goods:
        raise NotFoundError(f"{item['goods_id']} not exist")
    if goods["quantity"] < item["unit"]:
        raise ValueError(f"{item['goods_id']} 庫存不足")

    price = goods["price"]
    amount = price * item["unit"]
    item.update({"order_id": order_id, "price": price, "amount": amount})

    item_cols = ", ".join(item.keys())
    item_sum = ", ".join(["%s"] * len(item.values()))
    cursor.execute(f"insert into {table_details} ({item_cols}) values ({item_sum})",
                    tuple(item.values()))

    new_quantity = goods["quantity"] - item["unit"]
    cursor.execute("update `Invertory` set quantity = %s where goods_id = %s",
                    (new_quantity, item["goods_id"]))
    return amount


@order_bp.route("/order", methods=["get"])
@login_required
def show_all_order():
    with connect_manger() as cursor:
        result = get_all(cursor, table, select_col, True)
        return result


@order_bp.route("/order/<int:order_id>", methods=["get"])
@login_required
def show_one_order(order_id):
    with connect_manger() as cursor:
        _ = get_one(cursor, table, select_col, "order_id", order_id, True)

        cursor.execute(
            """
            select order_id, order_no, O.date, O.reason, O.discount, O.amount, O.status,
                   staff_no, cust_no
            from `Order` O
                join `Staff` using (staff_id)
                join `Customer` using (cust_id)
            where order_id = %s
            """, (order_id,))
        result = cursor.fetchone()

        cursor.execute(
            """
            select D.goods_id, I.name, D.unit, D.price, D.amount
            from `Order_details` D join `Invertory` I using (goods_id)
            where order_id = %s
            """, (order_id,))
        details = cursor.fetchall()
        result["details"] = details
        return result


@order_bp.route("/order", methods=["post"])
@login_required
def create_order():
    '''
    Transaction checklist：
    1. Staff ID exist
    2. Staff is active
    3. Cust ID exist
    4. 折扣與折扣原因必須同時填寫或同時留空
    5. 由 `Sequences` 取號碼加一，即此訂單的編號
    6. Goods ID exist，並確認庫存足夠 -> 用 Invertory 定價
    7. detail 最後要 update total amount 到 `Order`
    8. 扣 `Invertory` 庫存
    '''
    data_chk = type_create(**request.get_json())
    data = data_chk.model_dump(exclude_unset=True)

    with connect_manger() as cursor:
        user = get_one(cursor, "`Staff`", ("*", ), "staff_no", data["staff_no"], False)
        if not user["is_active"]:
            raise ValueError("Employee already quit")

        cust = get_one(cursor, "`Customer`", ("*", ), "cust_no", data["cust_no"], False)

        if ("reason" in data) != ("discount" in data):
            raise ValueError("折扣與折扣原因必須同時填寫或同時留空")

        details = data.pop("details")
        del data["staff_no"]
        del data["cust_no"]
        data["staff_id"] = user["staff_id"]
        data["cust_id"] = cust["cust_id"]

        year = data["date"].year
        num = get_Seq_no(cursor, "Order", year)
        order_no = f"INV-{year}{num:06d}"
        data.update({"order_no": order_no})

        cols = ", ".join(data.keys())
        s_sum = ", ".join(["%s"] * len(data.values()))
        cursor.execute(f"insert into {table} ({cols}) values ({s_sum})", tuple(data.values()))
        new_id = cursor.lastrowid

        total_amount = 0
        for item in details:
            total_amount += _apply_detail(cursor, new_id, item)

        total_amount -= data["discount"] if "discount" in data else 0
        cursor.execute(f"update {table} set amount = %s where order_id = %s", (total_amount, new_id))
        return jsonify({"message": "create successed", "order_no": order_no}), 201


@order_bp.route("/order/<int:order_id>", methods=["put"])
@login_required
def update_order(order_id):
    data_chk = type_update(**request.get_json())
    data = data_chk.model_dump(exclude_unset=True)

    with connect_manger() as cursor:
        '''
        Transaction checklist：
        1. Order ID exist
        2. Staff ID exist
        3. Staff is active
        4. Cust ID exist
        5. role == "staff" cannot update 負責職員的編號
        6. 折扣與折扣原因必須同時填寫或同時留空
        7. 狀態變更規則：
           - cancelled 訂單不可再異動狀態
           - 改成 cancelled，只有原本是 processing 才可以，而且只有負責職員或 admin 可以做
        8. 只有 processing 狀態才可修改明細
        9. Goods ID exist，確認庫存足夠 -> detail
        10. detail 最後要 update total amount 到 `Order`
        11. 更新 `Invertory`
        '''
        result = get_one(cursor, table, ("*", ), "order_id", order_id, True)
        order_no = result["order_no"]
        old_status = result["status"]

        # 狀態變更檢查
        if "status" in data:
            new_status = data["status"]
            if old_status == "cancelled":
                raise ValueError("已取消的訂單無法異動狀態")
            if new_status == "cancelled":
                if old_status != "processing":
                    raise ValueError("只有處理中的訂單可以被取消")
                if session["role"] != "admin" and session["staff_id"] != result["staff_id"]:
                    raise AuthError("You do not have permission")

        if "staff_no" in data:
            user = get_one(cursor, "`Staff`", ("*", ), "staff_no", data.pop("staff_no"), False)
            if not user["is_active"]:
                raise ValueError("Employee already quit")
            if session["role"] == "staff":
                raise AuthError("You cannot change the staff_no")
            data["staff_id"] = user["staff_id"]

        if "cust_no" in data:
            cust = get_one(cursor, "`Customer`", ("*", ), "cust_no", data.pop("cust_no"), False)
            data["cust_id"] = cust["cust_id"]

        old_order = get_one(cursor, table, ("reason", "discount"), "order_id", order_id, True)
        final_reason = data.get("reason", old_order["reason"])
        final_discount = data.get("discount", old_order["discount"])
        if (final_reason is not None) != (final_discount is not None):
            raise ValueError("折扣與折扣原因必須同時填寫或同時留空")

        details = data.pop("details", None)
        if details is not None and old_status != "processing":
            raise ValueError("只有處理中的訂單可以修改明細")

        not_update = True

        if data:
            cols = ", ".join([f"{key} = %s" for key in data.keys()])
            cursor.execute(f"update {table} set {cols} where order_id = %s",
                            tuple(data.values()) + (order_id,))
            if cursor.rowcount != 0:
                not_update = False

        if details is not None:
            cursor.execute(f"select goods_id, unit from {table_details} where order_id = %s", (order_id,))
            for od in cursor.fetchall():
                cursor.execute("update `Invertory` set quantity = quantity + %s where goods_id = %s",
                                (od["unit"], od["goods_id"]))
            cursor.execute(f"delete from {table_details} where order_id = %s", (order_id,))

            total_amount = 0
            for item in details:
                total_amount += _apply_detail(cursor, order_id, item)

            total_amount -= final_discount or 0
            cursor.execute(f"update {table} set amount = %s where order_id = %s", (total_amount, order_id))
            not_update = False

        if not_update:
            return jsonify({"message": "Not any update", "order_no": order_no}), 200
        return jsonify({"message": "update successed", "order_no": order_no}), 200