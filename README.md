# SteamNoodles Feedback Agent

## Author
**Nathasha Nethmini** – University of Moratuwa, 2nd Year

---

## Project Summary
This project implements **two AI agents** for SteamNoodles:  

1. **Feedback Response Agent** – Automatically responds to customer reviews with polite, context-aware messages using sentiment analysis.  
2. **Sentiment Visualization Agent** – Generates dynamic plots showing positive, negative, and neutral feedback trends over a user-defined date range.

---

## Project Files
- `agent.py` → Main Python script (agents + Flask app)  
- `feedback.html` → Web page for submitting feedback  
- `graph.html` → Web page for viewing sentiment plots  
- `.env` → Environment variables (API keys, **do not upload**)  
- `feedback_data.csv` → Sample feedback data  
- `requirements.txt` → Python dependencies  

---

## Setup & Run

**Step 1: Clone the repository**

```bash
git clone https://github.com/nathasha-nethmini/steamnoodles-feedback-agent-nathasha-nethmini.git
cd steamnoodles-feedback-agent-nathasha-nethmini
```
**Step 2: Install dependencies**

```bash 
pip install -r requirements.txt
```

**Step 3: Add your API key**
```bash
GROQ_API_KEY=your_api_key_here
```

**Step 4: Run the app**

```bash
python agent.py
```
**Step 5: Open in your browser**
Feedback page: http://127.0.0.1:5000/
Sentiment graph page: http://127.0.0.1:5000/graph-page

## Usage

Submit feedback on the feedback page to receive an automated reply.

View sentiment trends over a date range on the graph page (e.g., last 7 days or 2025-08-01 to 2025-08-07).