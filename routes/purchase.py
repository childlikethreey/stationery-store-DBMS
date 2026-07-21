from datetime import date as date_type
from flask import Blueprint, request, jsonify, session
from db import connect_manger
from routes.auth_required import login_required
from pydantic import BaseModel, Field
from typing import Optional
from routes.helpers import (
    get_Seq_no, get_all, get_one, empty_str_to_none,
    staff_no_fm, AuthError, NotFoundError)

table = "`Purchase`"
select_col = ("pu_id", "pu_no", "date", "amount")

table_details = "`Purchase_details`"

# Purchase_details
class type_create_detail(BaseModel):
    goods_id: int = Field(default=0, gt=0)
    unit: int = Field(default=0, ge=0)
    price: int = Field(default=0, ge=0)

# Purchase
class type_create(BaseModel):
    date: date_type = Field(default_factory=date_type.today)
    reason: Optional[str] = Field(default=None)
    discount: Optional[int] = Field(default=None, ge=0)
    staff_no: str = Field(pattern=staff_no_fm)
    details: list[type_create_detail] = Field(min_length=1)
    _ = empty_str_to_none("reason", "discount")
    
class type_update(BaseModel):
    date: Optional[date_type] = Field(default=None)
    reason: Optional[str] = None
    discount: Optional[int] = Field(default=None, ge=0)
    staff_no: Optional[str] = Field(default=None, pattern=staff_no_fm)
    details: Optional[list[type_create_detail]] = Field(default=None, min_length=1)
    _ = empty_str_to_none("reason", "discount")


pur_bp = Blueprint("purchase", __name__)


@pur_bp.route("/pur", methods = ["get"])
@login_required
def show_all_purchase():
    with connect_manger() as cursor:
        # role limit
        result = get_all(cursor, table, select_col, True)
        return result


@pur_bp.route("/pur/<int:pu_id>", methods = ["get"])
@login_required
def show_one_purchase(pu_id):
    with connect_manger() as cursor:
        # role limit
        _ = get_one(cursor, table, select_col, "pu_id", pu_id, True)

        cursor.execute(
            """
            select pu_no, date, reason, discount, amount, staff_no
            from `Purchase` join `Staff` using (staff_id)
            where pu_id = %s
            """, (pu_id, ))
        result = cursor.fetchone()

        cursor.execute(
            """
            select goods_id, I.name, P.unit, P.price, P.amount 
            from `Purchase_details` P join `Invertory` I using (goods_id)
            where pu_id = %s
            """, (pu_id, ))
        details = cursor.fetchall()
        result["details"] = details
        return result
    

@pur_bp.route("/pur", methods = ["post"])
@login_required
def create_purchase():
    '''
    Transaction checklist：
    1. Staff ID exist
    2. Staff is active
    3. 折扣與折扣原因必須同時填寫或同時留空
    4. 由`Sequences` 取號碼加一，即此訂單的編號，要update `Sequences`記得for update
    5. Goods ID exist and stop_purchase == False -> detail 
    6. detail最後要update total amount to `Purchase`
    7. Update `Invertory`
    '''
    data_chk = type_create(**request.get_json())
    data = data_chk.model_dump(exclude_unset=True)

    with connect_manger() as cursor:
        # check staff_id exist, is active
        user = get_one(cursor, "`Staff`", ("*", ), "staff_no", data["staff_no"], False)
        if not user["is_active"]:
            raise ValueError("Employee already quit")
            
        # 折扣與折扣原因必須同時填寫或同時留空
        if ("reason" in data) != ("discount" in data):
            raise ValueError("折扣與折扣原因必須同時填寫或同時留空")
            
        # 修正欄位
        details = data.pop("details")
        del data["staff_no"]
        data["staff_id"] = user["staff_id"]

        # 新訂單的編號, 入貨單編號格式為 “P-YEARXXXXXX”
        year = data["date"].year
        num = get_Seq_no(cursor, "Purchase", year)
        pu_no = f"P-{year}{num:06d}"
        data.update({"pu_no": pu_no})

        cols = ", ".join(data.keys())
        s_sum = ", ".join(["%s"] * len(data.values()))
        cursor.execute(f"insert into {table} ({cols}) values ({s_sum})", tuple(data.values()))

        num = cursor.lastrowid
        total_amount = 0
        for item in details:
            # check goods_id exits and not stop_purchase
            cursor.execute("select * from `Invertory` where goods_id = %s for update", (item["goods_id"],))
            goods = cursor.fetchone()
            if not goods:
                raise NotFoundError(f"{item['goods_id']} not exist")
            if goods["stop_purchase"]:
                raise ValueError(f"{item['goods_id']} cannot using")

            amount = item["unit"] * item["price"]
            total_amount += amount
            item.update({"pu_id": num, "amount": amount})
            item_cols = ", ".join(item.keys())
            item_sum = ", ".join(["%s"] * len(item.values()))
            cursor.execute(f"insert into {table_details} ({item_cols}) values ({item_sum})",
                            tuple(item.values()))
            
            # 更新庫存數量
            new_quantity = goods["quantity"] + item["unit"]
            cursor.execute("update `Invertory` set quantity = %s where goods_id = %s", (new_quantity, item["goods_id"]))
            
        total_amount -= data["discount"] if "discount" in data else 0
        cursor.execute(f"update {table} set amount = %s where pu_id = %s", (total_amount, num))
        return jsonify({"message": "create successed", "pu_no": pu_no}), 201
        

@pur_bp.route("/pur/<int:pu_id>", methods = ["put"])
@login_required
def update_purchase(pu_id):
    data_chk = type_update(**request.get_json())
    data = data_chk.model_dump(exclude_unset=True)
    
    with connect_manger() as cursor:
        '''
        Transaction checklist：
        1. Purchase ID exist
        2. Staff ID exist
        3. Staff is active
        4. role == "staff" cannot update 負責職員的編號
        5. 折扣與折扣原因必須同時填寫或同時留空
        6. Goods ID exist and stop_purchase == False-> detail 
        7. detail最後要update total amount to `Purchase`
        8. Update `Invertory`
        '''
        # check pu_id exist, role limit
        result = get_one(cursor, table, ("*", ), "pu_id", pu_id, True)
        pu_no = result["pu_no"]

        # check staff_id exist and is active, staff cannot update staff_id
        if "staff_no" in data:
            user = get_one(cursor, "`Staff`", ("*", ), "staff_no", data["staff_no"])
            if not user["is_active"]:
                raise ValueError("Employee already quit")
            if session["role"] == "staff":
                raise AuthError("You cannot change the staff_no")
            del data["staff_no"]
            data["staff_id"] = user["staff_id"]
            
        # 折扣跟折扣原因要嘛一起有要嘛一起沒有
        old_pur = get_one(cursor, table, ("reason", "discount"), "pu_id", pu_id, True)
        final_reason = data.get("reason", old_pur["reason"])
        final_discount = data.get("discount", old_pur["discount"])
        if (final_reason is not None) != (final_discount is not None):
            raise ValueError("折扣與折扣原因必須同時填寫或同時留空")
            
        # 修正欄位
        details = data.pop("details", None)
        not_update = True
        
        if data:
            cols = ', '.join([f"{key} = %s" for key in data.keys()])
            cursor.execute(f"update {table} set {cols} where pu_id = %s", tuple(data.values()) + (pu_id, ))
            if cursor.rowcount != 0:
                not_update = False

        # 處理明細
        if details is not None:
            cursor.execute(f"select goods_id, unit from {table_details} where pu_id = %s", (pu_id, ))
            for old in cursor.fetchall():
                cursor.execute("update `Invertory` set quantity = quantity - %s where goods_id = %s",
                                (old["unit"], old["goods_id"]))
            cursor.execute(f"delete from {table_details} where pu_id = %s", (pu_id,))

            total_amount = 0
            for item in details:
                # check goods_id exits and not stop_purchase
                cursor.execute("select * from `Invertory` where goods_id = %s for update", (item["goods_id"],))
                goods = cursor.fetchone()
                if not goods:
                    raise NotFoundError(f"{item['goods_id']} not exist")
                if goods["stop_purchase"]:
                    raise ValueError(f"{item['goods_id']} cannot using")
                
                amount = item["unit"] * item["price"]
                total_amount += amount
                item.update({"pu_id": pu_id, "amount": amount})
                item_cols = ", ".join(item.keys())
                item_sum = ", ".join(["%s"] * len(item.values()))
                cursor.execute(f"insert into {table_details} ({item_cols}) values ({item_sum})",tuple(item.values()))

                # 更新庫存數量
                new_quantity = goods["quantity"] + item["unit"]
                cursor.execute("update `Invertory` set quantity = %s where goods_id = %s", (new_quantity, item["goods_id"]))
                not_update = False

            total_amount -= final_discount or 0
            cursor.execute(f"update {table} set amount = %s where pu_id = %s", (total_amount, pu_id))
        
        if not_update:
            return jsonify({"message": "Not any update", "pu_no": pu_no}), 200
        return jsonify({"message": "update successed", "pu_no": pu_no}), 200
