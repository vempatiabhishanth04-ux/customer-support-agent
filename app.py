from flask import Flask, render_template, request, redirect, session
from openai import OpenAI
import json, os

app = Flask(__name__)
app.secret_key = "secret123"

client = OpenAI(api_key="YOUR_API_KEY")

# ---------- Load Data ----------
def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return []

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# ---------- Auth ----------
@app.route("/", methods=["GET", "POST"])
def login():
    users = load_json("users.json")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        for u in users:
            if u["username"] == username and u["password"] == password:
                session["user"] = username
                return redirect("/chat")

        return "Invalid login"

    return render_template("login.html")

# ---------- Chat Page ----------
@app.route("/chat")
def chat_page():
    if "user" not in session:
        return redirect("/")
    return render_template("chat.html")

# ---------- Intent ----------
def detect_intent(q):
    q = q.lower()
    if "refund" in q:
        return "refund"
    elif "order" in q:
        return "order"
    return "general"

# ---------- Hindsight ----------
def is_bad_query(q):
    feedback = load_json("feedback.json")
    for f in feedback:
        if f["query"] == q and f["feedback"] == "bad":
            return True
    return False

# ---------- AI ----------
def ai_reply(q):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": q}]
    )
    return res.choices[0].message.content

# ---------- CascadeFlow ----------
def handle(q):
    if is_bad_query(q):
        return "Connecting to human support..."

    intent = detect_intent(q)

    if intent == "order":
        return "Your order is on the way 🚚"
    elif intent == "refund":
        return "Refund request submitted 💸"
    else:
        return ai_reply(q)

# ---------- API ----------
@app.route("/send", methods=["POST"])
def send():
    q = request.form["query"]
    res = handle(q)
    return res

@app.route("/feedback", methods=["POST"])
def feedback():
    data = load_json("feedback.json")
    data.append({
        "query": request.form["query"],
        "response": request.form["response"],
        "feedback": request.form["type"]
    })
    save_json("feedback.json", data)
    return "ok"

app.run(host="0.0.0.0", port=5000, debug=True)