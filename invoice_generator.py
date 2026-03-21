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

W, H    = A4
LEFT    = 12*mm
RIGHT   = W - 12*mm
TOP     = H - 12*mm
BOTTOM  = 12*mm
INNER_W = RIGHT - LEFT
ROW_H   = 7*mm
HEADER_H = 10*mm
DATA_H   = 9*mm

C1  = 8*mm
C2  = 40*mm
C3  = 20*mm
C4  = 14*mm
C5  = 16*mm
C6  = 10*mm
C7  = 16*mm
C8  = 18*mm
C9  = 18*mm
C10 = INNER_W - C1 - C2 - C3 - C4 - C5 - C6 - C7 - C8 - C9

COL_DEFS = [
    ("Sr.",         C1,  "center"),
    ("Item Name",   C2,  "left"),
    ("Material",    C3,  "center"),
    ("Purity",      C4,  "center"),
    ("HSN/SAC",     C5,  "center"),
    ("UOM",         C6,  "center"),
    ("Weight (g)",  C7,  "center"),
    ("Rate (Rs/g)", C8,  "center"),
    ("Making (Rs)", C9,  "right"),
    ("Amount (Rs)", C10, "right"),
]

# How many item rows fit per page
# First page: header(47mm) + customer box(32mm) + table header(10mm) + footer space(75mm) = 164mm used
# Other pages: header(47mm) + continuation note(10mm) + table header(10mm) + footer space(75mm) = 142mm used
USABLE_H        = H - 24*mm   # page height minus top/bottom margins
ITEMS_FIRST     = max(1, int((USABLE_H - 164*mm) / DATA_H))
ITEMS_OTHER     = max(1, int((USABLE_H - 142*mm) / DATA_H))


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


def draw_page_header(c, sale_id, sale_date, payment_method,
                     buyer_name, buyer_phone, buyer_state, buyer_gstin,
                     is_first_page, page_num, total_pages):
    """Draw shop header + optionally customer info + table header.
    Returns the y coordinate where item rows should start (top of first data row)."""

    cur_y = TOP

    # Outer border
    c.setStrokeColor(RED)
    c.setLineWidth(2)
    c.rect(LEFT, BOTTOM, INNER_W, H - 24*mm)

    # TAX INVOICE
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(RED)
    c.drawCentredString(W / 2, cur_y - 6*mm, "TAX INVOICE")

    # Page number (if multi-page)
    if total_pages > 1:
        c.setFont("Helvetica", 7)
        c.setFillColor(BLACK)
        c.drawRightString(RIGHT - 2*mm, cur_y - 6*mm, f"Page {page_num} of {total_pages}")

    # GSTIN / PAN / Phones
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(BLACK)
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

    info_y = cur_y - 47*mm

    if is_first_page:
        # Customer + invoice info
        label_w = 28*mm
        left_w  = INNER_W * 0.55
        labels  = ["Name", "State", "GSTIN", "Phone"]
        values  = [buyer_name, buyer_state,
                   buyer_gstin if buyer_gstin else "—", buyer_phone]

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
        # Continuation note
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(RED)
        c.drawString(LEFT + 2*mm, info_y - 5*mm,
                     f"Invoice No: {sale_id}  |  {sale_date}  |  {buyer_name}  —  Continued from previous page")
        table_top = info_y - 12*mm

    # Table column headers
    cx = LEFT
    for hdr, cw, align in COL_DEFS:
        draw_cell(c, cx, table_top - HEADER_H, cw, HEADER_H,
                  hdr, fill_color=RED, text_color=WHITE, bold=True, size=7, align="center")
        cx += cw

    # Return y where first data row top edge is
    return table_top - HEADER_H


def draw_gst_and_footer(c, total_after_gst, taxable_amount,
                        sgst_amount, cgst_amount, igst_amount,
                        is_gujarat, items_bottom_y):
    """Draw GST summary box and full footer below items_bottom_y."""

    gst_lbl_w = 52*mm
    gst_val_w = 32*mm
    gst_x     = RIGHT - gst_lbl_w - gst_val_w
    gst_row_h = 7*mm
    gst_start_y = items_bottom_y - 3*mm

    if is_gujarat:
        gst_rows = [
            ("TOTAL Before GST",            f"Rs. {taxable_amount:.2f}",  False),
            ("Add SGST @ 1.5%",             f"Rs. {sgst_amount:.2f}",     False),
            ("Add CGST @ 1.5%",             f"Rs. {cgst_amount:.2f}",     False),
            ("Add IGST @ 3.0%",             "Rs. 0.00",                   False),
            ("TOTAL After GST",             f"Rs. {total_after_gst:.2f}", True),
            ("GST Payable on\nRev. Charge", "N",                          False),
        ]
    else:
        gst_rows = [
            ("TOTAL Before GST",            f"Rs. {taxable_amount:.2f}",  False),
            ("Add SGST @ 1.5%",             "Rs. 0.00",                   False),
            ("Add CGST @ 1.5%",             "Rs. 0.00",                   False),
            ("Add IGST @ 3.0%",             f"Rs. {igst_amount:.2f}",     False),
            ("TOTAL After GST",             f"Rs. {total_after_gst:.2f}", True),
            ("GST Payable on\nRev. Charge", "N",                          False),
        ]

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

    footer_top = gst_start_y - len(gst_rows) * gst_row_h - 4*mm

    # ── Everything anchored from BOTTOM up ───────────────────────
    mid_x = LEFT + INNER_W * 0.55

    # Signatures — pinned to very bottom
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

    # Terms — just above signatures
    terms = [
        "* Gold once sold are not returnable in any case.",
        "* Interest @2% pm will be charged on the amount from the date of Invoice.",
        "* Our responsibility ceases after golds are delivered.",
        "* Disputes if any are subject to Ahmedabad Jurisdiction only.",
    ]
    terms_bottom_y = sig_line_y + 4*mm
    c.setFont("Helvetica", 5.5)
    c.setFillColor(colors.HexColor("#333333"))
    for i, term in enumerate(reversed(terms)):
        c.drawString(LEFT + 2*mm, terms_bottom_y + i * 4*mm, term)

    # Bank details — just above terms
    bank_base_y = terms_bottom_y + len(terms) * 4*mm + 3*mm
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(BLACK)
    c.drawString(LEFT + 2*mm, bank_base_y + 15*mm, f"Bank Name  :  {BANK_NAME}")
    c.drawString(LEFT + 2*mm, bank_base_y + 10*mm, f"Branch       :  {BANK_BRANCH}")
    c.drawString(LEFT + 2*mm, bank_base_y + 5*mm,  f"Account No. :  {BANK_ACCOUNT}")
    c.drawString(LEFT + 2*mm, bank_base_y,          f"IFSC Code   :  {BANK_IFSC}")

    # Amount in words — just above bank details
    words_text = amount_to_words(total_after_gst)
    words_y = bank_base_y + 20*mm
    c.setFont("Helvetica", 6.5)
    c.setFillColor(BLACK)
    c.drawString(LEFT + 2*mm, words_y, words_text)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(LEFT + 2*mm, words_y + 5*mm, "Amount in words :")

    # Footer divider line — just above amount in words
    footer_top = words_y + 11*mm
    c.setStrokeColor(RED)
    c.setLineWidth(0.8)
    c.line(LEFT, footer_top, RIGHT, footer_top)

    # For RATNAKAR Jewellers
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(RED)
    c.drawRightString(RIGHT - 2*mm, footer_top - 5*mm, "for RATNAKAR Jewellers")

    # Vertical divider — full height from footer divider to bottom
    c.setStrokeColor(RED)
    c.setLineWidth(0.5)
    c.line(mid_x, footer_top, mid_x, BOTTOM + 2*mm)


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

    # ── Split items into pages ────────────────────────────────────
    if len(items) <= ITEMS_FIRST:
        pages = [items]
    else:
        pages      = [items[:ITEMS_FIRST]]
        remaining  = items[ITEMS_FIRST:]
        while remaining:
            pages.append(remaining[:ITEMS_OTHER])
            remaining = remaining[ITEMS_OTHER:]

    total_pages = len(pages)

    # ── Build PDF ─────────────────────────────────────────────────
    filename = f"Invoice_{sale_id}_{buyer_name.replace(' ', '_')}.pdf"
    filepath = os.path.join(INVOICE_DIR, filename)
    cv = canvas.Canvas(filepath, pagesize=A4)

    global_item_index = 0

    for page_num, page_items in enumerate(pages, start=1):
        is_first = page_num == 1
        is_last  = page_num == total_pages

        # Draw header and get y where rows start
        row_top_y = draw_page_header(
            cv, sale_id, sale_date, payment_method,
            buyer_name, buyer_phone, buyer_state, buyer_gstin,
            is_first_page=is_first,
            page_num=page_num,
            total_pages=total_pages
        )

        # Draw item rows
        for local_idx, itm in enumerate(page_items):
            row_y = row_top_y - local_idx * DATA_H
            row_data = [
                str(global_item_index + 1),
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
            fill = LIGHT if global_item_index % 2 == 0 else None
            cx = LEFT
            for (hdr, cw, align), val in zip(COL_DEFS, row_data):
                draw_cell(cv, cx, row_y - DATA_H, cw, DATA_H,
                          val, size=7.5, align=align, fill_color=fill)
                cx += cw
            global_item_index += 1

        items_drawn = len(page_items)

        if is_last:
            # Fill minimum empty rows — small fixed height
            EMPTY_H = 7*mm
            min_rows = 4 if is_first else 2
            empty_to_draw = max(0, min_rows - items_drawn)
            empty_top_y = row_top_y - items_drawn * DATA_H
            for extra in range(empty_to_draw):
                ey = empty_top_y - extra * EMPTY_H
                cx = LEFT
                for hdr, cw, align in COL_DEFS:
                    draw_cell(cv, cx, ey - EMPTY_H, cw, EMPTY_H, "", size=7.5)
                    cx += cw

            # GST sits right below last row (items or empty)
            if empty_to_draw > 0:
                items_bottom_y = empty_top_y - empty_to_draw * EMPTY_H
            else:
                items_bottom_y = row_top_y - items_drawn * DATA_H

            draw_gst_and_footer(
                cv, total_after_gst, taxable_amount,
                sgst_amount, cgst_amount, igst_amount,
                is_gujarat, items_bottom_y
            )
        else:
            # "Continued" note at bottom of non-last pages
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