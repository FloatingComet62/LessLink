from os import getenv
from string import ascii_letters, digits
from random import randint as random
from flask import Flask, request, render_template, redirect, session
from validators import url
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
KEY = getenv(key="MASTER_KEY")
app.secret_key = KEY
client = MongoClient(getenv("MONGO"))
collection = client["redirects"]["redirects"]


def generateLink():
    chars = ascii_letters + digits + "-_"
    link = ""
    for _ in range(11):
        link += chars[random(0, len(chars) - 1)]
    return link

@app.get("/")
def main():
    if 'user' in session:
        if 'alert' in request.args:
            return render_template("index.html", alert={"type": request.args['alert'], "text": request.args['message']}, links= [i for i in collection.find({})])
        return render_template("index.html", user=session['user'], links= [i for i in collection.find({})])
    return """
    <center style="margin-top: 1rem;">
        <form action="/login" method="post">
            <h1> Login </h1>
            <input type="password" name="password" placeholder="Password">
            <input type="submit" value="Login">
        </form>
    </center>
    """

@app.post("/login")
def login():
    if request.form.get("password") == KEY:
        session['user'] = True
    return redirect("/")

@app.route("/add-link", methods=['POST'])
def callback():
    if request.method == "POST":
        outlink = request.form.get("link")
        if request.form.get("custom"):
            inlink = request.form.get("code")
            inlink = inlink.replace(" ", "_")
        else:
            inlink = generateLink()
        if collection.find_one({"_id": inlink}):
            return redirect(f"/?alert=danger&message=Link%20already%20exists")
        if url(outlink):
            collection.insert_one({"_id": inlink, "link": outlink, "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "clicks": 0})
            return redirect(f"/?alert=success&message=Link%20created%20successfully")
        else:
            return redirect(f"/?alert=danger&message=Invalid%20URL")
    return render_template("index.html")

@app.route("/action/<action>/<link>")
def action(action, link):
    if 'user' in session:
        if action == "delete":
            collection.delete_one({"_id": link})
            return redirect(f"/?alert=success&message=Link%20deleted%20successfully")
        elif action == "edit":
            newlink = request.args.get("link")
            if url(newlink):
                collection.update_one({"_id": link}, {"$set": {"link": newlink}})
                return redirect(f"/?alert=success&message=Link%20edited%20successfully")
            else:
                return redirect(f"/?alert=danger&message=Invalid%20URL")
    return redirect("/")

@app.route("/r/<link>")
def outlink(link):
    res = collection.find_one({"_id": link})
    if res:
        collection.update_one({"_id": link}, {"$inc": {"clicks": 1}})
        return redirect(res["link"], code=302)
    return redirect("Doesn't exist lol")


if __name__ == "__main__":
    app.run(debug=True)
