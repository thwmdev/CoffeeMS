import mysql.connector

def get_connection():

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root123",
        database="quanlyquancafe"
    )

    return conn