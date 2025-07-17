# Whoppah GEO Monitor

A production-ready Streamlit application that tracks how frequently the brands **Whoppah** and **Chairish** are mentioned by GPT-4 Turbo across a set of strategic queries. The app stores daily results in SQLite, visualises mention trends and sentiment, and allows on-demand execution.

---

## Features

* **Automated monitoring** – Scheduled at **09:00 Europe/Amsterdam** every day via APScheduler.
* **Manual trigger** – Run the same job instantly from the UI.
* **SQLite storage** – Results (timestamp, query, mentions, sentiment, excerpt) are persisted locally.
* **Interactive dashboard** – Plotly charts for brand mentions over time and sentiment breakdown, plus the latest excerpts.
* **Modular code** – Separate modules for data access, scheduling/LLM integration, and UI.

---

## Installation

1. **Clone the repository**

```bash
$ git clone <your-repo-url>
$ cd "GEO analyser"   # adapt if your folder name differs
```

2. **Create a virtual environment & install dependencies**

```bash
$ python -m venv .venv
$ source .venv/bin/activate  # Windows: .venv\Scripts\activate
$ pip install -r requirements.txt
```

3. **Configure your OpenAI API key**

   The application now uses a `.env` file to store your API key securely.
   
   **Option A: Use the .env file (recommended)**
   ```bash
   # Edit the .env file and replace the placeholder with your actual key
   # File: .env
   OPENAI_API_KEY=your-actual-openai-api-key-here
   ```
   
   **Option B: Set environment variable (alternative)**
   ```bash
   $ export OPENAI_API_KEY="sk-…"  # obtain from https://platform.openai.com/
   ```

---

## Running the application

```bash
$ streamlit run app.py
```

The dashboard will automatically open in your default browser. The first launch creates **`whoppah_geo.db`** next to the code.

---

## 🚀 Deployment Options

### **Local Development**
- Use the `.env` file (recommended for local development)
- Copy `.env.template` to `.env` and add your API key

### **Production/Cloud Deployment**
- Set `OPENAI_API_KEY` as an environment variable
- **Heroku**: `heroku config:set OPENAI_API_KEY=your-key`
- **Railway**: Add in Environment Variables section
- **Streamlit Cloud**: Add in Secrets management
- **Docker**: Use `docker run -e OPENAI_API_KEY=your-key`

### **GitHub Actions/CI**
- Add `OPENAI_API_KEY` as a repository secret
- Access via `${{ secrets.OPENAI_API_KEY }}`

---

## Customisation

* **Queries** – Edit the `QUERIES` list in `schedule.py`.
* **Schedule time** – Adjust the `CronTrigger` in `schedule.py`.
* **Superlatives / sentiment logic** – Tweak `SUPERLATIVES` or the `analyze_response` function in `schedule.py`.

---

## File structure

```
app.py         # Streamlit entrypoint
schedule.py    # Scheduler & OpenAI integration
data.py        # Database models and helpers
ui.py          # Chart / table rendering helpers
requirements.txt
README.md
```

---

### License

MIT – see `LICENSE` (not included by default). 