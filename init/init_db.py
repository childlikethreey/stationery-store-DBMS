import pymysql
import os
from dotenv import load_dotenv
from pymysql.constants import CLIENT
import json

load_dotenv()
db_config = {
    'host': os.getenv('SERVER'),
    'user': os.getenv('USERNAME'),
    'password': os.getenv('PASSWORD'),
    'port': int(os.getenv('PORT')),
    'charset': 'utf8mb4',
    'client_flag': CLIENT.MULTI_STATEMENTS,
}

db_name = os.getenv('DBNAME')
ddl_file = 'init/ddl.sql'
seed_file = ''

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
        with open(ddl_file, 'r', encoding='utf-8') as f:
            content = f.read()
        '''
        stmt = [s.strip() for s in content.split(';') if s.strip()]
        for n in stmt:
            cursor.execute(n)
        '''
        cursor.execute(content)
        conn.commit()

        if os.path.exists(seed_file):
            with open(seed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for tables, tuples in data.items():
                for tuple in tuples:
                    attributes = ', '.join(tuple.keys())
                    val = ', '.join(['%s']*len(tuple))
                    sql_instr = f'insert into {tables} ({attributes}) values ({val})'
                    cursor.execute(sql_instr, tuple(tuple.values()))
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


