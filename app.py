
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "food_waste_project_key"

DATABASE = "food_waste.db"


# Connect to database
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create database table
def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS waste_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity REAL NOT NULL,
            source TEXT NOT NULL,
            reason TEXT NOT NULL,
            record_date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# Generate recommendations
def get_recommendations(records):
    suggestions = []

    for record in records:
        if record["reason"] == "Overproduction":
            suggestions.append(
                "Improve food quantity planning to prevent overproduction."
            )
        elif record["reason"] == "Spoilage":
            suggestions.append(
                "Improve food storage and monitor expiry dates."
            )
        elif record["reason"] == "Leftovers":
            suggestions.append(
                "Review portion sizes and encourage responsible serving."
            )

    return list(dict.fromkeys(suggestions))


# Main dashboard
@app.route("/")
def dashboard():
    conn = get_db()

    records = conn.execute(
        "SELECT * FROM waste_records ORDER BY id DESC"
    ).fetchall()

    total = conn.execute(
        "SELECT COALESCE(SUM(quantity), 0) FROM waste_records"
    ).fetchone()[0]

    count = len(records)

    categories = conn.execute("""
        SELECT category, SUM(quantity) AS total
        FROM waste_records
        GROUP BY category
    """).fetchall()

    recommendations = get_recommendations(records)

    conn.close()

    return render_template(
        "index.html",
        records=records,
        total=round(total, 2),
        count=count,
        categories=categories,
        recommendations=recommendations,
        today=date.today().isoformat()
    )


# Add food waste record
@app.route("/add", methods=["POST"])
def add_record():
    food_name = request.form.get("food_name", "").strip()
    category = request.form.get("category", "")
    quantity = request.form.get("quantity", "")
    source = request.form.get("source", "")
    reason = request.form.get("reason", "")

    if not all([food_name, category, quantity, source, reason]):
        flash("Please fill in all fields.")
        return redirect(url_for("dashboard"))

    try:
        quantity = float(quantity)
        if quantity <= 0:
            raise ValueError
    except ValueError:
        flash("Please enter a valid quantity greater than zero.")
        return redirect(url_for("dashboard"))

    conn = get_db()
    conn.execute("""
        INSERT INTO waste_records
        (food_name, category, quantity, source, reason, record_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (food_name, category, quantity, source, reason, date.today().isoformat()))

    conn.commit()
    conn.close()

    flash("Food waste record added successfully!")
    return redirect(url_for("dashboard"))


# Delete a record
@app.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM waste_records WHERE id = ?",
        (record_id,)
    )
    conn.commit()
    conn.close()

    flash("Record deleted successfully!")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
