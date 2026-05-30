from flask import Blueprint, render_template

pageR = Blueprint("pageR", __name__)

@pageR.route("/")
def login_page():
    return render_template("login.html")

@pageR.route("/menu")
def menu():
    return render_template("menu.html")

@pageR.route("/payment")
def payment():
    return render_template("payment.html")


@pageR.route("/recipe")
def recipe():
    return render_template("recipe.html")


@pageR.route("/report")
def report():
    return render_template("report.html")



@pageR.route("/inventory")
def inventory():
    return render_template("inventory.html")