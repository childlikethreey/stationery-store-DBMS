import mysql.connector
import os

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("SERVER"),
        user=os.getenv("USERNAME"),
        password=os.getenv("PASSWORD"),
        database=os.getenv("DBNAME"),
        port=os.getenv("PORT")
    )