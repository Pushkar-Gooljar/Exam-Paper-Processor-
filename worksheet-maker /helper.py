import io
import fitz  # PyMuPDF
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def create_exam_page_fitz(barcode_value, page_no, left_text, font_path="Code39.ttf"):
    # 1. Setup In-Memory Buffer
    packet = io.BytesIO()

    # Create the ReportLab canvas using the buffer instead of a filename
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4

    # 2. Register Barcode Font
    barcode_font_name = "Helvetica"  # Fallback
    if os.path.exists(font_path):
        try:
            # check if font is already registered to avoid error on multiple calls
            if 'BarcodeFont' not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont('BarcodeFont', font_path))
            barcode_font_name = 'BarcodeFont'
        except Exception as e:
            print(f"Error loading font: {e}")
    else:
        print(f"Warning: '{font_path}' not found. Using standard text.")

    # 3. Draw Corner Markers (Logic unchanged)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(2.8346)
    c.setLineCap(2)

    def invert_point(x, y):
        return x, height - y

    # --- Top Right Corner ---
    p1 = invert_point(558.425, 31.181)
    p2 = invert_point(558.425, 51.023)
    c.line(p1[0], p1[1], p2[0], p2[1])
    p1 = invert_point(537.165, 31.181)
    p2 = invert_point(557.007, 31.181)
    c.line(p1[0], p1[1], p2[0], p2[1])

    # --- Top Left Corner ---
    p1 = invert_point(38.267, 31.181)
    p2 = invert_point(58.110, 31.181)
    c.line(p1[0], p1[1], p2[0], p2[1])
    p1 = invert_point(36.850, 51.023)
    p2 = invert_point(36.850, 31.181)
    c.line(p1[0], p1[1], p2[0], p2[1])

    # --- Bottom Right Corner ---
    p1 = invert_point(558.425, 810.708)
    p2 = invert_point(558.425, 790.866)
    c.line(p1[0], p1[1], p2[0], p2[1])
    p1 = invert_point(537.165, 810.708)
    p2 = invert_point(557.007, 810.708)
    c.line(p1[0], p1[1], p2[0], p2[1])

    # --- Bottom Left Corner ---
    p1 = invert_point(38.267, 810.708)
    p2 = invert_point(58.110, 810.708)
    c.line(p1[0], p1[1], p2[0], p2[1])
    p1 = invert_point(36.850, 790.866)
    p2 = invert_point(36.850, 810.708)
    c.line(p1[0], p1[1], p2[0], p2[1])

    # 4. Draw Barcode
    c.setFillColorRGB(0, 0, 0)
    barcode_string = f"*{barcode_value}*"
    barcode_x = 75
    barcode_y = height - 55

    c.setFont(barcode_font_name, 36)
    c.drawString(barcode_x, barcode_y, barcode_string)

    c.setFont("Helvetica", 10)
    formatted_text = f"* {barcode_value} *"
    c.drawString(barcode_x, barcode_y+25, formatted_text)

    # 5. Draw Footer
    c.setFont("Helvetica", 8)
    c.drawString(50, 40, left_text)

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, 35, str(page_no))

    # 6. Finalize ReportLab to Buffer
    c.save()

    # Reset buffer position to the beginning
    packet.seek(0)

    # 7. Open with PyMuPDF (Fitz)
    # Open the PDF from the memory bytes
    doc = fitz.open("pdf", packet)

    # Get the specific page (there is only 1 page created)
    page = doc.load_page(0)

    # Return the fitz Page object
    # Note: Keep 'doc' in memory if you plan to use 'page' outside this function scope,
    # though usually returning the page keeps the doc reference alive in Python.
    return page


# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    # Create the page in memory
    fitz_page = create_exam_page_fitz(
        barcode_value="000",
        page_no=1,
        left_text="Exam Copy 2024"
    )


    print(f"Type of object returned: {type(fitz_page)}")

    # Draw a red rectangle covering the specified bbox
    rect = fitz.Rect(38.267, 55, 557, 790.87)
    fitz_page.draw_rect(rect, color=(1, 0, 0), width=2)

    # Proof: Save it to a file using PyMuPDF to show it works
    # We need the parent document to save
    fitz_page.parent.save("final_fitz_output.pdf")
    print("Saved 'final_fitz_output.pdf' via PyMuPDF.")


def parse_filename(filename):
    """
    Parse filename like '1.a.ii.pdf' into sortable components.
    Returns a tuple of comparable values.
    """
    # Remove .pdf extension
    name = filename.replace('.pdf', '')

    # Split by dots
    parts = name.split('.')

    result = []
    for part in parts:
        # Check if it's a number
        if part.isdigit():
            result.append((0, int(part)))  # (type, value) - numbers come first
        # Check if it's lowercase letters (a, b, c, etc.)
        elif part.isalpha() and part.islower():
            result.append((1, part))  # letters come second
        # Check if it's Roman numerals
        elif part in ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x',
                      'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii', 'xviii', 'xix', 'xx']:
            # Convert Roman to integer for proper sorting
            roman_map = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
                         'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10,
                         'xi': 11, 'xii': 12, 'xiii': 13, 'xiv': 14, 'xv': 15,
                         'xvi': 16, 'xvii': 17, 'xviii': 18, 'xix': 19, 'xx': 20}
            result.append((2, roman_map.get(part, 0)))  # Roman numerals come third
        else:
            result.append((3, part))  # anything else comes last

    return result


def parse_syllabus_string(s):
    """
    Parse string like '9709_s25_qp_35:5' into sortable components.
    Returns tuple: (year, paper, series_priority, question)
    """
    # Split by underscore and colon
    parts = s.split('_')

    # Extract components
    # parts[0] = syllabus code (e.g., '9709')
    # parts[1] = series + year (e.g., 's25')
    # parts[2] = 'qp'
    # parts[3] = paper + ':' + question (e.g., '35:5')

    series_year = parts[1]
    series = series_year[0]  # 's', 'm', or 'w'
    year = int(series_year[1:])  # '25' -> 25

    paper_question = parts[3].split(':')
    paper = int(paper_question[0])  # '35' -> 35
    question = int(paper_question[1])  # '5' -> 5

    # Series priority: m=0, s=1, w=2
    series_priority = {'m': 0, 's': 1, 'w': 2}.get(series, 3)

    return (year, paper, series_priority, question)


def format_id(syllabus: int, paper: int, topic: int, subtopic: int, question: int, page: int) -> str:
    """
    Return an XYAABBCCDDD string:
      - X: syllabus (0–9), zero-padded to 1 digit
      - Y: paper (0–9), zero-padded to 1 digit
      - AA: topic (0–99), zero-padded to 2 digits
      - BB: subtopic (0–99), zero-padded to 2 digits
      - CC: question (0–99), zero-padded to 2 digits
      - DDD: page (0–999), zero-padded to 3 digits
    """
    if not (0 <= syllabus <= 9):
        raise ValueError("syllabus must be between 0 and 9")
    if not (0 <= paper <= 9):
        raise ValueError("paper must be between 0 and 9")
    if not (0 <= topic <= 99):
        raise ValueError("topic must be between 0 and 99")
    if not (0 <= subtopic <= 99):
        raise ValueError("subtopic must be between 0 and 99")
    if not (0 <= question <= 99):
        raise ValueError("question must be between 0 and 99")
    if not (0 <= page <= 999):
        raise ValueError("page must be between 0 and 999")

    return f"{syllabus:01d}{paper:01d}{topic:02d}{subtopic:02d}{question:02d}{page:03d}"
