# 💎 Ratnakar Jewellery Management System

A production-ready web application for managing a jewellery shop — built with Flask and SQLite, featuring GST-compliant invoice generation, inventory management, sales tracking, and full data backup and restore.

---

## 🖼️ Overview

This system was built to replace manual record-keeping in a traditional jewellery shop. It handles the full lifecycle of a jewellery item — from purchase and stock entry to sale, invoice generation, and payment tracking — with a clean, mobile-friendly interface accessible from any device.

---

## ✨ Features

### 📦 Inventory & Stock
- Add purchases via a multi-item cart with tag ID, material, weight, and purity
- View current stock with pagination (50 items per page)
- Edit stock items — changes sync to purchase history automatically
- Delete stock with confirmation
- Live stock search on the sale page — type item name, ID, or material to auto-fill

### 💰 Sales & Invoicing
- Cart-based sale flow with HSN/SAC code, rate per gram, and making charges
- Full confirmation modal before completing a sale — review everything before it's final
- GST-compliant PDF invoice generated automatically on sale completion (SGST/CGST for Gujarat, IGST for other states)
- Reprint any past invoice at any time
- Partial payment support — outstanding balance tracked automatically
- Delete a sale — stock items restored to inventory automatically

### 📊 Reports
- Daily, monthly, yearly, and custom date range reports
- Revenue totals before and after GST
- Weight totals for purchases and sales
- Export any report as a dated CSV file

### 💳 Due Payments & Trade Dues
- Track partial payments with running balance
- Record trade dues (gold/silver owed by sellers)
- Settle dues incrementally with automatic status updates

### 🔍 Search
- Unified search across current stock, sales history, and purchase history in one query
- Scope filter to narrow to a specific table

### 📤 Export & Backup
- Export any table (stock, purchases, sales, payments, trade dues) as a dated CSV
- Full Excel backup with 5 sheets — one per table — with colour-coded headers and import instructions built in
- Download backup file directly from the dashboard

### 📂 Import & Restore
- Import stock, purchases, sales, due payments, and trade dues from CSV or Excel
- Auto-detects backup file header format (note row above headers)
- Step-by-step restore guide built into the import page
- Column reference table for all 5 import types

### 🔐 Security
- CSRF protection on every form
- Session timeout after 2 hours of inactivity
- Login lockout after 5 failed attempts (15-minute cooldown)
- Secure session cookies (HttpOnly, SameSite, Secure)
- Password hashing with Werkzeug
- Input length limits and weight sanity caps
- SQL injection protection via parameterised queries
- Custom 403, 404, and 500 error pages

### 👥 User Management (Admin)
- Add and delete users with role assignment (admin or standard)
- Reset any user's password
- Change your own password at any time

### 📋 Audit Log (Admin)
- Every sale, purchase, delete, edit, import, backup, and user action is logged
- Timestamp, username, action type, and detail stored per entry

### 🗄️ Dashboard
- Live gold, silver, and diamond stock weights
- Pending dues and trade dues count with colour alerts
- Database size monitoring with percentage of storage limit used

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database | SQLite (WAL mode) |
| Invoice Generation | ReportLab |
| Excel Export/Import | openpyxl |
| Frontend | Jinja2 templates, vanilla CSS, vanilla JavaScript |
| Auth | Werkzeug password hashing, Flask sessions |

---

## 🚀 Local Setup

**1. Clone the repository**
```bash
git clone https://github.com/PriyanshJeeleshJhaveri/jewellery-management-system.git
cd jewellery-management-system
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Initialise the database**
```bash
python3 -c "from app import init_db; init_db(); print('Done')"
```

**4. Set environment variable and run**
```bash
export SECRET_KEY="your-random-secret-key-here"
python3 app.py
```

**5. Open in browser**
```
http://localhost:5000
```

Default login: `admin` / `admin123` — **change this immediately after first login.**

---

## 📁 Project Structure

```
jewellery-management-system/
├── app.py                  # All routes and business logic
├── invoice_generator.py    # PDF invoice generation with ReportLab
├── requirements.txt
├── test_website.py         # Automated feature test suite
├── static/
│   └── style.css
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── add_purchase.html
    ├── record_sale.html
    ├── view_stock.html
    ├── view_purchases.html
    ├── view_sales.html
    ├── search.html
    ├── report.html
    ├── import_data.html
    ├── export_data.html
    ├── due_payments.html
    ├── trade_dues.html
    ├── manage_users.html
    ├── audit_log.html
    ├── change_password.html
    └── 403.html / 404.html / 500.html
```

---

## 🤖 Built With AI Mentorship

This project was built with the guidance of **Claude (Anthropic)** acting as a brutally honest technical mentor throughout the development process.

The AI did not build the project for me — it reviewed my code, identified security vulnerabilities, data integrity bugs, and architectural decisions, then challenged me to understand each problem before providing fixes. Every issue was explained, every trade-off was discussed, and I was asked to confirm my understanding before moving forward.

Issues identified and resolved through this process included CSRF vulnerabilities, broken database transactions, hardcoded secrets, session security, SQL injection exposure, storage optimisation, and a complete audit and backup system — none of which existed in the original version.

The experience of working with an AI as a mentor rather than a code generator produced a significantly more secure and production-ready result than building alone.

---

## 📄 License

This project is for personal and commercial use by Ratnakar Jewellers. Not licensed for redistribution.

---

*Built for Ratnakar Jewellers, Ahmedabad.*
