import re
from flask import jsonify

coname_fm = re.compile(r"^[a-zA-Z\u4e00-\u9fff\s\.]{1,255}$")
name_fm = re.compile(r"^[a-zA-Z\u4e00-\u9fff\s]{0,100}$")
phone_fm = re.compile(r"^[\d\-\(\)]{8,30}$")
staff_no_fm = re.compile(r"^CS-\d{6}$")

def check_fm(data: dict, val: dict) -> tuple | None:
    for col, fm in data.items():
        a = val[col]
        if a is not None and not fm.match(a):
            return (jsonify({"error": f"'{col}' format is not correct"}), 400)
    return None

def not_empty(Needed_tuple: tuple, val: dict) -> tuple | None:
    for cols, vals in val.items():
        if cols in Needed_tuple and vals == "":
            return (jsonify({"error": f"{Needed_tuple} cannot be empty"}), 400)    
    return None

def must_fill_in(Needed_tuple: tuple, val: dict) -> tuple | None:
    for cols, vals in val.items():
        if cols in Needed_tuple and vals is None:
            return (jsonify({"error": f"{Needed_tuple} must be filled in"}), 400)    
    return None