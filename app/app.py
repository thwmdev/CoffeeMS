from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

conn = mysql.connector.connect(
    host="localhost",
    user="Nia",
    password="123456",
    database="quanlyquancafe"
)

cursor = conn.cursor(dictionary=True)

@app.route("/mon", methods=["GET"])
def get_mon():

    sql = "SELECT * FROM MON"

    cursor.execute(sql)

    result = cursor.fetchall()

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)