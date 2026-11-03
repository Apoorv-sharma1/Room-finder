# pyrefly: ignore [missing-import]
import pdfplumber
import re
import json
import os

ROOM_REGEX = re.compile(
    r'\b(EB\d-\d+|TB-\d+(?:/\d+)?|TB\d+|LRC\d+|NF\d-[A-Z]+|IET\s+Amphitheatre|IET\s+Amphi|BYOD|NF1-CSE|NF2-MATHS)\b',
    re.IGNORECASE
)

TEACHER_PREFIX_REGEX = re.compile(
    r'\b(?:Dr\.|Mr\.|Ms\.|Mrs\.|DR\.|MR\.|MS\.|MRS\.)\s+([^()\n\r-]*?)(?=\s*(?:\(|-|\n|$|\b(?:Dr\.|Mr\.|Ms\.|Mrs\.|DR\.|MR\.|MS\.|MRS\.)\b))',
    re.IGNORECASE
)

DAYS_OF_WEEK = ["MON", "TUE", "WED", "THU", "FRI"]

def standardize_time_slot(slot_str):
    slot_str = slot_str.lower().replace(" ", "")
    match = re.match(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*(am|pm)?', slot_str)
    if not match:
        return slot_str
    
    h1, m1, h2, m2, ampm = match.groups()
    h1 = int(h1)
    h2 = int(h2)
    
    if not ampm:
        if h1 >= 9 and h1 < 12:
            ampm = "am"
        else:
            ampm = "pm"
            
    ampm_upper = ampm.upper()
    return f"{h1:02d}:{m1} - {h2:02d}:{m2} {ampm_upper}"

def parse_cell_text(text, default_room):
    text = text.strip()
    if not text:
        return None
    
    # Standardize spaces and lines
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.replace('\u2013', '-').replace('\u2010', '-').replace('\ufffd', '-')
    
    # Identify room
    room = default_room
    room_match = ROOM_REGEX.search(text)
    if room_match:
        room = room_match.group(1).strip().upper()
        # Remove the room text and any leading/trailing dashes/spaces around it
        span = room_match.span()
        before = text[:span[0]].rstrip(" -")
        after = text[span[1]:].lstrip(" -")
        text_clean = (before + " " + after).strip()
    else:
        text_clean = text

    # Remove extra spaces
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()
    
    # Simple labels
    if text_clean.lower() in ["coding hours", "project based learning", "lunch", "library"]:
        return {
            "course_name": text_clean,
            "course_code": "",
            "teachers": [],
            "type": "",
            "room": room or "N/A",
            "raw": text
        }

    # Find course code in parentheses
    course_code = ""
    course_name = ""
    code_match = re.search(r'\(([A-Z]{2,4}\d{4}|\s*)\)', text_clean)
    if code_match:
        course_code = code_match.group(1).strip()
        course_part = text_clean[:code_match.start()].strip()
        teacher_part = text_clean[code_match.end():].strip()
        course_name = course_part
    else:
        # Fallback split by lines
        parts = text.split('\n')
        if len(parts) >= 2:
            course_name = parts[0].strip()
            teacher_part = parts[1].strip()
        else:
            course_name = text_clean
            teacher_part = ""

    # Parse teachers
    teachers = []
    # Try using prefix regex on the entire cell text or teacher part
    teachers = []
    for match in TEACHER_PREFIX_REGEX.finditer(text):
        name = match.group(1).strip(" -/,\t")
        if name:
            # Capitalize properly
            name = " ".join([w.capitalize() if w.isupper() or w.islower() else w for w in name.split()])
            teachers.append(name)
            
    # Class type is usually in parentheses at the end, e.g. (L) or (P - A2) or (T-A1) or (P)
    class_type = ""
    type_match = re.search(r'\((L|P|T|P\s*-\s*[A-Z0-9]+|T\s*-\s*[A-Z0-9]+)\)', text, re.IGNORECASE)
    if type_match:
        class_type = type_match.group(1).strip()

    return {
        "course_name": course_name.strip(),
        "course_code": course_code.strip(),
        "teachers": teachers,
        "type": class_type.strip(),
        "room": room or "N/A",
        "raw": text
    }

def get_slot_ranges_on_page(page, table_obj):
    slot_ranges = []
    for cell in table_obj.cells:
        x0, y0, x1, y1 = cell
        try:
            cropped = page.crop((x0, y0, x1, y1))
            text = cropped.extract_text()
        except Exception:
            continue
        if text:
            clean_text = text.replace('\n', ' ').strip()
            match = re.search(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*(?:am|pm)?', clean_text, re.IGNORECASE)
            if match:
                slot_str = match.group(0).lower().replace(" ", "")
                standard_slot = standardize_time_slot(slot_str)
                slot_ranges.append({
                    "name": standard_slot,
                    "x0": x0,
                    "x1": x1
                })
    
    unique = {}
    for s in slot_ranges:
        name = s["name"]
        if name not in unique:
            unique[name] = s
        else:
            unique[name]["x0"] = min(unique[name]["x0"], s["x0"])
            unique[name]["x1"] = max(unique[name]["x1"], s["x1"])
            
    return list(unique.values())

def get_section_info(rows, r_idx, c_idx, next_sec_row):
    texts = []
    for i in range(r_idx, min(r_idx + 6, next_sec_row)):
        val = rows[i][c_idx]
        if val:
            # If it's a day row, stop
            if rows[i][0] in DAYS_OF_WEEK:
                break
            texts.append(str(val).strip())
            
    joined = " ".join(texts)
    
    # Parse section name, e.g. "Sec A" or "Sec D (CSAI)"
    sec_match = re.search(r'\bSec\s+([A-J])\b', joined, re.IGNORECASE)
    section_letter = sec_match.group(1).upper() if sec_match else None
    
    # Some tables have longer section descriptions like "Sec D (CSAI)" or "Sec F (EC)"
    desc_match = re.search(r'\bSec\s+[A-J]\s*(\([A-Z\s]+\))', joined, re.IGNORECASE)
    section_desc = desc_match.group(1).strip() if desc_match else ""
    
    if section_letter:
        section_name = f"Sec {section_letter}"
        if section_desc:
            section_name += f" {section_desc}"
    else:
        # Fallback to whatever matches Sec
        fallback_match = re.search(r'\b(Sec\s+\w+)', joined, re.IGNORECASE)
        section_name = fallback_match.group(1).strip() if fallback_match else "Unknown Sec"
        
    room_match = ROOM_REGEX.search(joined)
    default_room = room_match.group(1).upper() if room_match else None
    
    return section_name, default_room

def main():
    database = []
    
    pdf_files = [
        {"name": "Time Table 1st Sem.pdf", "sem": "1st Sem"},
        {"name": "Time Table 3rd sem.pdf", "sem": "3rd Sem"},
        {"name": "Time Table-5th Sem.pdf", "sem": "5th Sem"}
    ]
    
    for pdf_info in pdf_files:
        pdf_name = pdf_info["name"]
        semester = pdf_info["sem"]
        print(f"Parsing {pdf_name} ({semester})...")
        
        if not os.path.exists(pdf_name):
            print(f"Error: {pdf_name} not found.")
            continue
            
        with pdfplumber.open(pdf_name) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                tables = page.find_tables()
                if not tables:
                    print(f"  Page {page_idx+1}: No tables found")
                    continue
                t = tables[0]
                rows = t.extract()
                
                # 1. Get slot ranges for this page
                slots = get_slot_ranges_on_page(page, t)
                print(f"  Page {page_idx+1}: Found {len(slots)} slots: {[s['name'] for s in slots]}")
                
                # 2. Find section header rows
                sec_headers = []
                for r_idx, row in enumerate(rows):
                    # Check first two columns for section marker
                    found_sec = False
                    for c_idx in range(min(2, len(row))):
                        val = row[c_idx]
                        if val and re.search(r'\bSec\s+[A-J]\b', str(val), re.IGNORECASE):
                            sec_headers.append((r_idx, c_idx))
                            found_sec = True
                            break
                            
                print(f"  Page {page_idx+1}: Found {len(sec_headers)} sections")
                
                # Process each section
                for idx, (sec_row, sec_col) in enumerate(sec_headers):
                    next_sec_row = sec_headers[idx+1][0] if idx + 1 < len(sec_headers) else len(rows)
                    
                    section_name, default_room = get_section_info(rows, sec_row, sec_col, next_sec_row)
                    print(f"    Section: {section_name}, Default Room: {default_room}")
                    
                    # Inside this section, locate Day rows
                    day_rows = []
                    for r in range(sec_row, next_sec_row):
                        # Day name is usually in col 0 (or col 1 if col 0 is empty)
                        day_name = None
                        for c in range(min(2, len(rows[r]))):
                            val = rows[r][c]
                            if val and str(val).strip() in DAYS_OF_WEEK:
                                day_name = str(val).strip()
                                break
                        if day_name:
                            day_rows.append((day_name, r))
                            
                    # Process each day
                    for d_idx, (day_name, day_start) in enumerate(day_rows):
                        day_end = day_rows[d_idx+1][1] if d_idx + 1 < len(day_rows) else next_sec_row
                        
                        # Gather all rows for this day
                        day_subrows = list(range(day_start, day_end))
                        
                        # Process column by column
                        for c_idx in range(len(t.columns)):
                            col_obj = t.columns[c_idx]
                            col_x0, col_x1 = col_obj.bbox[0], col_obj.bbox[2]
                            mid_x = (col_x0 + col_x1) / 2.0
                            
                            # Find which slots this column belongs to
                            matching_slots = []
                            for slot in slots:
                                if slot["x0"] <= mid_x <= slot["x1"]:
                                    matching_slots.append(slot["name"])
                                    
                            if not matching_slots:
                                continue
                                
                            # Combine vertical subrows for this column
                            cell_parts = []
                            for r in day_subrows:
                                val = rows[r][c_idx]
                                if val:
                                    # Skip day name and section name cells
                                    if str(val).strip() in DAYS_OF_WEEK:
                                        continue
                                    if re.search(r'\bSec\s+[A-J]\b', str(val), re.IGNORECASE):
                                        continue
                                    cell_parts.append(str(val).strip())
                                    
                            cell_text = "\n".join(cell_parts).strip()
                            if not cell_text:
                                continue
                                
                            # Parse class details
                            parsed = parse_cell_text(cell_text, default_room)
                            if parsed:
                                for slot_name in matching_slots:
                                    entry = {
                                        "semester": semester,
                                        "section": section_name,
                                        "day": day_name,
                                        "time_slot": slot_name,
                                        "course_name": parsed["course_name"],
                                        "course_code": parsed["course_code"],
                                        "teachers": parsed["teachers"],
                                        "type": parsed["type"],
                                        "room": parsed["room"] or default_room or "N/A"
                                    }
                                    # Deduplicate
                                    if entry not in database:
                                        database.append(entry)

    # Save to timetable_data.js
    with open("timetable_data.js", "w", encoding="utf-8") as f:
        f.write("// Auto-generated B.Tech Timetable Database\n")
        f.write("const TIMETABLE_DATA = ")
        json.dump({"classes": database}, f, indent=2, ensure_ascii=False)
        f.write(";\n")
        
    print(f"Successfully generated timetable_data.js with {len(database)} entries!")

if __name__ == "__main__":
    main()
