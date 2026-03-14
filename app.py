from flask import Flask, render_template, request, redirect, Response, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from functools import wraps
from invoice_generator import generate_invoice
import sqlite3
import os
import csv
import io
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-dev-only")

DB_NAME = "jewellery.db"


# ---------- NO CACHE ----------
@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ---------- DATABASE SETUP ----------
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            USERNAME TEXT NOT NULL UNIQUE,
            PASSWORD TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoice_data (
            SALE_ID INTEGER PRIMARY KEY,
            BUYER_NAME TEXT NOT NULL,
            BUYER_PHONE TEXT NOT NULL,
            BUYER_STATE TEXT NOT NULL,
            BUYER_GSTIN TEXT,
            PAYMENT_METHOD TEXT NOT NULL,
            SALE_DATE TEXT NOT NULL,
            ITEMS_JSON TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            SALE_ID INTEGER NOT NULL,
            BUYER_NAME TEXT NOT NULL,
            BUYER_PHONE TEXT NOT NULL,
            TOTAL_AMOUNT REAL NOT NULL,
            PAID_AMOUNT REAL NOT NULL,
            DUE_AMOUNT REAL NOT NULL,
            SALE_DATE TEXT NOT NULL,
            LAST_PAYMENT_DATE TEXT NOT NULL,
            STATUS TEXT NOT NULL DEFAULT 'Pending'
        )
    """)
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


# ---------- LOGOUT ----------
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
@app.route("/record_sale")
@login_required
def record_sale():
    cart_items = session.get("cart", [])
    total = round(sum(
        (i["weight"] * i["rate_per_gram"]) + i["making_charges"]
        for i in cart_items
    ), 2)
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("record_sale.html", cart=cart_items, total=total, today=today)


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
        SELECT s.ID, s.ITEM, s.MATERIAL, s.CATEGORY, s.WEIGHT, s.PURITY,
               s.BUYER, s.PHONE, s.SALE_DATE,
               CASE WHEN i.SALE_ID IS NOT NULL THEN 1 ELSE 0 END as HAS_INVOICE
        FROM sale s
        LEFT JOIN invoice_data i ON s.ID = i.SALE_ID
    """).fetchall()
    conn.close()
    return render_template("view_sales.html", sales=sales)


# ---------- REPORTS ----------
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

    if report_type not in REPORT_QUERIES:
        report_type = "daily"

    queries  = REPORT_QUERIES[report_type]
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


# ---------- EXPORT DATA PAGE ----------
@app.route("/export_data")
@login_required
def export_data():
    return render_template("export_data.html")


# ---------- EXPORT TABLE ----------
@app.route("/export/<table_name>")
@login_required
def export_table(table_name):
    allowed = {
        "stock":    ("stock",    ["ID", "ITEM", "MATERIAL", "CATEGORY", "WEIGHT", "PURITY", "PURCHASE_DATE"]),
        "purchase": ("purchase", ["ID", "ITEM", "MATERIAL", "CATEGORY", "WEIGHT", "PURITY", "SELLER", "PHONE", "PURCHASE_DATE"]),
        "sale":     ("sale",     ["ID", "ITEM", "MATERIAL", "CATEGORY", "WEIGHT", "PURITY", "BUYER", "PHONE", "SALE_DATE"]),
    }

    if table_name not in allowed:
        return "Invalid table.", 400

    table, columns = allowed[table_name]
    conn = get_db()
    rows = conn.execute(f"SELECT {','.join(columns)} FROM {table}").fetchall()
    conn.close()

    def generate():
        yield ",".join(columns) + "\n"
        for row in rows:
            yield ",".join([f'"{str(row[col])}"' for col in columns]) + "\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={table_name}_export.csv"}
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


# ---------- IMPORT DATA ----------
@app.route("/import_data", methods=["GET", "POST"])
@login_required
def import_data():
    message = None
    errors  = []

    if request.method == "POST":
        import_type = request.form.get("import_type")
        file        = request.files.get("file")

        if not file or file.filename == "":
            message = "No file selected."
            return render_template("import_data.html", message=message, errors=errors)

        filename = file.filename.lower()

        try:
            rows = []
            if filename.endswith(".csv"):
                stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
                reader = csv.DictReader(stream)
                rows   = list(reader)
            elif filename.endswith((".xlsx", ".xls")):
                import openpyxl
                wb    = openpyxl.load_workbook(file)
                ws    = wb.active
                heads = [str(cell.value).strip() for cell in ws[1]]
                for row in ws.iter_rows(min_row=2, values_only=True):
                    rows.append(dict(zip(heads, row)))
            else:
                message = "Only .csv or .xlsx files are supported."
                return render_template("import_data.html", message=message, errors=errors)

        except Exception as e:
            message = f"Could not read file: {str(e)}"
            return render_template("import_data.html", message=message, errors=errors)

        conn    = get_db()
        cur     = conn.cursor()
        success = 0

        for idx, row in enumerate(rows, start=2):
            try:
                row = {k.strip().upper(): str(v).strip() if v is not None else "" for k, v in row.items()}

                if import_type == "stock":
                    cur.execute("""
                        INSERT INTO stock (ITEM, MATERIAL, CATEGORY, WEIGHT, PURITY, PURCHASE_DATE)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        row["ITEM"],
                        row["MATERIAL"].upper(),
                        row["CATEGORY"].upper(),
                        float(row["WEIGHT"]),
                        float(row["PURITY"]),
                        row.get("PURCHASE_DATE", datetime.now().strftime("%Y-%m-%d"))
                    ))

                elif import_type == "purchase":
                    cur.execute("""
                        INSERT INTO purchase (ITEM, MATERIAL, CATEGORY, WEIGHT, PURITY, SELLER, PHONE, PURCHASE_DATE)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row["ITEM"],
                        row["MATERIAL"].upper(),
                        row["CATEGORY"].upper(),
                        float(row["WEIGHT"]),
                        float(row["PURITY"]),
                        row["SELLER"],
                        row["PHONE"],
                        row.get("PURCHASE_DATE", datetime.now().strftime("%Y-%m-%d"))
                    ))

                elif import_type == "sale":
                    cur.execute("""
                        INSERT INTO sale (ITEM, MATERIAL, CATEGORY, WEIGHT, PURITY, BUYER, PHONE, SALE_DATE)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row["ITEM"],
                        row["MATERIAL"].upper(),
                        row["CATEGORY"].upper(),
                        float(row["WEIGHT"]),
                        float(row["PURITY"]),
                        row["BUYER"],
                        row["PHONE"],
                        row.get("SALE_DATE", datetime.now().strftime("%Y-%m-%d"))
                    ))

                success += 1

            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")

        conn.commit()
        conn.close()
        message = f"Successfully imported {success} records."
        if errors:
            message += f" {len(errors)} rows had errors and were skipped."

    return render_template("import_data.html", message=message, errors=errors)


# ---------- CART ----------
@app.route("/cart")
@login_required
def cart():
    cart_items = session.get("cart", [])
    total = round(sum(
        (i["weight"] * i["rate_per_gram"]) + i["making_charges"]
        for i in cart_items
    ), 2)
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("record_sale.html", cart=cart_items, total=total, today=today)


# ---------- ADD TO CART ----------
@app.route("/add_to_cart", methods=["POST"])
@login_required
def add_to_cart():
    try:
        stock_id = int(request.form["stock_id"])
    except (ValueError, KeyError):
        return redirect("/cart")

    hsn = request.form.get("hsn", "").strip()

    try:
        rate_per_gram  = float(request.form.get("rate_per_gram", 0))
        making_charges = float(request.form.get("making_charges", 0))
    except ValueError:
        return redirect("/cart")

    if not hsn or rate_per_gram <= 0:
        return redirect("/cart")

    conn = get_db()
    item = conn.execute(
        "SELECT * FROM stock WHERE ID=?", (stock_id,)
    ).fetchone()
    conn.close()

    if not item:
        return redirect("/cart")

    cart = session.get("cart", [])
    for c in cart:
        if c["stock_id"] == stock_id:
            return redirect("/cart")

    cart.append({
        "stock_id":       stock_id,
        "item":           item["ITEM"],
        "material":       item["MATERIAL"],
        "category":       item["CATEGORY"],
        "weight":         item["WEIGHT"],
        "purity":         item["PURITY"],
        "hsn":            hsn,
        "rate_per_gram":  rate_per_gram,
        "making_charges": making_charges,
        "item_total":     round((item["WEIGHT"] * rate_per_gram) + making_charges, 2)
    })
    session["cart"]  = cart
    session.modified = True
    return redirect("/cart")


# ---------- REMOVE FROM CART ----------
@app.route("/remove_from_cart/<int:stock_id>")
@login_required
def remove_from_cart(stock_id):
    cart = session.get("cart", [])
    session["cart"]  = [i for i in cart if i["stock_id"] != stock_id]
    session.modified = True
    return redirect("/cart")


# ---------- COMPLETE SALE ----------
@app.route("/complete_sale", methods=["POST"])
@login_required
def complete_sale():
    cart = session.get("cart", [])

    if not cart:
        return redirect("/cart")

    buyer          = request.form.get("buyer", "").strip()
    phone          = request.form.get("phone", "").strip()
    buyer_state    = request.form.get("buyer_state", "Gujarat").strip()
    buyer_gstin    = request.form.get("buyer_gstin", "").strip()
    payment_method = request.form.get("payment_method", "Cash").strip()
    sale_date_raw  = request.form.get("sale_date", "").strip()

    if not buyer:
        return redirect("/cart")

    if not phone.isdigit() or len(phone) != 10:
        return redirect("/cart")

    if sale_date_raw:
        try:
            sale_date_obj     = datetime.strptime(sale_date_raw, "%Y-%m-%d")
            sale_date_display = sale_date_obj.strftime("%d-%m-%Y")
            sale_date_db      = sale_date_obj.strftime("%Y-%m-%d")
        except ValueError:
            sale_date_display = datetime.now().strftime("%d-%m-%Y")
            sale_date_db      = datetime.now().strftime("%Y-%m-%d")
    else:
        sale_date_display = datetime.now().strftime("%d-%m-%Y")
        sale_date_db      = datetime.now().strftime("%Y-%m-%d")

    # Payment info
    payment_type = request.form.get("payment_type", "full").strip()
    try:
        paid_now = float(request.form.get("paid_amount", 0))
    except ValueError:
        paid_now = 0.0

    conn = get_db()
    cur  = conn.cursor()

    sale_ids = []
    for i in cart:
        cur.execute("""
            INSERT INTO sale
            (ITEM, MATERIAL, CATEGORY, WEIGHT, PURITY, BUYER, PHONE, SALE_DATE)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            i["item"], i["material"], i["category"],
            i["weight"], i["purity"], buyer, phone, sale_date_db
        ))
        sale_ids.append(cur.lastrowid)
        cur.execute("DELETE FROM stock WHERE ID=?", (i["stock_id"],))

    # Save full invoice data for reprinting
    cur.execute("""
        INSERT OR REPLACE INTO invoice_data
        (SALE_ID, BUYER_NAME, BUYER_PHONE, BUYER_STATE, BUYER_GSTIN, PAYMENT_METHOD, SALE_DATE, ITEMS_JSON)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        sale_ids[0], buyer, phone, buyer_state, buyer_gstin,
        payment_method, sale_date_display, json.dumps(cart)
    ))

    # Calculate totals for payment tracking
    taxable_amount = round(sum(i["item_total"] for i in cart), 2)
    is_gujarat = buyer_state.strip().upper() == "GUJARAT"
    if is_gujarat:
        total_amount = round(taxable_amount * 1.03, 2)
    else:
        total_amount = round(taxable_amount * 1.03, 2)

    if payment_type == "full":
        paid_amount = total_amount
    else:
        paid_amount = round(min(paid_now, total_amount), 2)

    due_amount = round(total_amount - paid_amount, 2)
    status     = "Cleared" if due_amount <= 0 else "Pending"

    cur.execute("""
        INSERT INTO payments
        (SALE_ID, BUYER_NAME, BUYER_PHONE, TOTAL_AMOUNT, PAID_AMOUNT, DUE_AMOUNT, SALE_DATE, LAST_PAYMENT_DATE, STATUS)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        sale_ids[0], buyer, phone, total_amount,
        paid_amount, due_amount, sale_date_db, sale_date_db, status
    ))

    conn.commit()
    conn.close()

    try:
        invoice_path = generate_invoice(
            sale_id        = sale_ids[0],
            buyer_name     = buyer,
            buyer_phone    = phone,
            buyer_state    = buyer_state,
            buyer_gstin    = buyer_gstin,
            payment_method = payment_method,
            sale_date      = sale_date_display,
            items          = cart
        )
        with open(invoice_path, "rb") as f:
            pdf_data = f.read()
        os.remove(invoice_path)
        session["cart"]  = []
        session.modified = True
        filename = os.path.basename(invoice_path)
        return Response(
            pdf_data,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        session["cart"]  = []
        session.modified = True
        return f"Sale recorded but invoice failed: {str(e)}"

# ---------- DUE PAYMENTS ----------
@app.route("/due_payments")
@login_required
def due_payments():
    conn = get_db()
    payments = conn.execute("""
        SELECT * FROM payments ORDER BY STATUS ASC, SALE_DATE DESC
    """).fetchall()
    conn.close()
    return render_template("due_payments.html", payments=payments)


# ---------- ADD PAYMENT ----------
@app.route("/add_payment/<int:payment_id>", methods=["POST"])
@login_required
def add_payment(payment_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM payments WHERE ID=?", (payment_id,)
    ).fetchone()

    if not row:
        conn.close()
        return redirect("/due_payments")

    try:
        amount = float(request.form.get("amount", 0))
    except ValueError:
        conn.close()
        return redirect("/due_payments")

    if amount <= 0:
        conn.close()
        return redirect("/due_payments")

    new_paid = round(row["PAID_AMOUNT"] + amount, 2)
    new_due  = round(row["TOTAL_AMOUNT"] - new_paid, 2)
    if new_due < 0:
        new_due  = 0
        new_paid = row["TOTAL_AMOUNT"]
    status   = "Cleared" if new_due <= 0 else "Pending"
    today    = datetime.now().strftime("%Y-%m-%d")

    conn.execute("""
        UPDATE payments
        SET PAID_AMOUNT=?, DUE_AMOUNT=?, LAST_PAYMENT_DATE=?, STATUS=?
        WHERE ID=?
    """, (new_paid, new_due, today, status, payment_id))
    conn.commit()
    conn.close()
    return redirect("/due_payments")


# ---------- REPRINT INVOICE ----------
@app.route("/reprint_invoice/<int:sale_id>")
@login_required
def reprint_invoice(sale_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM invoice_data WHERE SALE_ID=?", (sale_id,)
    ).fetchone()
    conn.close()

    if not row:
        return "Invoice data not found for this sale.", 404

    items = json.loads(row["ITEMS_JSON"])

    try:
        invoice_path = generate_invoice(
            sale_id        = sale_id,
            buyer_name     = row["BUYER_NAME"],
            buyer_phone    = row["BUYER_PHONE"],
            buyer_state    = row["BUYER_STATE"],
            buyer_gstin    = row["BUYER_GSTIN"],
            payment_method = row["PAYMENT_METHOD"],
            sale_date      = row["SALE_DATE"],
            items          = items
        )
        with open(invoice_path, "rb") as f:
            pdf_data = f.read()
        os.remove(invoice_path)
        filename = os.path.basename(invoice_path)
        return Response(
            pdf_data,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        return f"Could not generate invoice: {str(e)}"


# ---------- DELETE SALE ----------
@app.route("/delete_sale/<int:sale_id>", methods=["POST"])
@login_required
def delete_sale(sale_id):
    conn = get_db()
    conn.execute("DELETE FROM sale WHERE ID=?", (sale_id,))
    conn.execute("DELETE FROM invoice_data WHERE SALE_ID=?", (sale_id,))
    conn.execute("DELETE FROM payments WHERE SALE_ID=?", (sale_id,))
    conn.commit()
    conn.close()
    return redirect("/view_sales")


# ---------- DELETE PURCHASE ----------
@app.route("/delete_purchase/<int:purchase_id>", methods=["POST"])
@login_required
def delete_purchase(purchase_id):
    conn = get_db()
    conn.execute("DELETE FROM purchase WHERE ID=?", (purchase_id,))
    conn.commit()
    conn.close()
    return redirect("/view_purchases")

# ---------- EDIT STOCK ----------
@app.route("/edit_stock/<int:stock_id>", methods=["GET", "POST"])
@login_required
def edit_stock(stock_id):
    conn = get_db()
    item = conn.execute(
        "SELECT * FROM stock WHERE ID=?", (stock_id,)
    ).fetchone()

    if not item:
        conn.close()
        return redirect("/view_stock")

    error = None

    if request.method == "POST":
        try:
            new_item     = request.form["item"].strip()
            new_material = request.form["material"].strip().upper()
            new_category = request.form["category"].strip().upper()
            new_weight   = float(request.form["weight"])
            new_purity   = float(request.form["purity"])
        except (ValueError, KeyError):
            error = "Invalid input. Please check all fields."
            return render_template("edit_stock.html", item=item, error=error)

        if new_weight <= 0 or new_purity <= 0:
            error = "Weight and Purity must be positive numbers."
            return render_template("edit_stock.html", item=item, error=error)

        if not new_item or not new_material or not new_category:
            error = "All fields are required."
            return render_template("edit_stock.html", item=item, error=error)

        conn.execute("""
            UPDATE stock
            SET ITEM=?, MATERIAL=?, CATEGORY=?, WEIGHT=?, PURITY=?
            WHERE ID=?
        """, (new_item, new_material, new_category, new_weight, new_purity, stock_id))
        conn.commit()
        conn.close()
        return redirect("/view_stock")

    conn.close()
    return render_template("edit_stock.html", item=item, error=error)

# ---------- MAIN ----------
if __name__ == "__main__":
    init_db()
    app.run(debug=False)