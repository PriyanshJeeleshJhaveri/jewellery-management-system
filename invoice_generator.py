import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
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
INVOICE_DIR    = "invoices"

RED   = colors.HexColor("#8B0000")
WHITE = colors.white
BLACK = colors.black
LIGHT = colors.HexColor("#f5f5f5")


def purity_to_ct(purity):
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


def generate_invoice(sale_id, buyer_name="", buyer_phone="",
                     sale_date=None, items=None,
                     buyer_gstin="", buyer_state="Gujarat",
                     payment_method="Cash",
                     item=None, material=None, category=None,
                     weight=None, purity=None, hsn_code=None,
                     rate_per_gram=None, making_charges=0):

    os.makedirs(INVOICE_DIR, exist_ok=True)

    if sale_date is None:
        sale_date = datetime.now().strftime("%d-%m-%Y")

    if items is None:
        items = [{
            "item":           item,
            "material":       material,
            "category":       category,
            "weight":         weight,
            "purity":         purity,
            "hsn":            hsn_code,
            "rate_per_gram":  rate_per_gram,
            "making_charges": making_charges,
            "item_total":     round((weight * rate_per_gram) + making_charges, 2)
        }]

    is_gujarat     = buyer_state.strip().upper() == "GUJARAT"
    taxable_amount = round(sum(i["item_total"] for i in items), 2)

    if is_gujarat:
        sgst_amount = round(taxable_amount * 0.015, 2)
        cgst_amount = round(taxable_amount * 0.015, 2)
        igst_amount = 0.00
    else:
        sgst_amount = 0.00
        cgst_amount = 0.00
        igst_amount = round(taxable_amount * GST_RATE, 2)

    total_after_gst = round(taxable_amount + sgst_amount + cgst_amount + igst_amount, 2)

    filename = f"Invoice_{sale_id}_{buyer_name.replace(' ', '_')}.pdf"
    filepath = os.path.join(INVOICE_DIR, filename)

    W, H = A4
    c = canvas.Canvas(filepath, pagesize=A4)

    LEFT    = 12*mm
    RIGHT   = W - 12*mm
    TOP     = H - 12*mm
    BOTTOM  = 12*mm
    INNER_W = RIGHT - LEFT

    # Outer border
    c.setStrokeColor(RED)
    c.setLineWidth(2)
    c.rect(LEFT, BOTTOM, INNER_W, H - 24*mm)

    cur_y = TOP

    # TAX INVOICE centered at top
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(RED)
    c.drawCentredString(W / 2, cur_y - 6*mm, "TAX INVOICE")

    # GSTIN / PAN / Phone
    c.setFont("Helvetica-Bold", 8)
    c.drawString(LEFT + 2*mm,       cur_y - 13*mm, f"GSTIN : {SHOP_GSTIN}")
    c.drawString(LEFT + 2*mm,       cur_y - 18*mm, f"PAN   : {SHOP_PAN}")
    c.drawRightString(RIGHT - 2*mm, cur_y - 13*mm, SHOP_PHONE1)
    c.drawRightString(RIGHT - 2*mm, cur_y - 18*mm, SHOP_PHONE2)

    # Shop name
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(W / 2, cur_y - 32*mm, SHOP_NAME)

    c.setFont("Helvetica", 6.8)
    c.setFillColor(BLACK)
    c.drawCentredString(W / 2, cur_y - 38*mm, SHOP_TAGLINE)

    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(W / 2, cur_y - 43*mm, SHOP_ADDRESS)

    c.setStrokeColor(RED)
    c.setLineWidth(1)
    c.line(LEFT, cur_y - 46*mm, RIGHT, cur_y - 46*mm)

    # Customer + Invoice info
    info_y  = cur_y - 47*mm
    row_h   = 7*mm
    left_w  = INNER_W * 0.55
    label_w = 28*mm

    labels = ["Name", "State", "GSTIN", "Phone"]
    values = [
        buyer_name,
        buyer_state,
        buyer_gstin if buyer_gstin else "—",
        buyer_phone
    ]

    for i, (lbl, val) in enumerate(zip(labels, values)):
        ry = info_y - i * row_h
        draw_cell(c, LEFT,           ry - row_h, label_w,          row_h, lbl, bold=True, size=8)
        draw_cell(c, LEFT + label_w, ry - row_h, left_w - label_w, row_h, val, size=8)

    box_x = LEFT + left_w
    box_w = INNER_W - left_w

    box_rows = [
        f"Invoice No.  :  {sale_id}",
        f"Date  :  {sale_date}",
        f"Payment  :  {payment_method}",
        "",
    ]
    for i, lbl in enumerate(box_rows):
        ry = info_y - i * row_h
        draw_cell(c, box_x, ry - row_h, box_w, row_h, lbl, bold=True, size=8)

    # Item table
    table_y  = info_y - 4 * row_h - 4*mm
    header_h = 10*mm
    data_h   = 9*mm

    c1  = 8*mm
    c2  = 40*mm
    c3  = 20*mm
    c4  = 14*mm
    c5  = 16*mm
    c6  = 10*mm
    c7  = 16*mm
    c8  = 18*mm
    c9  = 18*mm
    c10 = INNER_W - c1 - c2 - c3 - c4 - c5 - c6 - c7 - c8 - c9

    COL_DEFS = [
        ("Sr.",          c1,  "center"),
        ("Item Name",    c2,  "left"),
        ("Material",     c3,  "center"),
        ("Purity",       c4,  "center"),
        ("HSN/SAC",      c5,  "center"),
        ("UOM",          c6,  "center"),
        ("Weight (g)",   c7,  "center"),
        ("Rate (Rs/g)",  c8,  "center"),
        ("Making (Rs)",  c9,  "right"),
        ("Amount (Rs)",  c10, "right"),
    ]

    # Header row
    cx = LEFT
    for hdr, cw, align in COL_DEFS:
        draw_cell(c, cx, table_y - header_h, cw, header_h,
                  hdr, fill_color=RED, text_color=WHITE, bold=True, size=7, align="center")
        cx += cw

    # Data rows
    for idx, itm in enumerate(items):
        row_y    = table_y - header_h - (idx + 1) * data_h
        row_data = [
            str(idx + 1),
            str(itm["item"]),
            str(itm["material"]),
            purity_to_ct(itm["purity"]),
            str(itm["hsn"]),
            "Gms",
            str(itm["weight"]),
            str(itm["rate_per_gram"]),
            f"{float(itm['making_charges']):.2f}",
            f"{itm['item_total']:.2f}",
        ]
        fill = LIGHT if idx % 2 == 0 else None
        cx = LEFT
        for (hdr, cw, align), val in zip(COL_DEFS, row_data):
            draw_cell(c, cx, row_y, cw, data_h, val, size=7.5,
                      align=align, fill_color=fill)
            cx += cw

    # Empty filler rows
    total_data_rows = len(items)
    for extra in range(max(0, 4 - total_data_rows)):
        ey = table_y - header_h - (total_data_rows + extra + 1) * data_h
        cx = LEFT
        for hdr, cw, align in COL_DEFS:
            draw_cell(c, cx, ey, cw, data_h, "", size=7.5)
            cx += cw

    # GST Summary
    total_rows  = max(4, total_data_rows)
    gst_start_y = table_y - header_h - (total_rows + 1) * data_h - 3*mm

    gst_lbl_w = 52*mm
    gst_val_w = 32*mm
    gst_x     = RIGHT - gst_lbl_w - gst_val_w
    gst_row_h = 7*mm

    if is_gujarat:
        gst_rows = [
            ("TOTAL Before GST", f"Rs. {taxable_amount:.2f}",  False),
            ("Add SGST @ 1.5%",  f"Rs. {sgst_amount:.2f}",     False),
            ("Add CGST @ 1.5%",  f"Rs. {cgst_amount:.2f}",     False),
            ("Add IGST @ 3.0%",  "Rs. 0.00",                   False),
            ("TOTAL After GST",  f"Rs. {total_after_gst:.2f}", True),
        ]
    else:
        gst_rows = [
            ("TOTAL Before GST", f"Rs. {taxable_amount:.2f}",  False),
            ("Add SGST @ 1.5%",  "Rs. 0.00",                   False),
            ("Add CGST @ 1.5%",  "Rs. 0.00",                   False),
            ("Add IGST @ 3.0%",  f"Rs. {igst_amount:.2f}",     False),
            ("TOTAL After GST",  f"Rs. {total_after_gst:.2f}", True),
        ]

    for i, (lbl, val, bold) in enumerate(gst_rows):
        gy = gst_start_y - i * gst_row_h
        fc = RED if bold else None
        tc = WHITE if bold else BLACK
        draw_cell(c, gst_x,              gy - gst_row_h, gst_lbl_w, gst_row_h,
                  lbl, bold=bold, size=7.5, fill_color=fc, text_color=tc)
        draw_cell(c, gst_x + gst_lbl_w, gy - gst_row_h, gst_val_w, gst_row_h,
                  val, bold=bold, size=7.5, align="right", fill_color=fc, text_color=tc)

    # Amount in words
    words_y = gst_start_y - len(gst_rows) * gst_row_h - 5*mm
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(BLACK)
    c.drawString(LEFT + 2*mm,  words_y, "Amount in Words :")
    c.setFont("Helvetica", 7.5)
    c.drawString(LEFT + 43*mm, words_y, amount_to_words(total_after_gst))

    # Footer
    footer_y = BOTTOM + 46*mm
    c.setStrokeColor(RED)
    c.setLineWidth(0.8)
    c.line(LEFT, footer_y, RIGHT, footer_y)

    # Bank details box
    bank_box_w = 80*mm
    bank_box_h = 28*mm
    c.setStrokeColor(RED)
    c.setLineWidth(0.5)
    c.rect(LEFT, footer_y - bank_box_h, bank_box_w, bank_box_h)

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(RED)
    c.drawCentredString(LEFT + bank_box_w / 2, footer_y - 6*mm, "BANK DETAILS")

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(BLACK)
    bank_lines = [
        f"Bank Name   :  {BANK_NAME}",
        f"Branch       :  {BANK_BRANCH}",
        f"Account No. :  {BANK_ACCOUNT}",
        f"IFSC Code   :  {BANK_IFSC}",
    ]
    for i, line in enumerate(bank_lines):
        c.drawString(LEFT + 3*mm, footer_y - 12*mm - i * 5*mm, line)

    # Shop signature
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(RED)
    c.drawCentredString(W / 2 + 20*mm, footer_y - 8*mm, "for RATNAKAR Jewellers")

    # Terms
    c.setFont("Helvetica", 6.3)
    c.setFillColor(BLACK)
    terms = [
        "* Gold once sold are not returnable in any case.",
        "* Interest @2% pm will be charged on the amount from the date of Invoice.",
        "* Our responsibility ceases after golds are delivered.",
        "* Disputes if any are subject to Ahmedabad Jurisdiction only.",
    ]
    for i, term in enumerate(terms):
        c.drawString(LEFT + bank_box_w + 4*mm, footer_y - 14*mm - i * 5*mm, term)

    # Signatures
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.5)
    sig_y = BOTTOM + 14*mm
    c.line(LEFT + 2*mm,   sig_y, LEFT + 55*mm,  sig_y)
    c.line(RIGHT - 55*mm, sig_y, RIGHT - 2*mm,  sig_y)

    c.setFont("Helvetica", 7.5)
    c.setFillColor(BLACK)
    c.drawString(LEFT + 2*mm,       sig_y - 4*mm, "Customer Signature")
    c.drawRightString(RIGHT - 2*mm, sig_y - 4*mm, "Prop./Auth.Signatory")

    c.save()
    return filepath


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