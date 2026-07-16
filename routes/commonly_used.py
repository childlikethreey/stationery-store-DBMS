import re
from datetime import date
from flask import jsonify, session

coname_fm = re.compile(r"^[a-zA-Z\u4e00-\u9fff\s\.]{1,255}$")
name_fm = re.compile(r"^[a-zA-Z\u4e00-\u9fff\s]{0,100}$")
goods_name_fm = re.compile(r"^[\w\u4e00-\u9fff\s]{1,100}$")
phone_fm = re.compile(r"^[\d\-\(\)]{8,30}$")
staff_no_fm = re.compile(r"^CS-\d{6}$")

# 捉必填
def must_fill_in(Needed_tuple: tuple, val: dict) -> tuple | None:
    for cols, vals in val.items():
        if cols in Needed_tuple and vals is None:
            return (jsonify({"error": f"{Needed_tuple} must be filled in"}), 400)    
    return None

# 捉不能空字串
def not_empty(Needed_tuple: tuple, val: dict) -> tuple | None:
    for cols, vals in val.items():
        if cols in Needed_tuple and vals == "":
            return (jsonify({"error": f"{Needed_tuple} cannot be empty"}), 400)    
    return None

# 捉格式不對
def check_fm(data: dict, val: dict) -> tuple | None:
    for col, fm in data.items():
        a = val[col]
        if a is not None and not fm.match(a):
            return (jsonify({"error": f"'{col}' format is not correct"}), 400)
    return None

# 三合一
def mix_chk(Needed_tuple: tuple, data: dict, val: dict, need_chk_fill: bool) -> tuple | None:
    if need_chk_fill:
        error1 = must_fill_in(Needed_tuple, val)
        if error1: return error1
    error2 = not_empty(Needed_tuple, val)
    if error2: return error2
    error3 = check_fm(data, val)
    if error3: return error3

# 方便每個表 select all
def get_all(cursor, table_name: str, show_col: tuple, is_role_limit: bool) -> tuple:
    if not is_role_limit or session["role"] == "admin":
        cursor.execute(f"select {', '.join(show_col)} from `{table_name}`")
    else:
        cursor.execute(f"select {', '.join(show_col)} from `{table_name}` where staff_id = %s", (session["staff_id"], ))
    result = cursor.fetchall()
    if cursor.rowcount == 0: return (jsonify([]), 200)
    return (jsonify(result), 200)
        
# 方便每個表 select one 順便處理 role limit
def get_one(cursor, table_name: str, show_col: tuple, id_colname: str, id: int, is_role_limit: bool) -> tuple:
    if id_colname in show_col:
        _ = show_col.pop(id_colname)
    cols = ", ".join(show_col) 
    if is_role_limit:
        cols += " ,staff_id"
    cursor.execute(f"select {cols} from {table_name} where {id_colname} = %s", (id, ))
    result = cursor.fetchone()

    if not result:
        return None, (jsonify({"error": "ID doesn't exist"}), 404)
    if is_role_limit:
        if session["role"] != "admin" and session["staff_id"] != result["staff_id"]:
            return None, (jsonify({"error": "You do not have permission"}), 403)
        del result["staff_id"]
    
    return result, None

# 取單號
def get_Seq_no(cursor, table_name: str, Seq_year: int) -> int:
    info = (table_name, Seq_year)
    cursor.execute("select last_num from `Sequences` where name = %s and year = %s for update",
                   info)
    r = cursor.fetchone()
    num = (r["last_num"] if r else 0) + 1
    if num == 1:
        cursor.execute("insert into `Sequences` (last_num, name, year) values (%s, %s, %s)",
                       (num, ) + info)
        return num
    
    cursor.execute("update `Sequences` set last_num = %s where name = %s and year = %s",
                   (num, ) + info)
    return num
                
