import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Flask, request, jsonify, send_from_directory, send_file
import os, io, warnings, re
import pandas as pd
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import dateparser

warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

# --- Setup ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama3-8b-8192", temperature=0)
DATA_FILE = "feedback_data.csv"

# Load CSV safely
if os.path.exists(DATA_FILE):
    data = pd.read_csv(DATA_FILE)
    # Convert all dates to datetime, invalid ones become NaT
    data["date"] = pd.to_datetime(data["date"], errors='coerce')
    # Drop rows where date could not be parsed
    data = data[data["date"].notna()].copy()
    data["date"] = data["date"].astype("datetime64[ns]")
else:
    data = pd.DataFrame(columns=["date", "feedback", "sentiment"])

# --- Prompts ---
feedback_prompt = PromptTemplate(
    input_variables=["feedback"],
    template="""
You are a polite restaurant assistant.
Analyze the sentiment of the following customer feedback and reply in a friendly tone.
Don't ask for personal details.
Don't mention anywhere this is an automated reply.
Feedback: {feedback}
Return:
Automated reply (1-2 sentences)
"""
)
sentiment_prompt = PromptTemplate(
    input_variables=["feedback"],
    template="Classify the sentiment of this review as Positive, Negative, or Neutral:\nReview: {feedback}\nOnly return the sentiment word."
)

# --- Helper Functions ---
def feedback_response_agent(feedback: str) -> str:
    prompt = feedback_prompt.format(feedback=feedback)
    response = llm.invoke(prompt)
    return response.content.strip()

def classify_sentiment(feedback: str) -> str:
    prompt = sentiment_prompt.format(feedback=feedback)
    try:
        result = llm.invoke(prompt).content.strip().capitalize()
        return result if result in ("Positive","Negative","Neutral") else "Neutral"
    except Exception as e:
        print("Sentiment classification error:", e)
        return "Neutral"

def parse_date_range(input_str: str):
    input_str = input_str.lower().strip()
    match = re.match(r"last\s+(\d+)\s+day", input_str)
    if match:
        days = int(match.group(1))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date
    if "to" in input_str:
        parts = input_str.split("to")
    else:
        parts = [input_str]
    if len(parts) == 2:
        start = dateparser.parse(parts[0].strip())
        end = dateparser.parse(parts[1].strip())
        if start and end:
            return start, end
    elif len(parts) == 1:
        single = dateparser.parse(parts[0].strip())
        if single:
            return single, single
    return datetime.now()-timedelta(days=7), datetime.now()

# --- Flask App ---
app = Flask(__name__)

@app.route("/")
def feedback_page():
    return send_from_directory(".", "feedback.html")

@app.route("/graph-page")
def graph_page():
    return send_from_directory(".", "graph.html")

@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():
    global data
    req = request.get_json()
    feedback_text = req.get("feedback","").strip()
    if not feedback_text:
        return jsonify({"message":"⚠️ Please enter some feedback."}), 400
    reply = feedback_response_agent(feedback_text)
    sentiment = classify_sentiment(feedback_text)
    new_entry = pd.DataFrame({
        "date":[pd.Timestamp.now()],
        "feedback":[feedback_text],
        "sentiment":[sentiment]
    })
    data = pd.concat([data,new_entry],ignore_index=True)
    data.to_csv(DATA_FILE,index=False)
    return jsonify({"message": reply})

@app.route("/sentiment-graph", methods=["GET"])
def sentiment_graph():
    global data
    date_range_str = request.args.get("range","last 7 days")
    start, end = parse_date_range(date_range_str)
    
    df = data.copy()
    df = df[df["date"].notna()]  # remove invalid dates
    df = df[(df["date"] >= start) & (df["date"] <= end)]

    img = io.BytesIO()
    plt.figure(figsize=(10,6),facecolor="#B95D3B")

    if df.empty:
        plt.text(0.5,0.5,"No feedback data available",ha="center",va="center",fontsize=14)
        plt.axis("off")
    else:
        days = pd.date_range(start, end)
        neg, neu, pos = [], [], []
        for day in days:
            day_feedbacks = df[df["date"].dt.date == day.date()]
            neg.append(len(day_feedbacks[day_feedbacks["sentiment"]=="Negative"]))
            neu.append(len(day_feedbacks[day_feedbacks["sentiment"]=="Neutral"]))
            pos.append(len(day_feedbacks[day_feedbacks["sentiment"]=="Positive"]))

        labels = [d.strftime("%Y-%m-%d") for d in days]
        plt.plot(labels, neg, marker='o', label='Negative', color='red')
        plt.plot(labels, pos, marker='o', label='Positive', color='green')
        plt.plot(labels, neu, marker='o', label='Neutral', color='gray')
        plt.title(f"Sentiment Counts from {labels[0]} to {labels[-1]}")
        plt.xlabel("Date")
        plt.ylabel("Feedback Count")
        plt.legend()
        plt.xticks(labels[::max(1,len(labels)//10)], rotation=45)
        plt.grid(True)

    plt.tight_layout()
    plt.savefig(img, format='png')
    plt.close('all')
    img.seek(0)
    return send_file(img, mimetype='image/png')

if __name__=="__main__":
    app.run(debug=True)
