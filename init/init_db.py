import pymysql
import os
from dotenv import load_dotenv
from pymysql.constants import CLIENT
import json
import bcrypt

load_dotenv()
db_config = {
    'host': os.getenv('SERVER_INIT'),
    'user': os.getenv('ROOT_USERNAME'),
    'password': os.getenv('ROOT_PASSWORD'),
    'port': int(os.getenv('PORT_INIT')),
    'charset': 'utf8mb4',
    'client_flag': CLIENT.MULTI_STATEMENTS,
}

db_name = os.getenv('DBNAME')
ddl_file = 'init/ddl.sql'
seed_file = 'init/seed_data.json'

def clear_testdata(cursor):
    table_list = [
        "Staff", "Customer", "Supplier", "Invertory",
        "Purchase", "Order", "Sequences", "Promotion",
        "Promotion_details", "Order_details", "Purchase_details",
        "login_info"
        ]
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0") 
    for table in table_list:
        cursor.execute(f"TRUNCATE TABLE `{table}`")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

def main():
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    try:
        cursor.execute(
            f'create database if not exists {db_name} '
            f'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
        )
        conn.commit()
        
        cursor.execute(f'use {db_name}')
        '''
        with open(ddl_file, 'r', encoding='utf-8') as f:
            content = f.read()
        cursor.execute(content)
        conn.commit()
        '''

        if os.path.exists(seed_file):
            clear_testdata(cursor)
            conn.commit()
        
            with open(seed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            ref_map = {} 
            for tables, rows in data.items():
                for row in rows:
                    ref = row.pop('_ref', None)
                    for key, val in row.items():
                        if isinstance(val, str) and val.startswith('@'):
                            row[key] = ref_map[val[1:]]

                    if tables == 'login_info' and 'password' in row:
                        pw = row.pop('password')
                        temp = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
                        row['pw_hash'] = temp.decode('utf-8')

                    attributes = ', '.join(row.keys())
                    val = ', '.join(['%s']*len(row))
                    sql_instr = f'insert into `{tables}` ({attributes}) values ({val})'
                    cursor.execute(sql_instr, tuple(row.values()))

                    iid = cursor.lastrowid

                    if tables == 'Staff':
                        staff_no = f"CS-{iid:06d}"
                        cursor.execute("UPDATE `Staff` SET staff_no = %s WHERE staff_id = %s", (staff_no, iid))
                    elif tables == 'Order':
                        order_no = f"INV-2026{iid:06d}"
                        cursor.execute("UPDATE `Order` SET order_no = %s WHERE order_id = %s", (order_no, iid))    
                    elif tables == 'Customer':
                        cust_no = f"K{iid:06d}"
                        cursor.execute("UPDATE `Customer` SET cust_no = %s WHERE cust_id = %s", (cust_no, iid))
                    elif tables == 'Purchase':
                        pu_no = f"P-2026{iid:06d}"
                        cursor.execute("UPDATE `Purchase` SET pu_no = %s WHERE pu_id = %s", (pu_no, iid))    


                    if ref:
                        ref_map[ref] = iid
            conn.commit()
       
        else:
            print('seed file is not exist')

    except Exception as err:
        conn.rollback()
        print(f'Error occurred: {err} and rollback')
        raise

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()


