import streamlit as st
import json
import re
import os

# Set page configuration
st.set_page_config(
    page_title="JKLU SmartSchedule",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS styling (clean minimal design with blue and golden yellow accents)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main container background */
    .stApp {
        background: #ffffff;
        color: #0f172a;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: #0f172a !important;
        border-right: none;
    }
    section[data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    /* Header and branding */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 2rem;
        background: rgba(255, 255, 255, 0.03);
        padding: 12px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .logo-icon {
        background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
        width: 40px;
        height: 40px;
        border-radius: 8px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 20px;
        color: #0f172a !important;
    }
    .logo-text h1 {
        font-size: 1.35rem !important;
        margin: 0 !important;
        background: linear-gradient(135deg, #ffffff 0%, #fef08a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
    }
    .logo-text p {
        font-size: 0.75rem !important;
        margin: 0 !important;
        color: #94a3b8 !important;
    }
    
    /* Metric cards styling */
    .status-summary {
        display: flex;
        gap: 16px;
        margin-bottom: 1.5rem;
    }
    .summary-card {
        flex: 1;
        background: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .summary-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.05);
    }
    .summary-num {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 2px;
    }
    .free-glow {
        color: #ca8a04; /* Gold */
    }
    .busy-glow {
        color: #1d4ed8; /* Blue */
    }
    .summary-lbl {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Room grid and cards */
    .rooms-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 14px;
        margin-top: 1rem;
    }
    .room-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
        transition: all 0.2s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .room-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
        border-color: #cbd5e1;
    }
    .room-card.status-free {
        border-top: 3px solid #eab308; /* Gold border */
    }
    .room-card.status-busy {
        border-top: 3px solid #2563eb; /* Blue border */
    }
    .room-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .room-name {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
    }
    .status-badge {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .status-badge.free {
        background: #fef9c3; /* Light gold */
        color: #854d0e;
    }
    .status-badge.busy {
        background: #dbeafe; /* Light blue */
        color: #1e40af;
    }
    .room-details {
        font-size: 0.8rem;
        color: #64748b;
    }
    .room-details-title {
        font-weight: 600;
        margin-bottom: 4px;
        font-size: 0.85rem;
    }
    .meta-item {
        margin-top: 3px;
        display: flex;
        align-items: center;
        gap: 5px;
        color: #64748b;
    }
    
    /* Table styles for timetable */
    .table-container {
        overflow-x: auto;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
        margin-top: 1rem;
        background: #ffffff;
    }
    table.weekly-table {
        width: 100%;
        border-collapse: collapse;
        text-align: left;
        background: #ffffff;
    }
    table.weekly-table th {
        background: #f8fafc;
        color: #475569;
        font-weight: 700;
        padding: 12px;
        border-bottom: 2px solid #e2e8f0;
        font-size: 0.85rem;
    }
    table.weekly-table td {
        padding: 12px;
        border-bottom: 1px solid #f1f5f9;
        color: #64748b;
        font-size: 0.8rem;
        vertical-align: top;
    }
    table.weekly-table tr:hover {
        background: #fafafb;
    }
    table.weekly-table td:first-child {
        font-weight: 700;
        color: #0f172a;
        background: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    .table-cell-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.01);
    }
    .cell-subject {
        color: #0f172a;
        font-weight: 700;
        display: block;
        margin-bottom: 2px;
        font-size: 0.85rem;
    }
    .cell-code {
        color: #2563eb;
        font-size: 0.7rem;
        font-weight: 600;
        display: block;
    }
    .cell-meta {
        display: flex;
        justify-content: space-between;
        margin-top: 6px;
        font-size: 0.7rem;
        color: #64748b;
    }
    .cell-room {
        color: #b45309; /* Gold/Amber */
        font-weight: 600;
    }
    .cell-free {
        color: #94a3b8;
        font-style: italic;
    }
    
    /* Teacher Finder Details */
    .teacher-status-card {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        align-items: center;
        justify-content: space-between;
    }
    .teacher-info-side {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .teacher-avatar {
        background: linear-gradient(135deg, #eab308 0%, #2563eb 100%);
        width: 44px;
        height: 44px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 18px;
        color: white !important;
    }
    .teacher-meta h2 {
        margin: 0;
        font-size: 1.25rem;
        color: #0f172a;
        font-weight: 700;
    }
    .teacher-meta p {
        margin: 2px 0 0 0;
        font-size: 0.8rem;
        color: #64748b;
    }
    .teacher-class-details {
        background: #f8fafc;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-top: 8px;
        width: 100%;
        color: #0f172a;
    }
</style>
""", unsafe_allow_html=True)


# Load timetable data
@st.cache_data
def load_timetable():
    file_path = "timetable_data.js"
    if not os.path.exists(file_path):
        return {"classes": []}
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract JSON part from JS assignment and clean/deduplicate
    try:
        json_start = content.find("{")
        json_str = content[json_start:]
        json_str = json_str.strip().rstrip(";")
        raw_data = json.loads(json_str)
        
        seen = set()
        deduped_classes = []
        for c in raw_data.get("classes", []):
            c["room"] = str(c.get("room", "")).strip().upper()
            c["semester"] = str(c.get("semester", "")).strip()
            c["section"] = str(c.get("section", "")).strip()
            c["day"] = str(c.get("day", "")).strip().upper()
            c["time_slot"] = str(c.get("time_slot", "")).strip()
            c["course_name"] = str(c.get("course_name", "")).strip()
            c["course_code"] = str(c.get("course_code", "")).strip().upper()
            c["type"] = str(c.get("type", "")).strip().upper()
            c["teachers"] = [str(t).strip() for t in c.get("teachers", []) if t]
            
            teachers_key = tuple(sorted(c["teachers"]))
            unique_key = (
                c["semester"], c["section"], c["day"], c["time_slot"],
                c["course_name"], c["course_code"], teachers_key, c["type"], c["room"]
            )
            if unique_key not in seen:
                seen.add(unique_key)
                deduped_classes.append(c)
                
        return {"classes": deduped_classes}
    except Exception as e:
        st.error(f"Error loading timetable data: {e}")
        return {"classes": []}

def clean_html(html_str):
    return "".join(line.strip() for line in html_str.splitlines())

data = load_timetable()
classes = data.get("classes", [])

# Helpers to extract master lists
def get_slot_minutes(slot):
    match = re.search(r'(\d{2}):(\d{2})\s*-\s*\d{2}:\d{2}\s*(AM|PM)', slot)
    if not match:
        return 0
    hr = int(match.group(1))
    minute = int(match.group(2))
    ampm = match.group(3)
    if ampm == 'PM' and hr != 12:
        hr += 12
    if ampm == 'AM' and hr == 12:
        hr = 0
    return hr * 60 + minute

all_rooms = sorted(list(set(
    c.get("room") for c in classes 
    if c.get("room") and c.get("room") not in ["N/A", "NONE", ""]
)))

all_slots = sorted(list(set(
    c.get("time_slot") for c in classes
)), key=get_slot_minutes)

all_teachers = sorted(list(set(
    t for c in classes for t in c.get("teachers", []) if t
)))

all_sems = sorted(list(set(
    c.get("semester") for c in classes if c.get("semester")
)))

# Sidebar controls for global Day & Time Slot
with st.sidebar:
    st.markdown("""
    <div class="logo-container">
        <div class="logo-icon">📅</div>
        <div class="logo-text">
            <h1>SmartSchedule</h1>
            <p>JK Lakshmipat University</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🕒 Quick Picker")
    day_options = {
        "MON": "Monday",
        "TUE": "Tuesday",
        "WED": "Wednesday",
        "THU": "Thursday",
        "FRI": "Friday"
    }
    selected_day = st.selectbox("Day", options=list(day_options.keys()), format_func=lambda x: day_options[x])
    
    default_slot_idx = 0
    if all_slots:
        selected_slot = st.selectbox("Time Slot", options=all_slots, index=default_slot_idx)
    else:
        selected_slot = None
        st.info("No time slots available in data.")
        
    st.markdown("---")
    st.caption("© 2026 JKLU SmartSchedule Dashboard. Fast & Offline.")

# Tabs
tab1, tab2, tab3 = st.tabs(["🚪 Room Locator", "🎓 Teacher Finder", "👥 Section Timetables"])

# ----------------- TAB 1: ROOM LOCATOR -----------------
with tab1:
    st.header("Room Locator")
    st.write(f"Showing room availability for **{day_options[selected_day]}** at **{selected_slot}**")
    
    # 1. Determine room occupations
    busy_rooms = {}
    if selected_slot:
        classes_at_time = [
            c for c in classes 
            if c.get("day") == selected_day and c.get("time_slot") == selected_slot
        ]
        for c in classes_at_time:
            rm = c.get("room")
            if rm and rm not in ["N/A", "NONE", ""]:
                if rm not in busy_rooms:
                    busy_rooms[rm] = []
                busy_rooms[rm].append(c)
                
    free_rooms_list = [r for r in all_rooms if r not in busy_rooms]
    busy_rooms_list = [r for r in all_rooms if r in busy_rooms]
    
    # Stat boxes
    st.markdown(clean_html(f"""
    <div class="status-summary">
        <div class="summary-card">
            <div class="summary-num free-glow">{len(free_rooms_list)}</div>
            <div class="summary-lbl">Available Rooms</div>
        </div>
        <div class="summary-card">
            <div class="summary-num busy-glow">{len(busy_rooms_list)}</div>
            <div class="summary-lbl">Occupied Rooms</div>
        </div>
    </div>
    """), unsafe_allow_html=True)
    
    # Search and Filter row
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        room_search = st.text_input("🔍 Search Rooms", placeholder="Search rooms (e.g. EB2-205, TB106)...").strip().lower()
    with col_filter:
        room_filter_status = st.radio("Filter status", ["All", "Only Free", "Only Occupied"], horizontal=True)
        
    # Render Grid
    cards_html = []
    for rm in all_rooms:
        is_free = rm not in busy_rooms
        
        # Apply filters
        if room_filter_status == "Only Free" and not is_free:
            continue
        if room_filter_status == "Only Occupied" and is_free:
            continue
            
        # Apply search
        if room_search and room_search not in rm.lower():
            continue
            
        if is_free:
            card = clean_html(f"""
            <div class="room-card status-free">
                <div class="room-header">
                    <span class="room-name">{rm}</span>
                    <span class="status-badge free">🟢 Free</span>
                </div>
                <div class="room-details">
                    <p class="room-details-title" style="color: #10b981;">Available</p>
                    <p>This room is empty at the selected time. Good for self-study or meetings.</p>
                </div>
            </div>
            """)
        else:
            ongoing_classes_html = ""
            for c in busy_rooms[rm]:
                teachers_str = ", ".join(c.get("teachers", [])) if c.get("teachers") else "Self-Study"
                ongoing_classes_html += clean_html(f"""
                <div style="border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.5rem; margin-bottom: 0.5rem; font-size: 0.85rem;">
                    <div style="color: #fff; font-weight: 600;">{c.get('course_name')} ({c.get('course_code') or 'Core'})</div>
                    <div class="meta-item">👥 Section: {c.get('section')} ({c.get('semester')})</div>
                    <div class="meta-item">🎓 Teacher: {teachers_str}</div>
                    <div class="meta-item">🏷️ Type: {c.get('type') or 'Lecture'}</div>
                </div>
                """)
            card = clean_html(f"""
            <div class="room-card status-busy">
                <div class="room-header">
                    <span class="room-name">{rm}</span>
                    <span class="status-badge busy">🔴 Busy</span>
                </div>
                <div class="room-details">
                    <p class="room-details-title">Class Ongoing</p>
                    {ongoing_classes_html}
                </div>
            </div>
            """)
        cards_html.append(card)
        
    if cards_html:
        st.markdown(f'<div class="rooms-grid">{"".join(cards_html)}</div>', unsafe_allow_html=True)
    else:
        st.info("No rooms found matching your search and filter criteria.")

# ----------------- TAB 2: TEACHER FINDER -----------------
with tab2:
    st.header("Teacher Finder")
    
    if all_teachers:
        selected_teacher = st.selectbox("Search for a Teacher", options=[""] + all_teachers, format_func=lambda x: "Select a teacher..." if x == "" else x)
        
        if selected_teacher:
            # Active status
            active_class = next((
                c for c in classes
                if selected_teacher in c.get("teachers", []) 
                and c.get("day") == selected_day 
                and c.get("time_slot") == selected_slot
            ), None)
            
            is_free = active_class is None
            
            status_badge_html = f'<span class="status-badge free">🟢 Available</span>' if is_free else f'<span class="status-badge busy">🔴 Busy (Room {active_class.get("room")})</span>'
            
            details_html = ""
            if not is_free:
                details_html = clean_html(f"""
                <div class="teacher-class-details">
                    <div style="font-weight: 700; color: #fff; font-size: 1.05rem;">Ongoing Class Details</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.5rem; font-size: 0.9rem;">
                        <div><span style="color: #94a3b8;">Subject:</span> {active_class.get('course_name')} ({active_class.get('course_code') or 'Core'})</div>
                        <div><span style="color: #94a3b8;">Room:</span> <strong style="color: #60a5fa;">{active_class.get('room')}</strong></div>
                        <div><span style="color: #94a3b8;">Section:</span> {active_class.get('section')} ({active_class.get('semester')})</div>
                        <div><span style="color: #94a3b8;">Type:</span> {active_class.get('type') or 'Lecture'}</div>
                    </div>
                </div>
                """)
                
            st.markdown(clean_html(f"""
            <div class="teacher-status-card">
                <div class="teacher-info-side">
                    <div class="teacher-avatar">👨‍🏫</div>
                    <div class="teacher-meta">
                        <h2>{selected_teacher}</h2>
                        <p>Active Status on {day_options[selected_day]} at {selected_slot}</p>
                    </div>
                </div>
                <div>
                    {status_badge_html}
                </div>
                {details_html}
            </div>
            """), unsafe_allow_html=True)
            
            # Weekly schedule
            st.subheader("Weekly Timetable")
            
            # Draw schedule grid
            header_cols = ["Day"] + all_slots
            header_html = "".join(f"<th>{slot}</th>" for slot in all_slots)
            
            rows_html = ""
            days_list = ["MON", "TUE", "WED", "THU", "FRI"]
            for d in days_list:
                row_cells_html = f"<td><strong>{d}</strong></td>"
                for slot in all_slots:
                    classes_for_slot = [
                        c for c in classes
                        if selected_teacher in c.get("teachers", []) 
                        and c.get("day") == d 
                        and c.get("time_slot") == slot
                    ]
                    
                    cell_content = ""
                    if classes_for_slot:
                        for c in classes_for_slot:
                            cell_content += clean_html(f"""
                            <div class="table-cell-card">
                                <span class="cell-subject">{c.get('course_name')}</span>
                                <span class="cell-code">{c.get('course_code') or 'Core'} - {c.get('type') or 'L'}</span>
                                <div class="cell-meta">
                                    <span>👥 {c.get('section')}</span>
                                    <span class="cell-room">{c.get('room')}</span>
                                </div>
                            </div>
                            """)
                    else:
                        cell_content = '<span class="cell-free">Free</span>'
                        
                    row_cells_html += f"<td>{cell_content}</td>"
                rows_html += f"<tr>{row_cells_html}</tr>"
                
            st.markdown(clean_html(f"""
            <div class="table-container">
                <table class="weekly-table">
                    <thead>
                        <tr>
                            <th>Day</th>
                            {header_html}
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
            """), unsafe_allow_html=True)
            
        else:
            st.info("Please select a teacher from the dropdown above to view their details.")
    else:
        st.info("No teachers available in timetable data.")

# ----------------- TAB 3: SECTION TIMETABLES -----------------
with tab3:
    st.header("Section Timetables")
    
    if all_sems:
        selected_sem = st.selectbox("Select Semester", options=all_sems)
        
        # Populate sections dynamically based on semester
        all_sections_for_sem = sorted(list(set(
            c.get("section") for c in classes
            if c.get("semester") == selected_sem and c.get("section")
        )))
        
        if all_sections_for_sem:
            selected_sec = st.selectbox("Select Section", options=all_sections_for_sem)
            
            st.subheader(f"Class Schedule for {selected_sem} - {selected_sec}")
            
            # Find time slots relevant to this specific section to avoid wide empty tables
            sec_classes = [
                c for c in classes
                if c.get("semester") == selected_sem and c.get("section") == selected_sec
            ]
            sec_slots = sorted(list(set(
                c.get("time_slot") for c in sec_classes
            )), key=get_slot_minutes)
            
            if sec_slots:
                header_html = "".join(f"<th>{slot}</th>" for slot in sec_slots)
                
                rows_html = ""
                days_list = ["MON", "TUE", "WED", "THU", "FRI"]
                for d in days_list:
                    row_cells_html = f"<td><strong>{d}</strong></td>"
                    for slot in sec_slots:
                        classes_for_slot = [
                            c for c in sec_classes
                            if c.get("day") == d and c.get("time_slot") == slot
                        ]
                        
                        cell_content = ""
                        if classes_for_slot:
                            for c in classes_for_slot:
                                teachers_str = ", ".join(c.get("teachers", [])) if c.get("teachers") else "Study"
                                cell_content += clean_html(f"""
                                <div class="table-cell-card">
                                    <span class="cell-subject">{c.get('course_name')}</span>
                                    <span class="cell-code">{c.get('course_code') or 'Core'} - {c.get('type') or 'L'}</span>
                                    <div class="cell-meta">
                                        <span title="{teachers_str}">👨‍🏫 {c.get('teachers')[0] if c.get('teachers') else 'Study'}</span>
                                        <span class="cell-room">{c.get('room')}</span>
                                    </div>
                                </div>
                                """)
                        else:
                            cell_content = '<span class="cell-free">Free</span>'
                            
                        row_cells_html += f"<td>{cell_content}</td>"
                    rows_html += f"<tr>{row_cells_html}</tr>"
                    
                st.markdown(clean_html(f"""
                <div class="table-container">
                    <table class="weekly-table">
                        <thead>
                            <tr>
                                <th>Day</th>
                                {header_html}
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                </div>
                """), unsafe_allow_html=True)
            else:
                st.info("No scheduled classes found for this section.")
        else:
            st.info("No sections available for the selected semester.")
    else:
        st.info("No semester data available.")
