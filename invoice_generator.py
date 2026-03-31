import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime

# ── Shop constants ───────────────────────────────────────────────
SHOP_NAME      = "Ratnakar Jewellers"
SHOP_TAGLINE   = "Mfrs. in: High Class Gold & Silver Ornaments * KDM JOINTS * 916 Hallmark Jewellery 100% Returnable"
SHOP_ADDRESS   = "LL 5, Temple Avenue, Dharnidhar Derasar, Ahmedabad - 380 007."
SHOP_GSTIN     = "24DJAPS9103J1Z4"
SHOP_PAN       = "DJAPS9103J"
SHOP_PHONE1    = "Nareshbhai Shah (M) 9898812460"
SHOP_PHONE2    = "Bhaumik Shah     (M) 9825266339"
BANK_NAME      = "SBI Bank"
BANK_BRANCH    = "Dharnidhar Branch"
BANK_ACCOUNT   = "41913738898"
BANK_IFSC      = "SBIN0060240"
GST_RATE       = 0.03
LOGO_PATH      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "rj_logo.png")
INVOICE_DIR    = "invoices"

RED   = colors.HexColor("#8B0000")
WHITE = colors.white
BLACK = colors.black
LIGHT = colors.HexColor("#f5f5f5")

W, H     = A4
LEFT     = 12*mm
RIGHT    = W - 12*mm
TOP      = H - 12*mm
BOTTOM   = 12*mm
INNER_W  = RIGHT - LEFT
ROW_H    = 7*mm
HEADER_H = 10*mm
DATA_H   = 9*mm

# ── Normal invoice columns (Gold / Silver — no diamond) ──────────
N_C1  = 8*mm
N_C2  = 42*mm
N_C3  = 20*mm
N_C4  = 14*mm
N_C5  = 16*mm
N_C6  = 10*mm
N_C7  = 16*mm
N_C8  = 20*mm
N_C9  = 20*mm
N_C10 = INNER_W - N_C1 - N_C2 - N_C3 - N_C4 - N_C5 - N_C6 - N_C7 - N_C8 - N_C9

NORMAL_COLS = [
    ("Sr.",          N_C1,  "center"),
    ("Item Name",    N_C2,  "left"),
    ("Material",     N_C3,  "center"),
    ("Purity",       N_C4,  "center"),
    ("HSN/SAC",      N_C5,  "center"),
    ("UOM",          N_C6,  "center"),
    ("Weight (g)",   N_C7,  "center"),
    ("Rate (Rs/g)",  N_C8,  "center"),
    ("Making (Rs)",  N_C9,  "right"),
    ("Amount (Rs)",  N_C10, "right"),
]

# ── Diamond invoice columns (adds Cent + Diamond Rate) ───────────
D_C1  = 7*mm
D_C2  = 30*mm
D_C3  = 16*mm
D_C4  = 12*mm
D_C5  = 13*mm
D_C6  = 8*mm
D_C7  = 13*mm
D_C8  = 15*mm
D_C9  = 12*mm
D_C10 = 18*mm
D_C11 = 15*mm
D_C12 = INNER_W - D_C1 - D_C2 - D_C3 - D_C4 - D_C5 - D_C6 - D_C7 - D_C8 - D_C9 - D_C10 - D_C11

DIAMOND_COLS = [
    ("Sr.",            D_C1,  "center"),
    ("Item Name",      D_C2,  "left"),
    ("Material",       D_C3,  "center"),
    ("Purity",         D_C4,  "center"),
    ("HSN/SAC",        D_C5,  "center"),
    ("UOM",            D_C6,  "center"),
    ("Weight (g)",     D_C7,  "center"),
    ("Rate (Rs/g)",    D_C8,  "center"),
    ("Cent",           D_C9,  "center"),
    ("Dia. Rate (Rs)", D_C10, "center"),
    ("Making (Rs)",    D_C11, "right"),
    ("Amount (Rs)",    D_C12, "right"),
]

USABLE_H    = H - 24*mm
ITEMS_FIRST = max(1, int((USABLE_H - 164*mm) / DATA_H))
ITEMS_OTHER = max(1, int((USABLE_H - 142*mm) / DATA_H))


def purity_to_ct(purity):
    if purity is None or str(purity).strip() == "":
        return "—"
    p = float(purity)
    if p == int(p):
        return f"{int(p)}CT"
    return f"{p}CT"


def draw_cell(c, x, y, w, h, text, font="Helvetica", size=8,
              fill_color=None, text_color=BLACK, align="left", bold=False):
    if fill_color:
        c.setFillColor(fill_color)
        c.rect(x, y, w, h, fill=1, stroke=0)
    c.setStrokeColor(RED)
    c.setLineWidth(0.5)
    c.rect(x, y, w, h, fill=0, stroke=1)
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold" if bold else font, size)
    text = str(text)
    if align == "center":
        c.drawCentredString(x + w / 2, y + h / 2 - size / 3, text)
    elif align == "right":
        c.drawRightString(x + w - 2*mm, y + h / 2 - size / 3, text)
    else:
        c.drawString(x + 2*mm, y + h / 2 - size / 3, text)


def draw_page_header(c, col_defs, sale_id, sale_date, payment_method,
                     buyer_name, buyer_phone, buyer_state, buyer_gstin,
                     is_first_page, page_num, total_pages, buyer_address=""):
    cur_y = TOP

    c.setStrokeColor(RED)
    c.setLineWidth(2)
    c.rect(LEFT, BOTTOM, INNER_W, H - 24*mm)

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(RED)
    c.drawCentredString(W / 2, cur_y - 6*mm, "TAX INVOICE")

    if total_pages > 1:
        c.setFont("Helvetica", 7)
        c.setFillColor(BLACK)
        c.drawRightString(RIGHT - 2*mm, cur_y - 6*mm, f"Page {page_num} of {total_pages}")

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(BLACK)
    c.drawString(LEFT + 2*mm,       cur_y - 13*mm, f"GSTIN : {SHOP_GSTIN}")
    c.drawString(LEFT + 2*mm,       cur_y - 18*mm, f"PAN   : {SHOP_PAN}")
    c.drawRightString(RIGHT - 2*mm, cur_y - 13*mm, SHOP_PHONE1)
    c.drawRightString(RIGHT - 2*mm, cur_y - 18*mm, SHOP_PHONE2)

    try:
        if os.path.exists(LOGO_PATH):
            logo   = ImageReader(LOGO_PATH)
            logo_s = 16*mm
            c.drawImage(logo, W/2 - logo_s/2, cur_y - 29*mm,
                        width=logo_s, height=logo_s,
                        mask="auto", preserveAspectRatio=True)
    except Exception:
        pass

    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(BLACK)
    c.drawCentredString(W / 2, cur_y - 34*mm, SHOP_NAME)

    c.setFont("Helvetica", 6.8)
    c.setFillColor(BLACK)
    c.drawCentredString(W / 2, cur_y - 40*mm, SHOP_TAGLINE)

    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(W / 2, cur_y - 45*mm, SHOP_ADDRESS)

    c.setStrokeColor(RED)
    c.setLineWidth(1)
    c.line(LEFT, cur_y - 48*mm, RIGHT, cur_y - 48*mm)

    info_y = cur_y - 49*mm

    if is_first_page:
        label_w = 28*mm
        left_w  = INNER_W * 0.55
        labels  = ["Name", "Address", "GSTIN", "Phone"]
        values  = [buyer_name,
                   buyer_address if buyer_address else "—",
                   buyer_gstin   if buyer_gstin   else "—",
                   buyer_phone]

        for i, (lbl, val) in enumerate(zip(labels, values)):
            ry = info_y - i * ROW_H
            draw_cell(c, LEFT,           ry - ROW_H, label_w,          ROW_H, lbl, bold=True, size=8)
            draw_cell(c, LEFT + label_w, ry - ROW_H, left_w - label_w, ROW_H, val, size=8)

        box_x    = LEFT + left_w
        box_w    = INNER_W - left_w
        box_rows = [
            f"Invoice No.  :  {sale_id}",
            f"Date  :  {sale_date}",
            f"Payment  :  {payment_method}",
            "",
        ]
        for i, lbl in enumerate(box_rows):
            ry = info_y - i * ROW_H
            draw_cell(c, box_x, ry - ROW_H, box_w, ROW_H, lbl, bold=True, size=8)

        table_top = info_y - 4 * ROW_H - 4*mm
    else:
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(RED)
        c.drawString(LEFT + 2*mm, info_y - 5*mm,
                     f"Invoice No: {sale_id}  |  {sale_date}  |  {buyer_name}  —  Continued from previous page")
        table_top = info_y - 12*mm

    cx = LEFT
    for hdr, cw, _ in col_defs:
        draw_cell(c, cx, table_top - HEADER_H, cw, HEADER_H,
                  hdr, fill_color=RED, text_color=WHITE, bold=True, size=6.5, align="center")
        cx += cw

    return table_top - HEADER_H


def draw_gst_and_footer(c, total_after_gst, taxable_amount, mrp_amount,
                        sgst_amount, cgst_amount, igst_amount,
                        is_gujarat, items_bottom_y):

    gst_lbl_w   = 52*mm
    gst_val_w   = 32*mm
    gst_x       = RIGHT - gst_lbl_w - gst_val_w
    gst_row_h   = 7*mm
    gst_start_y = items_bottom_y - 3*mm

    # Build GST rows — add MRP line only if there are MRP items
    base_rows_gujarat = [
        ("TOTAL (Taxable)",              f"Rs. {taxable_amount:.2f}",  False),
        ("Add SGST @ 1.5%",             f"Rs. {sgst_amount:.2f}",     False),
        ("Add CGST @ 1.5%",             f"Rs. {cgst_amount:.2f}",     False),
        ("Add IGST @ 3.0%",             "Rs. 0.00",                   False),
    ]
    base_rows_other = [
        ("TOTAL (Taxable)",              f"Rs. {taxable_amount:.2f}",  False),
        ("Add SGST @ 1.5%",             "Rs. 0.00",                   False),
        ("Add CGST @ 1.5%",             "Rs. 0.00",                   False),
        ("Add IGST @ 3.0%",             f"Rs. {igst_amount:.2f}",     False),
    ]
    mrp_row = [("MRP Items (incl. GST)", f"Rs. {mrp_amount:.2f}", False)] if mrp_amount > 0 else []
    total_row = [
        ("TOTAL After GST",             f"Rs. {total_after_gst:.2f}", True),
        ("GST Payable on\nRev. Charge", "N",                          False),
    ]
    if is_gujarat:
        gst_rows = base_rows_gujarat + mrp_row + total_row
    else:
        gst_rows = base_rows_other + mrp_row + total_row

    for i, (lbl, val, bold) in enumerate(gst_rows):
        gy = gst_start_y - i * gst_row_h
        fc = RED if bold else None
        tc = WHITE if bold else BLACK
        if "\n" in lbl:
            if fc:
                c.setFillColor(fc)
                c.rect(gst_x, gy - gst_row_h, gst_lbl_w, gst_row_h, fill=1, stroke=0)
            c.setStrokeColor(RED)
            c.setLineWidth(0.5)
            c.rect(gst_x, gy - gst_row_h, gst_lbl_w, gst_row_h, fill=0, stroke=1)
            c.setFillColor(tc)
            c.setFont("Helvetica", 6.5)
            lines = lbl.split("\n")
            c.drawString(gst_x + 2*mm, gy - gst_row_h + gst_row_h * 0.62, lines[0])
            c.drawString(gst_x + 2*mm, gy - gst_row_h + gst_row_h * 0.25, lines[1])
        else:
            draw_cell(c, gst_x, gy - gst_row_h, gst_lbl_w, gst_row_h,
                      lbl, bold=bold, size=7.5, fill_color=fc, text_color=tc)
        draw_cell(c, gst_x + gst_lbl_w, gy - gst_row_h, gst_val_w, gst_row_h,
                  val, bold=bold, size=7.5, align="right", fill_color=fc, text_color=tc)

    mid_x = LEFT + INNER_W * 0.55

    sig_label_y       = BOTTOM + 8*mm
    right_half_center = mid_x + (RIGHT - mid_x) * 0.3
    c.setFont("Helvetica", 8)
    c.setFillColor(BLACK)
    c.drawCentredString(right_half_center, sig_label_y, "Customer Signature")
    c.drawRightString(RIGHT - 2*mm, sig_label_y, "Prop./Auth.Signatory")

    sig_line_y = sig_label_y + 7*mm
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.5)
    c.line(mid_x + 3*mm,  sig_line_y, mid_x + 39*mm, sig_line_y)
    c.line(RIGHT - 33*mm, sig_line_y, RIGHT - 2*mm,  sig_line_y)

    terms = [
        "Declaration :-",
        "We decide that this invoice shows the actual price of the",
        "goods described and that all particular are true and correct",
        "***This a Computer Generated Invoice***",
    ]
    terms_bottom_y = sig_line_y + 4*mm
    c.setFont("Helvetica", 5.5)
    c.setFillColor(colors.HexColor("#333333"))
    for i, term in enumerate(reversed(terms)):
        c.drawString(LEFT + 2*mm, terms_bottom_y + i * 4*mm, term)

    bank_base_y = terms_bottom_y + len(terms) * 4*mm + 3*mm
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(BLACK)
    c.drawString(LEFT + 2*mm, bank_base_y + 15*mm, f"Bank Name  :  {BANK_NAME}")
    c.drawString(LEFT + 2*mm, bank_base_y + 10*mm, f"Branch       :  {BANK_BRANCH}")
    c.drawString(LEFT + 2*mm, bank_base_y + 5*mm,  f"Account No. :  {BANK_ACCOUNT}")
    c.drawString(LEFT + 2*mm, bank_base_y,          f"IFSC Code   :  {BANK_IFSC}")

    words_text = amount_to_words(total_after_gst)
    words_y    = bank_base_y + 20*mm
    c.setFont("Helvetica", 6.5)
    c.setFillColor(BLACK)
    c.drawString(LEFT + 2*mm, words_y, words_text)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(LEFT + 2*mm, words_y + 5*mm, "Amount in words :")

    footer_top = words_y + 11*mm
    c.setStrokeColor(RED)
    c.setLineWidth(0.8)
    c.line(LEFT, footer_top, RIGHT, footer_top)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(RED)
    c.drawRightString(RIGHT - 2*mm, footer_top - 5*mm, "for RATNAKAR Jewellers")

    c.setStrokeColor(RED)
    c.setLineWidth(0.5)
    c.line(mid_x, footer_top, mid_x, BOTTOM + 2*mm)


def _normal_row(itm, sr):
    rate_val = float(itm.get("rate_per_gram", 0) or 0)
    return [
        str(sr),
        str(itm["item"]),
        str(itm["material"]),
        purity_to_ct(itm["purity"]),
        str(itm["hsn"]),
        "Gms",
        str(itm["weight"]),
        f"{rate_val:.2f}" if rate_val > 0 else "—",
        f"{float(itm.get('making_charges', 0)):.2f}",
        f"{float(itm['item_total']):.2f}",
    ]


def _diamond_row(itm, sr):
    rate_val = float(itm.get("rate_per_gram", 0) or 0)
    flat_val = float(itm.get("flat_price", 0) or 0)
    cent_val = itm.get("cent")
    cent_str = f"{float(cent_val):.2f}" if cent_val is not None else "—"
    return [
        str(sr),
        str(itm["item"]),
        str(itm["material"]),
        purity_to_ct(itm["purity"]),
        str(itm["hsn"]),
        "Gms",
        str(itm["weight"]),
        f"{rate_val:.2f}" if rate_val > 0 else "—",
        cent_str,
        f"{flat_val:.2f}" if flat_val > 0 else "—",
        f"{float(itm.get('making_charges', 0)):.2f}",
        f"{float(itm['item_total']):.2f}",
    ]


def generate_invoice(sale_id, buyer_name="", buyer_phone="",
                     sale_date=None, items=None,
                     buyer_gstin="", buyer_state="Gujarat", buyer_address="",
                     payment_method="Cash",
                     item=None, material=None, category=None,
                     weight=None, purity=None, hsn_code=None,
                     rate_per_gram=None, making_charges=0):

    os.makedirs(INVOICE_DIR, exist_ok=True)

    if sale_date is None:
        sale_date = datetime.now().strftime("%d-%m-%Y")

    if items is None:
        _rpg = float(rate_per_gram or 0)
        items = [{
            "item": item, "material": material, "category": category,
            "weight": weight, "purity": purity, "hsn": hsn_code,
            "rate_per_gram": _rpg, "flat_price": 0.0,
            "making_charges": making_charges,
            "item_total": round((weight * _rpg) + making_charges, 2),
            "cent": None, "mrp_price": None,
        }]

    # Normalise — old carts may be missing new keys
    for itm in items:
        itm.setdefault("flat_price", 0)
        itm.setdefault("rate_per_gram", 0)
        itm.setdefault("making_charges", 0)
        itm.setdefault("cent", None)
        itm.setdefault("mrp_price", None)
        itm.setdefault("is_mrp", False)
        # Auto-detect MRP silver if flag missing (old cart data)
        if not itm["is_mrp"] and str(itm.get("material","")).upper() == "SILVER":
            mrp_val = float(itm.get("mrp_price") or 0)
            if mrp_val > 0 and float(itm.get("rate_per_gram") or 0) == 0:
                itm["is_mrp"] = True

    # Invoice type: diamond layout if any item is DIAMOND
    has_diamond = any(str(i.get("material", "")).upper() == "DIAMOND" for i in items)
    col_defs    = DIAMOND_COLS if has_diamond else NORMAL_COLS
    build_row   = _diamond_row if has_diamond else _normal_row

    # GST — MRP silver items are already at inclusive price, no GST on top
    gstin_clean    = (buyer_gstin or "").strip()
    is_gujarat     = (not gstin_clean) or gstin_clean.startswith("24")
    mrp_amount     = round(sum(float(i["item_total"]) for i in items if i.get("is_mrp")), 2)
    taxable_amount = round(sum(float(i["item_total"]) for i in items if not i.get("is_mrp")), 2)
    total_before_gst = round(taxable_amount + mrp_amount, 2)

    if is_gujarat:
        sgst_amount = round(taxable_amount * 0.015, 2)
        cgst_amount = round(taxable_amount * 0.015, 2)
        igst_amount = 0.00
    else:
        sgst_amount = 0.00
        cgst_amount = 0.00
        igst_amount = round(taxable_amount * GST_RATE, 2)

    total_after_gst = round(total_before_gst + sgst_amount + cgst_amount + igst_amount, 2)

    # Paginate
    if len(items) <= ITEMS_FIRST:
        pages = [items]
    else:
        pages     = [items[:ITEMS_FIRST]]
        remaining = items[ITEMS_FIRST:]
        while remaining:
            pages.append(remaining[:ITEMS_OTHER])
            remaining = remaining[ITEMS_OTHER:]

    total_pages = len(pages)
    filename    = f"Invoice_{sale_id}_{buyer_name.replace(' ', '_')}.pdf"
    filepath    = os.path.join(INVOICE_DIR, filename)
    cv          = canvas.Canvas(filepath, pagesize=A4)

    global_sr = 0

    for page_num, page_items in enumerate(pages, start=1):
        is_first = page_num == 1
        is_last  = page_num == total_pages

        row_top_y = draw_page_header(
            cv, col_defs, sale_id, sale_date, payment_method,
            buyer_name, buyer_phone, buyer_state, buyer_gstin,
            is_first_page=is_first,
            page_num=page_num,
            total_pages=total_pages,
            buyer_address=buyer_address
        )

        for local_idx, itm in enumerate(page_items):
            global_sr += 1
            row_y    = row_top_y - local_idx * DATA_H
            row_data = build_row(itm, global_sr)
            fill     = LIGHT if global_sr % 2 == 1 else None
            cx       = LEFT
            for (_, cw, align), val in zip(col_defs, row_data):
                draw_cell(cv, cx, row_y - DATA_H, cw, DATA_H,
                          val, size=7, align=align, fill_color=fill)
                cx += cw

        items_drawn = len(page_items)

        if is_last:
            EMPTY_H       = 7*mm
            min_rows      = 4 if is_first else 2
            empty_to_draw = max(0, min_rows - items_drawn)
            empty_top_y   = row_top_y - items_drawn * DATA_H
            for extra in range(empty_to_draw):
                ey = empty_top_y - extra * EMPTY_H
                cx = LEFT
                for _, cw, _ in col_defs:
                    draw_cell(cv, cx, ey - EMPTY_H, cw, EMPTY_H, "", size=7)
                    cx += cw

            items_bottom_y = (empty_top_y - empty_to_draw * EMPTY_H
                              if empty_to_draw > 0
                              else row_top_y - items_drawn * DATA_H)

            draw_gst_and_footer(
                cv, total_after_gst, taxable_amount, mrp_amount,
                sgst_amount, cgst_amount, igst_amount,
                is_gujarat, items_bottom_y
            )
        else:
            cont_y = row_top_y - items_drawn * DATA_H - 5*mm
            cv.setFont("Helvetica-Bold", 7.5)
            cv.setFillColor(RED)
            cv.drawRightString(RIGHT - 2*mm, cont_y, "Continued on next page →")
            cv.showPage()

    cv.save()
    return filepath


# ── Amount to words (Indian format) ─────────────────────────────
def amount_to_words(amount):
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
            "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
            "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty",
            "Sixty", "Seventy", "Eighty", "Ninety"]

    def words(n):
        if n == 0:         return ""
        elif n < 20:       return ones[n]
        elif n < 100:      return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
        elif n < 1000:     return ones[n // 100] + " Hundred" + (" " + words(n % 100) if n % 100 else "")
        elif n < 100000:   return words(n // 1000) + " Thousand" + (" " + words(n % 1000) if n % 1000 else "")
        elif n < 10000000: return words(n // 100000) + " Lakh" + (" " + words(n % 100000) if n % 100000 else "")
        else:              return words(n // 10000000) + " Crore" + (" " + words(n % 10000000) if n % 10000000 else "")

    rupees = int(amount)
    paise  = round((amount - rupees) * 100)
    result = words(rupees) + " Rupees"
    if paise:
        result += " and " + words(paise) + " Paise"
    return result + " Only"
