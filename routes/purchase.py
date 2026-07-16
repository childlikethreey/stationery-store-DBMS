from datetime import date as date_type
import mysql.connector
from flask import Flask, Blueprint, request, jsonify
from db import get_connection, connect_manger
from routes.auth_required import login_required, admin_required
from routes.commonly_used import get_Seq_no, get_all, get_one
from pydantic import BaseModel, ValidationError, Field
from typing import Optional

table = "Purchase"
select_col1 = ("pu_no", "date", "amount", "pu_id")
select_col2 = ("pu_no", "date", "reason", "discount", "amount", "staff_id")

class type_create(BaseModel):
    date: date_type = Field(default_factory=date_type.today)
    reason: Optional[str] = None
    discount: Optional[int] = Field(default=None, ge=0)
    staff_id: int = Field(gt=0)

class type_update(BaseModel):
    date: Optional[date_type] = Field(default=None)
    reason: Optional[str] = None
    discount: Optional[int] = Field(default=None, ge=0)
    staff_id: Optional[int] = Field(default=None, gt=0)

def chk_staff_id(cursor, staff_id: int) -> tuple | None:
    cursor.execute("select * from `Staff` where staff_id = %s", (staff_id, ))
    result = cursor.fetchone()
    if not result:
        return (jsonify({"error": "This employee ID doesn't exist"}), 404)
    if not result["is_active"]:
        return (jsonify({"error": "This employee already quit"}), 400)
    return None


pur_bp = Blueprint("purchase", __name__)


# 可以顯示入貨單的基本資料
@pur_bp.route("/pur", methods = ["get"])
@login_required
def show_all_purchase():
    with connect_manger() as cursor:
        try:
            result = get_all(cursor, table, select_col1, True)
            return result
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500


# 可以顯示入貨單的基本資料（ONE）
@pur_bp.route("/pur/<int:pu_id>", methods = ["get"])
@login_required
def show_one_purchase(pu_id):
    with connect_manger() as cursor:
        try:
            pur, error = get_one(cursor, table, select_col1, "pu_id", pu_id, True)
            if error:
                return error
            else:
                return jsonify(pur), 200
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500
    

@pur_bp.route("/pur", methods = ["post"])
@login_required
def create_purchase():
    try:
        pur_chk = type_create(**request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400
    pur_data = pur_chk.model_dump()
    
    with connect_manger() as cursor:
        try:
            # firm staff_id exist & working
            error1 = chk_staff_id(cursor, pur_data["staff_id"])
            if error1: return error1
            
            # 折扣跟折扣原因要嘛一起有要嘛一起沒有
            if (pur_data["reason"] is None) != (pur_data["discount"] is None):
                return jsonify({"error": "折扣與折扣原因必須同時填寫或同時留空"}), 400

            '''
            "transaction checklist"
            會rollback：
            1. 負責職員是否是在職 -> chk done
            2. 因為要取下來成為新訂單的編號，sequences 要扣起來
            需要處理的：
            1. seqquences取下來之後用要加一才能用
            2. 入貨單編號格式為 “P-YEARXXXXXX”
            '''
            # 新訂單的編號
            year = pur_data["date"].year
            num = get_Seq_no(cursor, "Purchase", year)
        
            # 入貨單編號格式為 “P-YEARXXXXXX”
            pu_no = f"P-{year}{num:06d}"
            pur_data.update({"pu_no": pu_no, "amount": 0})
            s_sum = ", ".join(["%s"] * len(pur_data.values()))
            cursor.execute(f"insert into `Purchase` ({', '.join(pur_data.keys())}) values ({s_sum})",
                           tuple(pur_data.values()))
            return jsonify({"message": "create successed"}), 201
    
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500
        

@pur_bp.route("/pur/<int:pu_id>", methods = ["put"])
@login_required
def update_purchase(pu_id):
    try:
        pur_chk = type_update(**request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400
    pur_data = pur_chk.model_dump(exclude_unset=True)
    
    with connect_manger() as cursor:
        try:
            # firm pu_id, staff_id exist & working
            old_pur, error3 = get_one(cursor, table, select_col2, "pu_id", pu_id, True)
            if error3: return error3

            if "staff_id" in pur_data:
                error1 = chk_staff_id(cursor, pur_data["staff_id"])
                if error1: return error1
            
            # 折扣跟折扣原因要嘛一起有要嘛一起沒有
            final_reason = pur_data.get("reason", old_pur["reason"])
            final_discount = pur_data.get("discount", old_pur["discount"])
            if (final_reason is None) != (final_discount is None):
                return jsonify({"error": "折扣與折扣原因必須同時填寫或同時留空"}), 400
            
            if pur_data:
                cols = ", ".join(f"{key} = %s" for key in pur_data.keys())
                cursor.execute(f"update `Purchase` set {cols} where pu_id = %s",
                           tuple(pur_data.values()) + (pu_id, ))
    
            return jsonify({"message": "update successed"}), 200
    
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500
