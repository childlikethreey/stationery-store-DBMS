import re
from flask import jsonify

coname_fm = re.compile(r"^[a-zA-Z\u4e00-\u9fff\s\.]{1,255}$")
name_fm = re.compile(r"^[a-zA-Z\u4e00-\u9fff\s]{0,100}$")
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
