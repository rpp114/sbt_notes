from flask_login import current_user
from flask import current_app
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab import rl_config

rl_config.renderPMBackend = 'PIL'

from pathlib import Path
from io import BytesIO
from datetime import datetime
import json, math


def draw_header(c, width, height, client, dates):
    logo_path = Path(current_app.root_path).resolve().parent / "docs" / str(current_user.company_id) / 'reports' / 'logo.png'
    print(f'logo path: {logo_path}')
    try:
        c.drawImage(
            logo_path,
            40,
            height - 75,
            width=120,
            height=65,
            preserveAspectRatio=True,
            mask='auto'
        )
    except:
        print('in pass for draw logo')
        pass

    text_start = 200
    
    # title
    c.setFont("Helvetica-Bold", 12)
    c.drawString(text_start, height - 25, f'CLIENT SIGNATURE SHEET - {dates[0]} to {dates[1]}')

    # divider line
    c.setLineWidth(0.5)
    c.line(40, height - 80, width - 40, height - 80)

    # client info
    c.setFont("Helvetica", 10)
    c.drawString(text_start, height - 40, f"Client: {client.full_name}")
    c.drawString(text_start, height - 55, f"UCI No.: {client.uci_id}")
    c.drawString(text_start, height - 70, f"Caretaker: {client.care_giver}")


def draw_table_header(c, y, col_positions):

    c.setFont("Helvetica-Bold", 10)

    c.drawString(col_positions[0] + 5, y, "Appt Time")
    c.drawCentredString((col_positions[1] + col_positions[2]) / 2, y, "Caretaker Signature")
    c.drawCentredString((col_positions[2] + col_positions[3]) / 2, y, "Therapist")
    # c.drawCentredString((col_positions[3] + col_positions[4]) / 2, y, "Therapist")

    c.setLineWidth(0.5)
    c.line(40, y - 5, col_positions[-1], y - 5)


def draw_signature(c, strokes, x, y, w, h, orig_w, orig_h):
    if not strokes:
        return

    scale = min(w / orig_w, h / orig_h)

    offset_x = x + (w - orig_w * scale) / 2
    offset_y = y + (h - orig_h * scale) / 2

    c.setLineWidth(1)

    for stroke in strokes:
        points = stroke.get("points", [])
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            c.line(
                p1["x"] * scale + offset_x,
                (orig_h - p1["y"]) * scale + offset_y,
                p2["x"] * scale + offset_x,
                (orig_h - p2["y"]) * scale + offset_y,
            )


def draw_footer(c, width, page_num, total_pages):
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 20, f"Page {page_num} of {total_pages}")
    

def parse_strokes(strokes):
    
    if isinstance(strokes, str):
        try:
            strokes = json.loads(strokes)
        except:
            strokes = []

    return [
        {"points": s} if isinstance(s, list) else s
        for s in (strokes or [])
    ]


def create_signatures_pdf(appts):

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    width, height = letter

    margin_left = 40
    margin_right = 40
    usable_width = width - margin_left - margin_right

    # columns (balanced visually)
    col_widths = [
        usable_width * 0.30,
        usable_width * 0.20,
        usable_width * 0.20,
        usable_width * 0.30,
    ]

    col_positions = [
        margin_left,
        margin_left + col_widths[0],
        margin_left + col_widths[0] + col_widths[1],
        margin_left + col_widths[0] + col_widths[1] + col_widths[2],
        margin_left + usable_width
    ]


    client = appts[0].client
    dates = [appts[0].start_datetime.strftime('%m/%d/%Y'), appts[-1].start_datetime.strftime('%m/%d/%Y')]

    def new_page():
        nonlocal page_num

        draw_footer(c, width, page_num, total_pages)
        c.showPage()
        page_num += 1

        draw_header(c, width, height, client, dates)

        y = height - 90
        draw_table_header(c, y, col_positions)

        return y

    # first page
    draw_header(c, width, height, client, dates)

    y = height - 90
    draw_table_header(c, y, col_positions)
    # y -= 20
    
    row_height = 50
    page_num = 1
    total_pages = math.ceil(len(appts)/13)
    padding = row_height/10
    
    for appt in appts:
        if y < 100:
            y = new_page()
        
        y -= row_height
        # timestamp
        c.setFont("Helvetica", 9)
        c.drawString(
            col_positions[0] + 5,
            y + row_height/2 - padding,
            f'{appt.start_datetime.strftime("%m/%d/%Y %I:%M %p")} - {appt.end_datetime.strftime("%I:%M %p")}'
        )


        if appt.signature:
            client_strokes = parse_strokes(appt.signature.strokes)
            # client signature
            draw_signature(
                c,
                client_strokes,
                col_positions[1] + padding,
                y + padding,
                col_widths[1] - padding * 2,
                row_height - padding * 2,
                appt.signature.canvas_width or 1,
                appt.signature.canvas_height or 1
            )

        therapist_strokes = parse_strokes(appt.therapist.strokes) if appt.therapist.strokes else []
        # therapist signature
        draw_signature(
            c,
            therapist_strokes,
            col_positions[2] + padding,
            y + padding,
            col_widths[2] - padding * 2,
            row_height - padding * 2,
            appt.therapist.canvas_width or 1,
            appt.therapist.canvas_height or 1
        )

        c.drawString(
            col_positions[3] + 5,
            y + row_height/2 - padding,
            appt.therapist.name
        )
        
        c.line(margin_left, y, width - margin_right, y)

    draw_footer(c, width, page_num, total_pages)

    c.save()
    buffer.seek(0)
    return buffer

