# Personal Expense Tracker

A personal finance web app built with **Flask** (Python backend routing/logic)
and a **SQLite** SQL database for recording, managing, and querying daily
expense data — matching the project description on Arshil Tamboli's resume.

## Features

- **Manual expense entry** — add expenses with description, category, amount, and date.
- **Notification-based reminders** — browser notifications remind you to log
  today's expenses if you haven't yet (uses the Notification API + a
  `/api/reminder-status` endpoint backed by a SQL query).
- **SQL-backed dashboard** — monthly totals, category breakdown (doughnut chart),
  and filtering by month/category, all powered by raw SQL queries against SQLite.
- **Edit / delete** expenses.
- Clean, responsive UI — no external framework required beyond Chart.js (loaded via CDN).

## Tech Stack

| Layer      | Technology            |
|------------|------------------------|
| Backend    | Python, Flask          |
| Database   | SQLite (SQL)           |
| Frontend   | HTML, CSS, vanilla JS, Chart.js |
| Notifications | Browser Notification API |

## Project Structure

```
expense_tracker/
├── app.py                 # Flask app: routes, SQL queries, API endpoints
├── requirements.txt
├── templates/
│   ├── base.html           # Layout, nav, notification button
│   ├── index.html          # Dashboard: totals, chart, expense table
│   ├── add.html             # Add-expense form
│   └── edit.html            # Edit-expense form
└── static/
    ├── style.css
    └── script.js            # Notification reminder logic
```

## Setup & Run

1. **Install dependencies** (Python 3.9+ recommended):
   ```bash
   cd expense_tracker
   python -m venv venv
   source venv/bin/activate      # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the app**:
   ```bash
   python app.py
   ```
   The SQLite database (`expenses.db`) is created automatically on first run.

3. Open your browser at **http://127.0.0.1:5000**

4. Click **"Enable Reminders"** in the top bar and allow notifications to get
   a browser reminder if you haven't logged an expense yet today.

## Database Schema

```sql
CREATE TABLE expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT    NOT NULL,
    category    TEXT    NOT NULL,
    amount      REAL    NOT NULL,
    entry_date  TEXT    NOT NULL,
    created_at  TEXT    NOT NULL
);
```

## Possible Extensions

- Switch to Flask-SQLAlchemy / migrate to Django (as mentioned on the resume)
  for a larger-scale version.
- Add user accounts/authentication for multi-user support.
- Export monthly reports as PDF/CSV.
- Add budget limits per category with over-budget notifications.
- Deploy with PostgreSQL for production use.

## Author

Arshil Tamboli — Computer Science undergraduate, backend web development
and database architecture focus.
