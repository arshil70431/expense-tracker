"""
Personal Expense Tracker Application
-------------------------------------
Backend: Flask (Python web framework)
Database: SQLite (SQL database, accessed via raw SQL through sqlite3)
Features: manual expense entry, notification-based daily reminders,
category-wise summaries, monthly filtering, edit/delete records,
shop/store tracking with weekly totals.

Author: Arshil Tamboli
"""

import os
import sqlite3
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-this")

DB_PATH = "expenses.db"

CATEGORIES = [
    "Food", "Transport", "Rent", "Utilities", "Shopping",
    "Entertainment", "Health", "Education", "Other"
]

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """
    Initializes the database schema.
    - Creates 'shops' table if not exists.
    - Creates 'expenses' table with shop_id column if not exists.
    - If 'expenses' already exists but lacks shop_id, adds the column.
    """
    conn = get_db()
    
    # Create shops table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shops (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            created_at  TEXT NOT NULL
        )
    """)
    
    # Create expenses table (with shop_id column) – if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            entry_date  TEXT    NOT NULL,
            created_at  TEXT    NOT NULL,
            shop_id     INTEGER REFERENCES shops(id) ON DELETE SET NULL
        )
    """)
    
    # If the expenses table existed before but without shop_id, add it now
    cursor = conn.execute("PRAGMA table_info(expenses)")
    columns = [col[1] for col in cursor.fetchall()]
    if "shop_id" not in columns:
        conn.execute("ALTER TABLE expenses ADD COLUMN shop_id INTEGER REFERENCES shops(id) ON DELETE SET NULL")
    
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    conn = get_db()
    month_filter = request.args.get("month", date.today().strftime("%Y-%m"))
    category_filter = request.args.get("category", "All")

    # Expenses query
    query = "SELECT * FROM expenses WHERE entry_date LIKE ?"
    params = [f"{month_filter}%"]
    if category_filter != "All":
        query += " AND category = ?"
        params.append(category_filter)
    query += " ORDER BY entry_date DESC, id DESC"
    expenses = conn.execute(query, params).fetchall()

    total = sum(e["amount"] for e in expenses)

    # Category totals
    category_totals = conn.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE entry_date LIKE ?
        GROUP BY category
        ORDER BY total DESC
    """, [f"{month_filter}%"]).fetchall()

    # Last entry date (for notifications)
    last_entry = conn.execute(
        "SELECT entry_date FROM expenses ORDER BY entry_date DESC LIMIT 1"
    ).fetchone()

    # Shop summary for the selected month
    shops_summary = conn.execute("""
        SELECT s.id, s.name, COUNT(e.id) as count, COALESCE(SUM(e.amount), 0) as total
        FROM shops s
        LEFT JOIN expenses e ON e.shop_id = s.id AND e.entry_date LIKE ?
        GROUP BY s.id, s.name
        ORDER BY total DESC, s.name
    """, [f"{month_filter}%"]).fetchall()

    conn.close()

    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        category_totals=category_totals,
        categories=CATEGORIES,
        month_filter=month_filter,
        category_filter=category_filter,
        today=date.today().isoformat(),
        last_entry_date=last_entry["entry_date"] if last_entry else None,
        shops_summary=shops_summary
    )

@app.route("/add", methods=["GET", "POST"])
def add_expense():
    conn = get_db()
    shops = conn.execute("SELECT id, name FROM shops ORDER BY name").fetchall()
    conn.close()

    if request.method == "POST":
        description = request.form.get("description", "").strip()
        category = request.form.get("category")
        amount = request.form.get("amount")
        entry_date = request.form.get("entry_date") or date.today().isoformat()
        shop_id = request.form.get("shop_id")
        new_shop_name = request.form.get("new_shop_name", "").strip()

        # Handle new shop creation
        if new_shop_name:
            conn = get_db()
            existing = conn.execute("SELECT id FROM shops WHERE name = ?", (new_shop_name,)).fetchone()
            if existing:
                shop_id = existing["id"]
            else:
                cursor = conn.execute(
                    "INSERT INTO shops (name, created_at) VALUES (?, ?)",
                    (new_shop_name, datetime.now().isoformat())
                )
                shop_id = cursor.lastrowid
            conn.commit()
            conn.close()
        else:
            if shop_id == "":
                shop_id = None
            else:
                shop_id = int(shop_id)

        # Validation
        error = None
        try:
            amount = float(amount)
            if amount <= 0:
                error = "Amount must be greater than zero."
        except (TypeError, ValueError):
            error = "Please enter a valid numeric amount."

        if not description:
            error = "Description is required."
        if category not in CATEGORIES:
            error = "Please select a valid category."

        if error:
            flash(error, "error")
            conn = get_db()
            shops = conn.execute("SELECT id, name FROM shops ORDER BY name").fetchall()
            conn.close()
            return render_template("add.html", categories=CATEGORIES,
                                    today=date.today().isoformat(), form=request.form, shops=shops)

        conn = get_db()
        conn.execute(
            "INSERT INTO expenses (description, category, amount, entry_date, created_at, shop_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (description, category, amount, entry_date, datetime.now().isoformat(), shop_id)
        )
        conn.commit()
        conn.close()

        flash("Expense added successfully.", "success")
        return redirect(url_for("index"))

    # GET request
    return render_template("add.html", categories=CATEGORIES, today=date.today().isoformat(), form={}, shops=shops)

@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    conn = get_db()
    expense = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if expense is None:
        conn.close()
        flash("Expense not found.", "error")
        return redirect(url_for("index"))

    shops = conn.execute("SELECT id, name FROM shops ORDER BY name").fetchall()
    conn.close()

    if request.method == "POST":
        description = request.form.get("description", "").strip()
        category = request.form.get("category")
        amount = request.form.get("amount")
        entry_date = request.form.get("entry_date")
        shop_id = request.form.get("shop_id")
        new_shop_name = request.form.get("new_shop_name", "").strip()

        # Handle new shop creation
        conn = get_db()
        if new_shop_name:
            existing = conn.execute("SELECT id FROM shops WHERE name = ?", (new_shop_name,)).fetchone()
            if existing:
                shop_id = existing["id"]
            else:
                cursor = conn.execute(
                    "INSERT INTO shops (name, created_at) VALUES (?, ?)",
                    (new_shop_name, datetime.now().isoformat())
                )
                shop_id = cursor.lastrowid
        else:
            if shop_id == "":
                shop_id = None
            else:
                shop_id = int(shop_id)

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            amount = expense["amount"]

        conn.execute(
            "UPDATE expenses SET description=?, category=?, amount=?, entry_date=?, shop_id=? WHERE id=?",
            (description, category, amount, entry_date, shop_id, expense_id)
        )
        conn.commit()
        conn.close()
        flash("Expense updated.", "success")
        return redirect(url_for("index"))

    return render_template("edit.html", expense=expense, categories=CATEGORIES, shops=shops)

@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    flash("Expense deleted.", "success")
    return redirect(url_for("index"))

# -----------------------------------------------------------
# API endpoints
# -----------------------------------------------------------

@app.route("/api/reminder-status")
def reminder_status():
    conn = get_db()
    today = date.today().isoformat()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM expenses WHERE entry_date = ?", (today,)
    ).fetchone()
    conn.close()
    return jsonify({"logged_today": row["cnt"] > 0, "date": today})

@app.route("/api/summary")
def api_summary():
    conn = get_db()
    month_filter = request.args.get("month", date.today().strftime("%Y-%m"))
    rows = conn.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE entry_date LIKE ?
        GROUP BY category
        ORDER BY total DESC
    """, [f"{month_filter}%"]).fetchall()
    conn.close()
    return jsonify([{"category": r["category"], "total": r["total"]} for r in rows])

@app.route("/api/quick-add", methods=["POST"])
def api_quick_add():
    import json
    data = request.get_json()
    category = data.get("category")
    amount = data.get("amount")
    description = data.get("description", f"Quick {category}")

    if category not in CATEGORIES:
        return jsonify({"success": False, "error": "Invalid category"}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({"success": False, "error": "Amount must be > 0"}), 400
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid amount"}), 400

    today = date.today().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (description, category, amount, entry_date, created_at) VALUES (?, ?, ?, ?, ?)",
        (description, category, amount, today, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Added {category} for ₹{amount:.2f}"})

@app.route("/export")
def export_csv():
    import csv
    from io import StringIO

    month_filter = request.args.get("month", date.today().strftime("%Y-%m"))
    category_filter = request.args.get("category", "All")

    conn = get_db()
    query = "SELECT * FROM expenses WHERE entry_date LIKE ?"
    params = [f"{month_filter}%"]
    if category_filter != "All":
        query += " AND category = ?"
        params.append(category_filter)
    query += " ORDER BY entry_date DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "Description", "Category", "Amount", "Entry Date", "Created At", "Shop ID"])
    for r in rows:
        writer.writerow([r["id"], r["description"], r["category"], r["amount"], r["entry_date"], r["created_at"], r["shop_id"]])
    output = si.getvalue()
    return output, 200, {
        "Content-Type": "text/csv",
        "Content-Disposition": f'attachment; filename="expenses_{month_filter}.csv"'
    }

@app.route("/shop/<int:shop_id>")
def shop_detail(shop_id):
    conn = get_db()
    shop = conn.execute("SELECT * FROM shops WHERE id = ?", (shop_id,)).fetchone()
    if not shop:
        conn.close()
        flash("Shop not found.", "error")
        return redirect(url_for("index"))

    expenses = conn.execute("""
        SELECT * FROM expenses
        WHERE shop_id = ?
        ORDER BY entry_date DESC, id DESC
    """, (shop_id,)).fetchall()

    weekly_totals = conn.execute("""
        SELECT 
            strftime('%Y-%W', entry_date) as week,
            MIN(entry_date) as week_start,
            SUM(amount) as total
        FROM expenses
        WHERE shop_id = ?
        GROUP BY week
        ORDER BY week DESC
    """, (shop_id,)).fetchall()

    conn.close()
    return render_template("shop_detail.html", shop=shop, expenses=expenses, weekly_totals=weekly_totals)

if __name__ == "__main__":
    init_db()
   # app.run(debug=True)
    app.run(host='0.0.0.0', debug=False)