from flask import Blueprint, render_template

pageR = Blueprint("pageR", __name__)

@pageR.route("/")
def login_page():
    return render_template("login.html")