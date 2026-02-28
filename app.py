from flask import Flask, render_template, request, redirect, Response, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import webbrowser
import threading
import os
from datetime import datetime, date
from functools import wraps

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret-key-before-deploying"  # FIX: Added secret key for sessions

DB_NAME = "jewellery.db"

# ---------- DATABASE SETUP ----------
# FIX: Moved DB init into a function instead of running at module level
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ITEM TEXT NOT NULL,
            MATERIAL TEXT NOT NULL,
            CATEGORY TEXT NOT NULL,
            WEIGHT REAL NOT NULL,
            PURITY REAL NOT NULL,
            PURCHASE_DATE TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchase (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ITEM TEXT NOT NULL,
            MATERIAL TEXT NOT NULL,
            CATEGORY TEXT NOT NULL,
            WEIGHT REAL NOT NULL,
            PURITY REAL NOT NULL,
            SELLER TEXT NOT NULL,
            PHONE TEXT NOT NULL,
            PURCHASE_DATE TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sale (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ITEM TEXT NOT NULL,
            MATERIAL TEXT NOT NULL,
            CATEGORY TEXT NOT NULL,
            WEIGHT REAL NOT NULL,
            PURITY REAL NOT NULL,
            BUYER TEXT NOT NULL,
            PHONE TEXT NOT NULL,
            SALE_DATE TEXT NOT NULL
        )
    """)
    # FIX: Added users table for authentication
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            USERNAME TEXT NOT NULL UNIQUE,
            PASSWORD TEXT NOT NULL
        )
    """)
    # Insert a default admin user (password: admin123) — CHANGE THIS IMMEDIATELY
    hashed_password = generate_password_hash('admin123')
    cur.execute(
        "INSERT OR IGNORE INTO users (USERNAME, PASSWORD) VALUES (?, ?)",
        ('admin', hashed_password)
    )
    conn.commit()
    conn.close()

# ---------- DATABASE HELPER ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- AUTH DECORATOR ----------
# FIX: Added login_required so every route is protected
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE USERNAME=?",
            (username,)
        ).fetchone()
        conn.close()
        if user and check_password_hash(user["PASSWORD"], password):
            session["logged_in"] = True
            session["username"] = username
            return redirect("/")
        else:
            error = "Invalid username or password"
    return render_template("login.html", error=error)
@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect("/login")

# ---------- DASHBOARD ----------
@app.route("/")
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor()
    gold = cur.execute(
        "SELECT IFNULL(SUM(WEIGHT),0) FROM stock WHERE MATERIAL='GOLD'"
    ).fetchone()[0]
    silver = cur.execute(
        "SELECT IFNULL(SUM(WEIGHT),0) FROM stock WHERE MATERIAL='SILVER'"
    ).fetchone()[0]
    diamond = cur.execute(
        "SELECT COUNT(*) FROM stock WHERE MATERIAL='DIAMOND'"
    ).fetchone()[0]
    conn.close()
    return render_template(
        "dashboard.html",
        gold_weight=gold,
        silver_weight=silver,
        diamond_count=diamond
    )

# ---------- VIEW STOCK ----------
@app.route("/view_stock")
@login_required
def view_stock():
    conn = get_db()
    cur = conn.cursor()
    stock = cur.execute("""
        SELECT ID, ITEM, MATERIAL, CATEGORY, WEIGHT, PURITY, PURCHASE_DATE
        FROM stock
    """).fetchall()
    conn.close()
    return render_template("view_stock.html", stock=stock)

# ---------- ADD PURCHASE ----------
@app.route("/add_purchase", methods=["GET", "POST"])
@login_required
def add_purchase():
    error = None
    if request.method == "POST":
        # FIX: Wrapped in try/except to handle bad float input instead of crashing
        try:
            item     = request.form["item"].strip()
            material = request.form["material"].strip()
            category = request.form["category"].strip()
            weight   = float(request.form["weight"])
            purity   = float(request.form["purity"])
            seller   = request.form["seller"].strip()
            phone    = request.form["phone"].strip()
        except (ValueError, KeyError):
            error = "Invalid input. Please check all fields and enter valid numbers."
            return render_template("add_purchase.html", error=error)

        # FIX: Validate weight and purity are positive numbers
        if weight <= 0 or purity <= 0:
            error = "Weight and Purity must be positive numbers."
            return render_template("add_purchase.html", error=error)

        if not phone.isdigit() or len(phone) != 10:
            error = "Phone number must be exactly 10 digits."
            return render_template("add_purchase.html", error=error)

        if not item or not material or not category or not seller:
            error = "All fields are required."
            return render_template("add_purchase.html", error=error)

        purchase_date = datetime.now().strftime("%Y-%m-%d")
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO stock VALUES (NULL,?,?,?,?,?,?)",
            (item, material, category, weight, purity, purchase_date)
        )
        cur.execute(
            "INSERT INTO purchase VALUES (NULL,?,?,?,?,?,?,?,?)",
            (item, material, category, weight, purity, seller, phone, purchase_date)
        )
        conn.commit()
        conn.close()
        return redirect("/view_stock")
    return render_template("add_purchase.html", error=error)

# ---------- RECORD SALE ----------
@app.route("/record_sale", methods=["GET", "POST"])
@login_required
def record_sale():
    message = None
    if request.method == "POST":
        # FIX: Validate stock_id is actually an integer before querying
        try:
            stock_id = int(request.form["stock_id"])
        except (ValueError, KeyError):
            message = "Invalid Stock ID."
            return render_template("record_sale.html", message=message)

        buyer = request.form.get("buyer", "").strip()
        phone = request.form.get("phone", "").strip()

        if not phone.isdigit() or len(phone) != 10:
            message = "Phone number must be exactly 10 digits."
            return render_template("record_sale.html", message=message)

        if not buyer:
            message = "Buyer name is required."
            return render_template("record_sale.html", message=message)

        sale_date = datetime.now().strftime("%Y-%m-%d")
        conn = get_db()
        cur = conn.cursor()
        item = cur.execute(
            "SELECT * FROM stock WHERE ID=?", (stock_id,)
        ).fetchone()

        if not item:
            message = "Invalid Stock ID. No item found."
        else:
            cur.execute("""
                INSERT INTO sale
                (ITEM, MATERIAL, CATEGORY, WEIGHT, PURITY, BUYER, PHONE, SALE_DATE)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                item["ITEM"], item["MATERIAL"], item["CATEGORY"],
                item["WEIGHT"], item["PURITY"], buyer, phone, sale_date
            ))
            cur.execute("DELETE FROM stock WHERE ID=?", (stock_id,))
            conn.commit()
            message = f"Stock ID {stock_id} sold and removed from stock."
        conn.close()

    return render_template("record_sale.html", message=message)

# ---------- VIEW PURCHASES ----------
@app.route("/view_purchases")
@login_required
def view_purchases():
    conn = get_db()
    purchases = conn.execute("""
        SELECT ID, ITEM, MATERIAL, CATEGORY, WEIGHT, PURITY,
               SELLER, PHONE, PURCHASE_DATE
        FROM purchase
    """).fetchall()
    conn.close()
    return render_template("view_purchases.html", purchases=purchases)

# ---------- VIEW SALES ----------
@app.route("/view_sales")
@login_required
def view_sales():
    conn = get_db()
    sales = conn.execute("""
        SELECT ITEM, MATERIAL, CATEGORY, WEIGHT, PURITY,
               BUYER, PHONE, SALE_DATE
        FROM sale
    """).fetchall()
    conn.close()
    return render_template("view_sales.html", sales=sales)

# ---------- REPORTS ----------
# FIX: Removed f-string SQL injection risk by using a lookup dict for safe query selection
@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    conn = get_db()
    today = date.today().strftime("%Y-%m-%d")
    report_type = request.form.get("type", "daily")

    REPORT_QUERIES = {
        "daily": {
            "purchase": ("SELECT ITEM, MATERIAL, CATEGORY, WEIGHT, SELLER, PURCHASE_DATE FROM purchase WHERE PURCHASE_DATE=?", (today,)),
            "sale":     ("SELECT ITEM, MATERIAL, CATEGORY, WEIGHT, BUYER, SALE_DATE FROM sale WHERE SALE_DATE=?", (today,)),
        },
        "monthly": {
            "purchase": ("SELECT ITEM, MATERIAL, CATEGORY, WEIGHT, SELLER, PURCHASE_DATE FROM purchase WHERE strftime('%Y-%m', PURCHASE_DATE)=strftime('%Y-%m','now')", ()),
            "sale":     ("SELECT ITEM, MATERIAL, CATEGORY, WEIGHT, BUYER, SALE_DATE FROM sale WHERE strftime('%Y-%m', SALE_DATE)=strftime('%Y-%m','now')", ()),
        },
        "yearly": {
            "purchase": ("SELECT ITEM, MATERIAL, CATEGORY, WEIGHT, SELLER, PURCHASE_DATE FROM purchase WHERE strftime('%Y', PURCHASE_DATE)=strftime('%Y','now')", ()),
            "sale":     ("SELECT ITEM, MATERIAL, CATEGORY, WEIGHT, BUYER, SALE_DATE FROM sale WHERE strftime('%Y', SALE_DATE)=strftime('%Y','now')", ()),
        },
    }

    # FIX: Default to daily if someone sends a garbage report_type value
    if report_type not in REPORT_QUERIES:
        report_type = "daily"

    queries = REPORT_QUERIES[report_type]
    purchase = conn.execute(*queries["purchase"]).fetchall()
    sales    = conn.execute(*queries["sale"]).fetchall()
    conn.close()

    return render_template(
        "report.html",
        purchase=purchase,
        sales=sales,
        report_type=report_type
    )

# ---------- EXPORT STOCK ----------
@app.route("/export_stock")
@login_required
def export_stock():
    conn = get_db()
    rows = conn.execute("""
        SELECT ID, ITEM, MATERIAL, CATEGORY, WEIGHT, PURITY, PURCHASE_DATE
        FROM stock
    """).fetchall()
    conn.close()

    def generate():
        yield "ID,Item,Material,Category,Weight,Purity,Purchase Date\n"
        for r in rows:
            # FIX: Wrap fields in quotes to handle commas in item names
            yield (
                f"{r['ID']},"
                f"\"{r['ITEM']}\","
                f"\"{r['MATERIAL']}\","
                f"\"{r['CATEGORY']}\","
                f"{r['WEIGHT']},"
                f"{r['PURITY']},"
                f"{r['PURCHASE_DATE']}\n"
            )

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=stock_report.csv"}
    )

# ---------- EXPORT REPORT ----------
@app.route("/export_report/<report_type>")
@login_required
def export_report(report_type):
    conn = get_db()
    today = date.today().strftime("%Y-%m-%d")

    EXPORT_QUERIES = {
        "daily": {
            "purchase": ("SELECT ITEM, MATERIAL, CATEGORY, WEIGHT, SELLER, PHONE, PURCHASE_DATE FROM purchase WHERE PURCHASE_DATE=?", (today,)),
            "sale":     ("SELECT ITEM, MATERIAL, CATEGORY, WEIGHT, BUYER, PHONE, SALE_DATE FROM sale WHERE SALE_DATE=?", (today,)),
        },
        "monthly": {
            "purchase": ("SELECT ITEM, MATERIAL, CATEGORY, WEIGHT, SELLER, PHONE, PURCHASE_DATE FROM purchase WHERE strftime('%Y-%m', PURCHASE_DATE)=strftime('%Y-%m','now')", ()),
            "sale":     ("SELECT ITEM, MATERIAL, CATEGORY, WEIGHT, BUYER, PHONE, SALE_DATE FROM sale WHERE strftime('%Y-%m', SALE_DATE)=strftime('%Y-%m','now')", ()),
        },
        "yearly": {
            "purchase": ("SELECT ITEM, MATERIAL, CATEGORY, WEIGHT, SELLER, PHONE, PURCHASE_DATE FROM purchase WHERE strftime('%Y', PURCHASE_DATE)=strftime('%Y','now')", ()),
            "sale":     ("SELECT ITEM, MATERIAL, CATEGORY, WEIGHT, BUYER, PHONE, SALE_DATE FROM sale WHERE strftime('%Y', SALE_DATE)=strftime('%Y','now')", ()),
        },
    }

    # FIX: Reject invalid report_type values — don't process garbage input
    if report_type not in EXPORT_QUERIES:
        return "Invalid report type.", 400

    queries  = EXPORT_QUERIES[report_type]
    purchase = conn.execute(*queries["purchase"]).fetchall()
    sales    = conn.execute(*queries["sale"]).fetchall()
    conn.close()

    def generate():
        yield "PURCHASE REPORT\n"
        yield "Item,Material,Category,Weight,Seller,Phone,Date\n"
        for p in purchase:
            yield f"\"{p['ITEM']}\",\"{p['MATERIAL']}\",\"{p['CATEGORY']}\",{p['WEIGHT']},\"{p['SELLER']}\",{p['PHONE']},{p['PURCHASE_DATE']}\n"
        yield "\nSALES REPORT\n"
        yield "Item,Material,Category,Weight,Buyer,Phone,Date\n"
        for s in sales:
            yield f"\"{s['ITEM']}\",\"{s['MATERIAL']}\",\"{s['CATEGORY']}\",{s['WEIGHT']},\"{s['BUYER']}\",{s['PHONE']},{s['SALE_DATE']}\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_type}_report.csv"}
    )

# ---------- SEARCH ----------
@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    results = []
    if request.method == "POST":
        column = request.form.get("column", "").strip()
        value  = request.form.get("value", "").strip()

        allowed_columns = {
            "ID":            "ID",
            "ITEM":          "ITEM",
            "MATERIAL":      "MATERIAL",
            "CATEGORY":      "CATEGORY",
            "PURITY":        "PURITY",
            "PURCHASE_DATE": "PURCHASE_DATE"
        }

        if column in allowed_columns:
            conn = get_db()
            if column in ["ID", "PURITY", "PURCHASE_DATE"]:
                # FIX: exact match for numeric/date fields
                results = conn.execute(f"""
                    SELECT ID, ITEM, MATERIAL, CATEGORY, WEIGHT, PURITY, PURCHASE_DATE
                    FROM stock WHERE {allowed_columns[column]} = ?
                """, (value,)).fetchall()
            else:
                results = conn.execute(f"""
                    SELECT ID, ITEM, MATERIAL, CATEGORY, WEIGHT, PURITY, PURCHASE_DATE
                    FROM stock WHERE LOWER({allowed_columns[column]}) LIKE ?
                """, (f"%{value.lower()}%",)).fetchall()
            conn.close()

    return render_template("search.html", results=results)

# ---------- SHUTDOWN ----------
# FIX: Removed unauthenticated /shutdown endpoint — was a huge security hole.
# The app can simply be stopped with Ctrl+C in the terminal.

# ---------- OPEN BROWSER ----------
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")
@app.after_request
#----------- cache ----------
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
# ---------- MAIN ----------
if __name__ == "__main__":
    init_db()  # FIX: Proper DB init only when app starts, not at import time
    threading.Timer(1.2, open_browser).start()
    try:
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass
