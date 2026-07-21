from flask import jsonify, session
import re
from pydantic import field_validator

coname_fm = re.compile(r"^[a-zA-Z\u4e00-\u9fff\s\.]{1,255}$")
name_fm = re.compile(r"^[a-zA-Z\u4e00-\u9fff\s]{1,100}$")
goods_name_fm = re.compile(r"^[\w\u4e00-\u9fff\s]{1,100}$")
phone_fm = re.compile(r"^[\d\-\(\)]{8,30}$")
staff_no_fm = re.compile(r"^CS-\d{6}$")
cust_no_fm = re.compile(r"^K\d{6}$")

# 指定欄位
def empty_str_to_none(*fields):
    @field_validator(*fields, mode="before")
    @classmethod
    def _validator(cols, v):
        return None if v == "" else v
    return _validator

# 方便每個表 select all
def get_all(cursor, table_name: str, show_col: tuple, is_role_limit: bool=False) -> tuple:
    """
    Please remain the content of variable table_name need add `...`
    """
    if not is_role_limit or session["role"] == "admin":
        cursor.execute(f"select {', '.join(show_col)} from {table_name}")
    else:
        cursor.execute(f"select {', '.join(show_col)} from {table_name} where staff_id = %s", (session["staff_id"], ))
    result = cursor.fetchall()
    if cursor.rowcount == 0: return (jsonify([]), 200)
    return (jsonify(result), 200)
        
# 方便每個表 select one 順便處理 role limit
class NotFoundError(Exception):
    pass

class AuthError(Exception):
    pass

def get_one(cursor, table_name: str, show_col: tuple, id_col_name: str, id: int, is_role_limit: bool=False) -> dict:
    """
    Please remain the content of variable table_name need add `...`
    """
    cols = ", ".join(show_col)
    if is_role_limit:
        cols += " ,staff_id"
    cursor.execute(f"select {cols} from {table_name} where {id_col_name} = %s", (id, ))
    result = cursor.fetchone()

    if not result:
        raise NotFoundError("ID doesn't exist")
    if is_role_limit:
        if session["role"] != "admin" and session["staff_id"] != result["staff_id"]:
            raise AuthError("You do not have permission")
        del result["staff_id"]
    
    return result

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
                
