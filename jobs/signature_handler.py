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
    c.setFont("Helvetica-Bold", 10)
    c.drawString(text_start, height - 40, f"Client: {client.full_name}")
    c.setFont("Helvetica", 10)
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


# def draw_signature(c, strokes, x, y, w, h, orig_w, orig_h):
#     if not strokes:
#         return

#     scale = min(w / orig_w, h / orig_h)

#     offset_x = x + (w - orig_w * scale) / 2
#     offset_y = y + (h - orig_h * scale) / 2

#     c.setLineWidth(1)

#     for stroke in strokes:
#         points = stroke.get("points", [])
#         for i in range(len(points) - 1):
#             p1 = points[i]
#             p2 = points[i + 1]

#             c.line(
#                 p1["x"] * scale + offset_x,
#                 (orig_h - p1["y"]) * scale + offset_y,
#                 p2["x"] * scale + offset_x,
#                 (orig_h - p2["y"]) * scale + offset_y,
#             )


def compute_velocity(p0, p1):
    dx = p1["x"] - p0["x"]
    dy = p1["y"] - p0["y"]
    dt = max((p1.get("time", 0) - p0.get("time", 0)), 1)

    return (dx**2 + dy**2)**0.5 / dt


            
def draw_signature_bezier(c, strokes, x, y, w, h):
    c.setLineJoin(1)
    c.setLineCap(1)

    for stroke in strokes:
        if len(stroke) < 2:
            continue

        for i in range(len(stroke['points']) - 1):
            p0 = stroke['points'][i]
            p1 = stroke['points'][i + 1]

            x0 = x + p0["x"] * w
            y0 = y + p0["y"] * h
            x1 = x + p1["x"] * w
            y1 = y + p1["y"] * h

            # flip Y (PDF coords)
            y0 = y + h - (y0 - y)
            y1 = y + h - (y1 - y)

            # control point (midpoint smoothing)
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2

            # velocity → line width
            velocity = compute_velocity(p0, p1)
            line_width = max(0.8, 2.5 - velocity * 1500)
            c.setLineWidth(line_width)

            path = c.beginPath()
            path.moveTo(x0, y0)

            # quadratic approximation using cubic curve
            path.curveTo(x0, y0, cx, cy, x1, y1)

            c.drawPath(path)


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


def normalize_strokes(strokes_input):
 
    raw_strokes = parse_strokes(strokes_input)
 
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")
    
    for stroke in raw_strokes:
        for p in stroke['points']:
            x, y = p["x"], p["y"]

            if x < min_x: min_x = x
            if y < min_y: min_y = y
            if x > max_x: max_x = x
            if y > max_y: max_y = y

    width = max_x - min_x
    height = max_y - min_y

    # Match JS behavior exactly
    if width == 0:
        width = 1
    if height == 0:
        height = 1

    strokes = []
    
    for stroke in raw_strokes:
        new_stroke = {'dotSize': stroke.get('dotSize', 0),
                    'minWidth': stroke.get('minWidth', 0.5),
                    'maxWidth': stroke.get('maxWidth', 2.5),
                    'penColor': stroke.get('penColor', 'black'),
                    'points': []}
        
        for p in stroke['points']:
            new_stroke['points'].append({
                "x": (p["x"] - min_x) / width,
                "y": (p["y"] - min_y) / height,
                "pressure": p.get("pressure", 0.5),
                "time": p.get("time")
            })
        strokes.append(new_stroke)

    return strokes


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
        
        y -= row_height + padding
        # timestamp
        c.setFont("Helvetica", 9)
        c.drawString(
            col_positions[0] + 5,
            y + row_height/2 - padding,
            f'{appt.start_datetime.strftime("%m/%d/%Y %I:%M %p")} - {appt.end_datetime.strftime("%I:%M %p")}'
        )


        if appt.signature:
            # client signature
            draw_signature_bezier(
                c,
                appt.signature.normalized_strokes,
                col_positions[1] + padding,
                y + padding,
                col_widths[1] - padding * 2,
                row_height - padding * 2
            )

        # therapist signature
        draw_signature_bezier(
            c,
            appt.therapist.normalized_strokes,
            col_positions[2] + padding,
            y + padding,
            col_widths[2] - padding * 2,
            row_height - padding * 2
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

