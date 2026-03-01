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
SGST_RATE      = 0.015
CGST_RATE      = 0.015
INVOICE_DIR    = "invoices"

RED   = colors.HexColor("#8B0000")
WHITE = colors.white
BLACK = colors.black


def draw_cell(c, x, y, w, h, text, font="Helvetica", size=8,
              fill_color=None, text_color=BLACK, align="left", bold=False):
    """Draw a bordered cell with text."""
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


def generate_invoice(sale_id, item, material, category, weight,
                     purity, hsn_code, rate_per_gram,
                     making_charges=0,
                     buyer_name="", buyer_phone="",
                     sale_date=None):

    os.makedirs(INVOICE_DIR, exist_ok=True)

    if sale_date is None:
        sale_date = datetime.now().strftime("%d-%m-%Y")

    filename = f"Invoice_{sale_id}_{buyer_name.replace(' ', '_')}.pdf"
    filepath = os.path.join(INVOICE_DIR, filename)

    # ── Calculations ─────────────────────────────────────────────
    item_value      = round(weight * rate_per_gram, 2)
    taxable_amount  = round(item_value + making_charges, 2)
    sgst_amount     = round(taxable_amount * SGST_RATE, 2)
    cgst_amount     = round(taxable_amount * CGST_RATE, 2)
    total_after_gst = round(taxable_amount + sgst_amount + cgst_amount, 2)

    W, H = A4  # 595.27 x 841.89 points
    c = canvas.Canvas(filepath, pagesize=A4)

    LEFT    = 12*mm
    RIGHT   = W - 12*mm
    TOP     = H - 12*mm
    BOTTOM  = 12*mm
    INNER_W = RIGHT - LEFT

    # ════════════════════════════════════════════════════════════
    # OUTER BORDER
    # ════════════════════════════════════════════════════════════
    c.setStrokeColor(RED)
    c.setLineWidth(2)
    c.rect(LEFT, BOTTOM, INNER_W, H - 24*mm)

    # ════════════════════════════════════════════════════════════
    # HEADER
    # ════════════════════════════════════════════════════════════
    cur_y = TOP

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(RED)
    c.drawString(LEFT + 2*mm,    cur_y - 6*mm,  f"GSTIN : {SHOP_GSTIN}")
    c.drawString(LEFT + 2*mm,    cur_y - 11*mm, f"PAN   : {SHOP_PAN}")
    c.drawRightString(RIGHT - 2*mm, cur_y - 6*mm,  SHOP_PHONE1)
    c.drawRightString(RIGHT - 2*mm, cur_y - 11*mm, SHOP_PHONE2)

    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(RIGHT - 2*mm, cur_y - 17*mm, "TAX INVOICE")

    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(W / 2, cur_y - 26*mm, SHOP_NAME)

    c.setFont("Helvetica", 6.8)
    c.setFillColor(BLACK)
    c.drawCentredString(W / 2, cur_y - 32*mm, SHOP_TAGLINE)

    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(W / 2, cur_y - 37*mm, SHOP_ADDRESS)

    c.setStrokeColor(RED)
    c.setLineWidth(1)
    c.line(LEFT, cur_y - 40*mm, RIGHT, cur_y - 40*mm)

    # ════════════════════════════════════════════════════════════
    # CUSTOMER + INVOICE INFO
    # ════════════════════════════════════════════════════════════
    info_y  = cur_y - 41*mm
    row_h   = 7*mm
    left_w  = INNER_W * 0.55
    label_w = 22*mm

    labels = ["Name", "State", "GSTN"]
    values = [buyer_name, "Gujarat", "—"]

    for i, (lbl, val) in enumerate(zip(labels, values)):
        ry = info_y - i * row_h
        draw_cell(c, LEFT,              ry - row_h, label_w,            row_h, lbl, bold=True, size=8)
        draw_cell(c, LEFT + label_w,    ry - row_h, left_w - label_w,   row_h, val, size=8)

    box_x   = LEFT + left_w
    box_w   = INNER_W - left_w
    lbl_w_b = box_w * 0.68
    val_w_b = box_w - lbl_w_b

    box_rows = [
        ("Reverse Charge (Y/N)", "N"),
        (f"Inv. No.  {sale_id}",  ""),
        (f"Dated  {sale_date}",   ""),
    ]
    for i, (lbl, val) in enumerate(box_rows):
        ry = info_y - i * row_h
        if val:
            draw_cell(c, box_x,           ry - row_h, lbl_w_b, row_h, lbl, bold=True, size=7.5)
            draw_cell(c, box_x + lbl_w_b, ry - row_h, val_w_b, row_h, val, size=7.5, align="center")
        else:
            draw_cell(c, box_x,           ry - row_h, box_w,   row_h, lbl, bold=True, size=7.5)

    # ════════════════════════════════════════════════════════════
    # ITEM TABLE
    # ════════════════════════════════════════════════════════════
    table_y  = info_y - 3 * row_h - 3*mm
    header_h = 10*mm
    data_h   = 9*mm

    # Column widths — must sum to INNER_W exactly
    c1 = 10*mm   # Sr
    c2 = 66*mm   # Description
    c3 = 20*mm   # HSN
    c4 = 13*mm   # UOM
    c5 = 20*mm   # Weight
    c6 = 22*mm   # Rate
    c7 = INNER_W - c1 - c2 - c3 - c4 - c5 - c6  # Taxable Amount

    COL_DEFS = [
        ("Sr.",                        c1, "center"),
        ("ITEM DESCRIPTION / SERVICE", c2, "left"),
        ("HSN/SAC Code",               c3, "center"),
        ("UOM",                        c4, "center"),
        ("Weight (g)",                 c5, "center"),
        ("Rate (Rs/g)",                c6, "center"),
        ("Taxable Amount (Rs)",        c7, "right"),
    ]

    # Header
    cx = LEFT
    for hdr, cw, align in COL_DEFS:
        draw_cell(c, cx, table_y - header_h, cw, header_h,
                  hdr, fill_color=RED, text_color=WHITE, bold=True, size=7, align="center")
        cx += cw

    # Item row
    row_data = [
        "1",
        f"{item} ({material}) | {category} | Purity: {purity}",
        str(hsn_code),
        "Gms",
        str(weight),
        str(rate_per_gram),
        f"{item_value:.2f}",
    ]
    cx = LEFT
    for (hdr, cw, align), val in zip(COL_DEFS, row_data):
        draw_cell(c, cx, table_y - header_h - data_h, cw, data_h,
                  val, size=7.5, align=align)
        cx += cw

    # Making charges row
    extra_rows = 0
    if making_charges > 0:
        mc_y   = table_y - header_h - data_h
        mc_data = ["2", "Making Charges", str(hsn_code), "—", "—", "—", f"{making_charges:.2f}"]
        cx = LEFT
        for (hdr, cw, align), val in zip(COL_DEFS, mc_data):
            draw_cell(c, cx, mc_y - data_h, cw, data_h,
                      val, size=7.5, align=align)
            cx += cw
        extra_rows = 1

    # Empty filler rows
    filled = 1 + extra_rows
    for extra in range(max(0, 5 - filled)):
        ey = table_y - header_h - (filled + extra + 1) * data_h
        cx = LEFT
        for hdr, cw, align in COL_DEFS:
            draw_cell(c, cx, ey, cw, data_h, "", size=7.5)
            cx += cw

    # ════════════════════════════════════════════════════════════
    # GST SUMMARY
    # ════════════════════════════════════════════════════════════
    total_rows  = max(5, filled)
    gst_start_y = table_y - header_h - (total_rows + 1) * data_h - 3*mm

    gst_lbl_w = 52*mm
    gst_val_w = 30*mm
    gst_x     = RIGHT - gst_lbl_w - gst_val_w
    gst_row_h = 7*mm

    gst_rows = [
        ("TOTAL Before GST",              f"Rs. {taxable_amount:.2f}",  False),
        ("Add SGST @ 1.5%",               f"Rs. {sgst_amount:.2f}",     False),
        ("Add CGST @ 1.5%",               f"Rs. {cgst_amount:.2f}",     False),
        ("Add IGST @ 3.0%",               "Rs. 0.00",                   False),
        ("TOTAL After GST",               f"Rs. {total_after_gst:.2f}", True),
        ("GST Payable on Reverse Charge", "—",                          False),
    ]

    for i, (lbl, val, bold) in enumerate(gst_rows):
        gy = gst_start_y - i * gst_row_h
        fc = RED if bold else None
        tc = WHITE if bold else BLACK
        draw_cell(c, gst_x,             gy - gst_row_h, gst_lbl_w, gst_row_h,
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

    # ════════════════════════════════════════════════════════════
    # FOOTER
    # ════════════════════════════════════════════════════════════
    footer_y = BOTTOM + 42*mm
    c.setStrokeColor(RED)
    c.setLineWidth(0.8)
    c.line(LEFT, footer_y, RIGHT, footer_y)

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(BLACK)
    bank_lines = [
        f"Bank Name  : {BANK_NAME}",
        f"Branch      : {BANK_BRANCH}",
        f"Account No. : {BANK_ACCOUNT}",
        f"IFSC Code   : {BANK_IFSC}",
    ]
    for i, line in enumerate(bank_lines):
        c.drawString(LEFT + 2*mm, footer_y - 6*mm - i * 5.5*mm, line)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(RED)
    c.drawCentredString(W / 2, footer_y - 8*mm, "for RATNAKAR Jewellers")

    c.setFont("Helvetica", 6.5)
    c.setFillColor(BLACK)
    terms = [
        "* Gold once sold are not returnable in any case",
        "* Interest @2% pm will be charged on the amount from the date of Invoice",
        "* Our responsibility ceases after golds are delivered.",
        "* Disputes if any are subject to Ahmedabad Jurisdiction only.",
    ]
    for i, term in enumerate(terms):
        c.drawString(LEFT + 2*mm, footer_y - 28*mm - i * 4.5*mm, term)

    # Signature lines
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.5)
    sig_y = BOTTOM + 14*mm
    c.line(LEFT + 2*mm,   sig_y, LEFT + 55*mm,  sig_y)
    c.line(RIGHT - 55*mm, sig_y, RIGHT - 2*mm,  sig_y)

    c.setFont("Helvetica", 7.5)
    c.drawString(LEFT + 2*mm,    sig_y - 4*mm, "Customer Signature")
    c.drawRightString(RIGHT - 2*mm, sig_y - 4*mm, "Prop./Auth.Signatory")

    c.save()
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
