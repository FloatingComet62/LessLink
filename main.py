from os import getenv
from string import ascii_letters, digits
from random import randint as random
from flask import Flask, request, render_template, redirect, session
from validators import url
from pymongo import MongoClient
from dotenv import load_dotenv

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
        return render_template("index.html", user=session['user'])
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
        outlink = request.form.get('link')
        valid = url(outlink)
        if not valid:
            return render_template("invalid.html")

        inlink = generateLink()
        collection.insert_one({"inlink": inlink, "outlink": outlink})

        base = request.base_url.split("/")
        base.pop()
        base = "/".join(base)
        return render_template("valid.html", link=inlink, domain=base)
    return render_template("index.html")


@app.route("/s/<link>")
def outlink(link):
    res = collection.find({"inlink": link})
    return redirect(res[0]["outlink"], code=302)


if __name__ == "__main__":
    app.run(debug=True)
