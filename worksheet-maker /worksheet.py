import json
import os

import fitz

from CPAPERS.helpers import parse_filename, parse_syllabus_string, format_id
from helpers import create_exam_page_fitz

c1 = r"C:/Users/HP/PycharmProjects/obi-wan/9709/9709-P3-Captures/9709_w25_qp_32/1.a.pdf"
c2 = r"C:/Users/HP/PycharmProjects/obi-wan/9709/9709-P3-Captures/9709_w25_qp_32/1.b.pdf"


def create_page(page_number, barcode_data, bottom_text, sections):
    page = create_exam_page_fitz(
        barcode_value=barcode_data,
        page_no=page_number,
        left_text=bottom_text
    )

    y_coordinate = 60
    for section in sections:
        # section PDF
        insert_doc = fitz.open(section)
        insert_page = insert_doc.load_page(0)

        insert_rect = insert_page.rect
        x_coordinate = (page.rect.width - insert_rect.width) / 2

        target_rect = fitz.Rect(
            x_coordinate,
            y_coordinate,
            x_coordinate + insert_rect.width,
            y_coordinate + insert_rect.height
        )

        # Show the PDF page on the main page at the specified location
        page.show_pdf_page(target_rect, insert_doc, 0)
        insert_doc.close()
        y_coordinate += insert_rect.height

    return page
    # page.parent.save("output.pdf")
    # page.parent.close()

def assign_parts(capture_dir: str, questions):
    raw_data = []
    for question in questions:
        try:
            paper, question_number = question.split(':')
            parts = [
                i for i in os.listdir(
                    os.path.join(capture_dir, paper)
                ) if question_number == i.split('.')[0]
            ]
            raw_data.append(
                {
                    "id": question,
                    "paper": paper,
                    "question_number": question_number,
                    "parts": parts
                }
            )
        except:
            pass
    return raw_data

def assign_pages(capture_dir: str, parts_structure):
    # Usable space within a page
    bbox_limit = fitz.Rect(38.267, 55, 557, 790.87)

    # master data
    master = []

    # Loop through each question
    for question in parts_structure:
        # Pages the whole question will occupy
        pages = {
            "0": [],
            "1": [],
        }

        # part numbers in hierarchical order
        part_ordered = sorted(question['parts'], key=parse_filename)

        # Vertical room on a blank page
        fixed_vertical_room = bbox_limit.y1 - bbox_limit.y0

        # vertical room on current page
        vertical_room = fixed_vertical_room

        current_page = 0

        # loop through each part
        for part in part_ordered:

            # open the pdf for that part
            with fitz.open(os.path.join(capture_dir, question['paper'], part)) as part_pdf:
                # load the page and get its rect
                part_page = part_pdf.load_page(0)
                part_rect = part_page.rect

                # if question fits on current page, remove used space from vertical room and proceed
                if vertical_room >= part_rect.height:
                    vertical_room -= part_rect.height

                # if question does not fit on current page, go to next page and reset vertical room
                else:
                    current_page += 1
                    vertical_room = fixed_vertical_room

                # add content to correct page
                pages[str(current_page)].append({
                    "paper": question['paper'],
                    "part": part,

                })
        master.append({
            "id": question['id'],
            "paper": question['paper'],
            "question_number": question['question_number'],
            "parts": question['parts'],
            "regions_with_pages": pages
        })

    return master

def create_regions(questions_with_pages):
    questions_with_pages.sort(key=lambda x: parse_syllabus_string(x['id']), reverse=True)

    worksheet = []
    current_page = 1
    for question in questions_with_pages:
        question_spans_two_pages = len(question['regions_with_pages']['1']) > 0

        if not question_spans_two_pages:
            worksheet.append({
                "page_no": current_page,
                "id": question['id'],
                "paper": question['paper'],
                "question_number": question['question_number'],

                "insert_pages": question['regions_with_pages']['0']
            })
            current_page += 1
        else:
            if current_page % 2 != 0:
                current_page += 1
            worksheet.append({
                "page_no": current_page,
                "id": question['id'],
                "paper": question['paper'],
                "question_number": question['question_number'],

                "insert_pages": question['regions_with_pages']['0']
            })
            current_page += 1
            worksheet.append({
                "page_no": current_page,
                "id": question['id'],
                "paper": question['paper'],
                "question_number": question['question_number'],

                "insert_pages": question['regions_with_pages']['1']
            })
            current_page += 1

    blank_pages = []
    for i, w in enumerate(worksheet):
        if i != len(worksheet)-1 and (int(worksheet[i+1]['page_no']) - int(w['page_no']) != 1):
            blank_pages.append({'id': 'blank_page', 'page_no': int(w['page_no'])+1})
    worksheet.extend(blank_pages)
    worksheet.sort(key=lambda x: x['page_no'])

    return worksheet

def create_worksheet(capture_dir: str, worksheet_data, save_file, sy, pp, tp, stp):
    worksheet = fitz.open()
    for i, page_data in enumerate(worksheet_data):
        if page_data['id'] != 'blank_page':
            # 9709_w24_qp_12
            mapping = {
                "m":1,
                "s":2,
                "w":3
            }
            insert_page = create_page(
                page_number=page_data['page_no'],
                barcode_data=format_id(sy,mapping[page_data['paper'][5]],int(page_data['paper'][6:8]),int(page_data['paper'][12:]),int(page_data['question_number']),page_data['page_no']),
                bottom_text=page_data['id'],
                sections=[os.path.join(capture_dir, i['paper'], i['part']) for i in page_data['insert_pages']]
            )
        else:
            insert_page = create_page(
                page_number=page_data['page_no'],
                barcode_data=format_id(0,0,0,0,0,page_data['page_no']),
                bottom_text="BLANK PAGE",
                sections=[]
            )
        worksheet.insert_pdf(
            insert_page.parent,
            from_page=0,
            to_page=i
        )
    worksheet.save(save_file)
if __name__ == "__main__":
    JSON_INDEX = r'C:\Users\HP\PycharmProjects\obi-wan\9709\cpapers/P3/complex_numbers.json'
    CAPTURE_DIR = r"C:\Users\HP\PycharmProjects\obi-wan\9709\9709-P3-Captures"
    OUTPUT_PDF_FILE = "complex_numbers_worksheet.pdf"

    SYLLABUS = 3
    SERIES = 3
    TOPIC = 11
    SUBTOPIC = 1


    # Return an XYAABBCCDDD string:
    #   - X: syllabus (0–9), zero-padded to 1 digit
    #   - Y: paper (0–9), zero-padded to 1 digit
    #   - AA: topic (0–99), zero-padded to 2 digits
    #   - BB: subtopic (0–99), zero-padded to 2 digits
    #   - CC: question (0–99), zero-padded to 2 digits
    #   - DDD: page (0–999), zero-padded to 3 digits

    with open(JSON_INDEX) as f:
        question_data = json.load(f)
        assigned_parts = assign_parts(CAPTURE_DIR, question_data)
        assigned_pages = assign_pages(CAPTURE_DIR, assigned_parts)
        worksheet_regions = create_regions(assigned_pages)
        create_worksheet(CAPTURE_DIR, worksheet_regions, OUTPUT_PDF_FILE, SYLLABUS, SERIES, TOPIC, SUBTOPIC)



