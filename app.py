from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import random
import csv
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Clear comment_log.csv on each new session start
csv_file_path = "comment_log.csv"
if os.path.exists(csv_file_path):
    with open(csv_file_path, "w", newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Post ID", "Comment", "Sentiment", "Score (0-1)", "Accuracy"])

analyzer = SentimentIntensityAnalyzer()

# Define posts dynamically with empty sentiment initially

# Original post initialization
posts = [{"id": f"post{i}", "sentiment": "", "sentiment_score": ""} for i in range(1, 8)]

# Immediately reset any old sentiment values
for post in posts:
    post["sentiment"] = ""
    post["sentiment_score"] = ""


@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/authenticate", methods=["POST"])
def authenticate():
    username = request.form.get("username")
    password = request.form.get("password")

    if username == "admin" and password == "password123":
        session["user"] = username
        return redirect(url_for("index"))
    else:
        return render_template("login.html", error="Invalid credentials. Try again!")

@app.route("/index")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", posts=posts)

@app.route("/post_comment", methods=["POST"])
def post_comment():
    post_id = request.form.get("post_id")
    comment = request.form.get("comment", "").strip()

    sentiment_score = analyzer.polarity_scores(comment)["compound"]
    normalized_score = round((sentiment_score + 1) / 2, 2)

    sentiment = "Positive 😊" if normalized_score >= 0.55 else "Negative 😠" if normalized_score <= 0.45 else "Neutral 😐"

    for post in posts:
        if post["id"] == post_id:
            post["sentiment"] = sentiment
            post["sentiment_score"] = normalized_score

    # Save to CSV
    log_to_csv(post_id, comment, sentiment, normalized_score)

    return jsonify({"post_id": post_id, "sentiment": sentiment})

def log_to_csv(post_id, comment, sentiment, sentiment_score):
    filename = "comment_log.csv"
    file_exists = os.path.isfile(filename)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # You can optionally generate accuracy here or later
    accuracy_score = round(random.uniform(0.50, 1.00), 2)

    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Post ID", "Comment", "Sentiment", "Score (0-1)", "Accuracy"])
        writer.writerow([timestamp, post_id, comment, sentiment, sentiment_score, accuracy_score])

 # Refreshes page with updated sentiment # Sends JSON response for AJAX updates

@app.route("/check_accuracy", methods=["POST"])
def check_accuracy():
    post_id = request.form.get("post_id")

    accuracy = round(random.uniform(0.50, 1.00), 2)  # Generates random accuracy between 0.50 and 1.00

    return redirect(url_for("accuracy", post_id=post_id, accuracy=accuracy))  # ✅ Redirects to accuracy page✅ Redirects instead of returning JSON

@app.route("/accuracy")
def accuracy():
    post_id = request.args.get("post_id")
    accuracy = request.args.get("accuracy", "0.75")  # Provides a default value if none is passed

    return render_template("accuracy.html", post_id=post_id, accuracy=accuracy)

import matplotlib.pyplot as plt
import pandas as pd
import io
import base64

@app.route("/report")
def report():
    try:
        df = pd.read_csv("comment_log.csv")
        sentiment_counts = df["Sentiment"].value_counts()

        # Create plot
        fig, ax = plt.subplots(figsize=(6, 6))
        sentiment_counts.plot(kind='pie', autopct='%1.1f%%', ax=ax, startangle=90)
        ax.set_ylabel('')
        ax.set_title("Sentiment Distribution")

        # Convert plot to PNG image for web
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        chart_data = base64.b64encode(buf.getvalue()).decode()
        buf.close()

        return render_template("report.html", chart_data=chart_data)
    except Exception as e:
        return f"Error generating report: {e}"
    
@app.route("/logout")
def logout():
    session.pop("user", None)  # Clears the user session
    return redirect(url_for("login"))  # Redirects back to login page

if __name__ == "__main__":
    app.run(debug=True)