# 💰 Personal Expense Tracker

A full‑featured personal finance web app built with **Flask** (Python) and **SQLite**.  
It helps you track daily expenses, manage monthly budgets, and visualize spending habits — all with a clean, responsive interface that supports **light/dark mode**.

---

## ✨ Features

- **User authentication** – Sign up and log in (auto‑login after signup).
- **Expense CRUD** – Add, edit, and delete expenses with description, category, amount, date, and optional store/shop.
- **Monthly budget** – Set a monthly budget and see remaining amount at a glance.
- **Interactive charts** – Category breakdown (doughnut chart) and daily spending trend (bar chart) using Chart.js.
- **Shop/Store tracking** – Attach expenses to shops and view per‑shop summaries and weekly totals.
- **Quick‑add** – One‑click buttons to add common expenses (Food, Transport, etc.).
- **CSV export** – Download expense data for any month/category filter.
- **Daily reminders** – Browser notifications remind you to log expenses if you haven't for the day.
- **Dark / Light mode** – Toggle themes; your preference is saved in the browser.
- **Fully responsive** – Works on desktop, tablet, and mobile.

---

## 🧰 Tech Stack

| Layer          | Technology                          |
|----------------|--------------------------------------|
| Backend        | Python, Flask, Flask‑Login           |
| Database       | SQLite (raw SQL via `sqlite3`)       |
| Authentication | Werkzeug (password hashing)          |
| Frontend       | HTML, CSS, vanilla JS, Bootstrap 5   |
| Charts         | Chart.js (CDN)                       |
| Notifications  | Browser Notification API             |
| Environment    | python‑dotenv                        |

---

## 📁 Project Structure

expense_tracker/
├── app.py # Flask app: routes, SQL queries, API endpoints
├── requirements.txt # Python dependencies
├── .env # Environment variables (SECRET_KEY)
├── expenses.db # SQLite database (auto‑created)
├── templates/
│ ├── base.html # Layout, navbar, dark mode toggle, Chart.js
│ ├── index.html # Dashboard (totals, charts, expense table, shops)
│ ├── add.html # Add expense form
│ ├── edit.html # Edit expense form
│ ├── login.html # Login page
│ ├── signup.html # Signup page (auto‑login after signup)
│ └── shop_detail.html # Per‑shop expense history + weekly totals
└── static/
├── style.css # Light/dark theme, KPI cards, responsive styles
└── script.js # Dark mode toggle, budget, reminders, quick‑add


---

## 🗄️ Database Schema

```sql
-- Users table
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

-- Shops table
CREATE TABLE shops (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE
);

-- Expenses table
CREATE TABLE expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT    NOT NULL,
    category    TEXT    NOT NULL,
    amount      REAL    NOT NULL,
    entry_date  TEXT    NOT NULL,
    created_at  TEXT    NOT NULL,
    shop_id     INTEGER REFERENCES shops(id) ON DELETE SET NULL,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE
);

Setup & Run
Clone the repository:

bash
git clone https://github.com/yourusername/expense_tracker.git
cd expense_tracker
Create and activate a virtual environment:

bash
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
Install dependencies:

bash
pip install -r requirements.txt
Create a .env file (optional – a default secret is used if missing):

text
SECRET_KEY=your-secret-key-here
Run the app:

bash
python app.py
Open your browser at http://127.0.0.1:5000 and sign up – you’ll be automatically logged in.

