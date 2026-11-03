// Wait for DOM to load
document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

// App State
let state = {
  selectedDay: "MON",
  selectedTimeSlot: "",
  activeTab: "rooms",
  roomFilter: "all",
  roomSearchQuery: "",
  selectedTeacher: "",
  selectedSem: "1st Sem",
  selectedSec: ""
};

// Master Lists extracted dynamically
let allRooms = [];
let allTimeSlots = [];
let allTeachers = [];

function initApp() {
  // Extract master lists from timetable data
  extractMasterLists();

  // Populate time slot selectors
  populateTimeSlots();

  // Set default time slot (first available one)
  if (allTimeSlots.length > 0) {
    state.selectedTimeSlot = allTimeSlots[0];
    document.getElementById("time-select").value = state.selectedTimeSlot;
  }

  // Populate sections selector for initial semester
  populateSectionsSelector();

  // Initialize Lucide Icons
  lucide.createIcons();

  // Register Event Listeners
  registerEventListeners();

  // Initial renders
  renderRoomsTab();
  
  // Set default search if empty
  const teacherInput = document.getElementById("teacher-search-input");
  teacherInput.value = "";
}

function extractMasterLists() {
  if (!TIMETABLE_DATA || !TIMETABLE_DATA.classes) return;

  // 1. Get unique rooms (excluding N/A)
  allRooms = [...new Set(TIMETABLE_DATA.classes
    .map(c => c.room)
    .filter(r => r && r !== 'N/A' && r !== 'NONE' && r.trim() !== '')
  )].sort();

  // 2. Get unique time slots and sort them chronologically
  allTimeSlots = [...new Set(TIMETABLE_DATA.classes.map(c => c.time_slot))].sort((a, b) => {
    return getSlotMinutes(a) - getSlotMinutes(b);
  });

  // 3. Get unique teachers
  allTeachers = [...new Set(TIMETABLE_DATA.classes.flatMap(c => c.teachers))].filter(Boolean).sort();
}

function getSlotMinutes(slot) {
  const match = slot.match(/(\d{2}):(\d{2})\s*-\s*\d{2}:\d{2}\s*(AM|PM)/);
  if (!match) return 0;
  let hr = parseInt(match[1]);
  const min = parseInt(match[2]);
  const ampm = match[3];
  if (ampm === 'PM' && hr !== 12) hr += 12;
  if (ampm === 'AM' && hr === 12) hr = 0;
  return hr * 60 + min;
}

function populateTimeSlots() {
  const timeSelect = document.getElementById("time-select");
  timeSelect.innerHTML = "";
  allTimeSlots.forEach(slot => {
    const opt = document.createElement("option");
    opt.value = slot;
    opt.textContent = slot;
    timeSelect.appendChild(opt);
  });
}

function populateSectionsSelector() {
  const sem = state.selectedSem;
  const sections = [...new Set(TIMETABLE_DATA.classes
    .filter(c => c.semester === sem)
    .map(c => c.section)
  )].sort();

  const secSelect = document.getElementById("sec-filter");
  secSelect.innerHTML = "";
  sections.forEach(sec => {
    const opt = document.createElement("option");
    opt.value = sec;
    opt.textContent = sec;
    secSelect.appendChild(opt);
  });

  if (sections.length > 0) {
    state.selectedSec = sections[0];
    secSelect.value = state.selectedSec;
  }
}

function registerEventListeners() {
  // Day select listener
  document.getElementById("day-select").addEventListener("change", (e) => {
    state.selectedDay = e.target.value;
    onDateTimeChange();
  });

  // Time select listener
  document.getElementById("time-select").addEventListener("change", (e) => {
    state.selectedTimeSlot = e.target.value;
    onDateTimeChange();
  });

  // Tabs navigation listeners
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const targetTab = e.currentTarget.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });

  // Room search listener
  document.getElementById("room-search").addEventListener("input", (e) => {
    state.roomSearchQuery = e.target.value.toLowerCase().trim();
    renderRoomsTab();
  });

  // Room filter pills listeners
  document.querySelectorAll(".filter-pill").forEach(pill => {
    pill.addEventListener("click", (e) => {
      document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
      e.currentTarget.classList.add("active");
      state.roomFilter = e.currentTarget.getAttribute("data-filter");
      renderRoomsTab();
    });
  });

  // Teacher search autocomplete
  const teacherInput = document.getElementById("teacher-search-input");
  const suggestionsBox = document.getElementById("teacher-suggestions");

  teacherInput.addEventListener("input", (e) => {
    const val = e.target.value.trim().toLowerCase();
    if (!val) {
      suggestionsBox.style.display = "none";
      return;
    }

    const filtered = allTeachers.filter(t => t.toLowerCase().includes(val));
    if (filtered.length === 0) {
      suggestionsBox.style.display = "none";
      return;
    }

    suggestionsBox.innerHTML = "";
    filtered.slice(0, 8).forEach(t => {
      const div = document.createElement("div");
      div.className = "suggestion-item";
      div.textContent = t;
      div.addEventListener("click", () => {
        teacherInput.value = t;
        suggestionsBox.style.display = "none";
        selectTeacher(t);
      });
      suggestionsBox.appendChild(div);
    });
    suggestionsBox.style.display = "block";
  });

  // Closesuggestions box when clicking outside
  document.addEventListener("click", (e) => {
    if (!teacherInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
      suggestionsBox.style.display = "none";
    }
  });

  // Section semester and section select listeners
  document.getElementById("sem-filter").addEventListener("change", (e) => {
    state.selectedSem = e.target.value;
    populateSectionsSelector();
    renderSectionsTab();
  });

  document.getElementById("sec-filter").addEventListener("change", (e) => {
    state.selectedSec = e.target.value;
    renderSectionsTab();
  });
}

function onDateTimeChange() {
  if (state.activeTab === "rooms") {
    renderRoomsTab();
  } else if (state.activeTab === "teachers") {
    renderTeacherStatus();
  }
}

function switchTab(tabId) {
  state.activeTab = tabId;
  
  // Update button active states
  document.querySelectorAll(".tab-btn").forEach(btn => {
    if (btn.getAttribute("data-tab") === tabId) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // Show/hide tab panels
  document.querySelectorAll(".tab-content").forEach(panel => {
    if (panel.id === `tab-${tabId}`) {
      panel.classList.add("active");
    } else {
      panel.classList.remove("active");
    }
  });

  // Trigger tab-specific renders
  if (tabId === "rooms") {
    renderRoomsTab();
  } else if (tabId === "teachers") {
    if (state.selectedTeacher) {
      selectTeacher(state.selectedTeacher);
    }
  } else if (tabId === "sections") {
    renderSectionsTab();
  }
}

/* ==================== TAB 1: ROOM LOCATOR ==================== */
function renderRoomsTab() {
  const container = document.getElementById("rooms-container");
  container.innerHTML = "";

  // 1. Find busy rooms and their class info for current Day and Time Slot
  const classesAtTime = TIMETABLE_DATA.classes.filter(c => 
    c.day === state.selectedDay && c.time_slot === state.selectedTimeSlot
  );

  const busyRoomsMap = {};
  classesAtTime.forEach(c => {
    if (c.room && c.room !== "N/A" && c.room !== "NONE") {
      if (!busyRoomsMap[c.room]) {
        busyRoomsMap[c.room] = [];
      }
      busyRoomsMap[c.room].push(c);
    }
  });

  // Calculate status lists
  let freeCount = 0;
  let busyCount = 0;
  const cardsToRender = [];

  allRooms.forEach(room => {
    const isBusy = room in busyRoomsMap;
    const isFree = !isBusy;
    
    if (isFree) freeCount++;
    else busyCount++;

    // Apply Filter
    if (state.roomFilter === "free" && isBusy) return;
    if (state.roomFilter === "busy" && isFree) return;

    // Apply Search
    if (state.roomSearchQuery && !room.toLowerCase().includes(state.roomSearchQuery)) return;

    cardsToRender.push({
      room,
      isFree,
      classes: busyRoomsMap[room] || []
    });
  });

  // Update counts on UI
  document.getElementById("free-rooms-count").textContent = freeCount;
  document.getElementById("busy-rooms-count").textContent = busyCount;

  if (cardsToRender.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <i data-lucide="door-closed"></i>
        <h3>No Rooms Found</h3>
        <p>Try modifying your search query or filters.</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }

  // Render cards
  cardsToRender.forEach(item => {
    const card = document.createElement("div");
    card.className = `room-card ${item.isFree ? 'status-free' : 'status-busy'}`;

    let detailsHTML = "";
    if (item.isFree) {
      detailsHTML = `
        <div class="room-details">
          <p class="room-details-title" style="color: var(--success-color);">Available</p>
          <p>This room is empty at the selected time. Good for self-study, work, or meetings.</p>
        </div>
      `;
    } else {
      // Busy details, potentially multiple classes if shared lab space
      detailsHTML = `
        <div class="room-details">
          <p class="room-details-title">Class Ongoing</p>
          <div class="room-details-meta">
      `;
      
      item.classes.forEach(c => {
        const teachersStr = c.teachers.length > 0 ? c.teachers.join(", ") : "Self-Study";
        detailsHTML += `
            <div style="border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.5rem; margin-bottom: 0.5rem; font-size: 0.85rem;">
              <div style="color: #fff; font-weight: 600;">${c.course_name} (${c.course_code || 'Core'})</div>
              <div class="meta-item" style="margin-top: 0.25rem;"><i data-lucide="users"></i> Section: ${c.section} (${c.semester})</div>
              <div class="meta-item"><i data-lucide="graduation-cap"></i> Teacher: ${teachersStr}</div>
              <div class="meta-item"><i data-lucide="tag"></i> Type: ${c.type || 'Lecture'}</div>
            </div>
        `;
      });

      detailsHTML += `
          </div>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="room-header">
        <span class="room-name">${item.room}</span>
        <span class="status-badge">
          <i data-lucide="${item.isFree ? 'check-circle' : 'alert-circle'}"></i>
          ${item.isFree ? 'Free' : 'Busy'}
        </span>
      </div>
      ${detailsHTML}
    `;

    container.appendChild(card);
  });

  lucide.createIcons();
}

/* ==================== TAB 2: TEACHER FINDER ==================== */
function selectTeacher(teacherName) {
  state.selectedTeacher = teacherName;
  document.getElementById("teacher-search-input").value = teacherName;
  document.getElementById("teacher-empty-state").style.display = "none";
  document.getElementById("teacher-results").style.display = "flex";

  renderTeacherStatus();
  renderTeacherWeeklySchedule();
}

function renderTeacherStatus() {
  if (!state.selectedTeacher) return;

  const statusCard = document.getElementById("teacher-status-card");
  statusCard.innerHTML = "";

  // Check if teacher is teaching right now
  const activeClass = TIMETABLE_DATA.classes.find(c => 
    c.teachers.includes(state.selectedTeacher) &&
    c.day === state.selectedDay &&
    c.time_slot === state.selectedTimeSlot
  );

  const isFree = !activeClass;

  let classDetailsHTML = "";
  if (!isFree) {
    classDetailsHTML = `
      <div class="teacher-class-details">
        <div style="font-weight: 700; color: #fff; font-size: 1.05rem;">Ongoing Class Details</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.5rem; font-size: 0.9rem;">
          <div><span style="color: var(--text-secondary);">Subject:</span> ${activeClass.course_name} (${activeClass.course_code || 'Core'})</div>
          <div><span style="color: var(--text-secondary);">Room:</span> <strong style="color: var(--accent-color);">${activeClass.room}</strong></div>
          <div><span style="color: var(--text-secondary);">Section:</span> ${activeClass.section} (${activeClass.semester})</div>
          <div><span style="color: var(--text-secondary);">Type:</span> ${activeClass.type || 'Lecture'}</div>
        </div>
      </div>
    `;
  }

  statusCard.innerHTML = `
    <div class="teacher-info-side">
      <div class="teacher-avatar">
        <i data-lucide="user"></i>
      </div>
      <div class="teacher-meta">
        <h2>${state.selectedTeacher}</h2>
        <p><i data-lucide="calendar"></i> Active Status on ${getDayFullName(state.selectedDay)} at ${state.selectedTimeSlot}</p>
      </div>
    </div>
    <div>
      <span class="teacher-status-badge ${isFree ? 'status-free' : 'status-busy'}">
        <i data-lucide="${isFree ? 'check-circle' : 'alert-circle'}"></i>
        ${isFree ? 'Available' : 'Busy (In Room ' + activeClass.room + ')'}
      </span>
    </div>
    ${classDetailsHTML}
  `;

  lucide.createIcons();
}

function getDayFullName(dayCode) {
  const map = {
    "MON": "Monday",
    "TUE": "Tuesday",
    "WED": "Wednesday",
    "THU": "Thursday",
    "FRI": "Friday"
  };
  return map[dayCode] || dayCode;
}

function renderTeacherWeeklySchedule() {
  if (!state.selectedTeacher) return;

  const headerRow = document.getElementById("weekly-table-header");
  const body = document.getElementById("weekly-table-body");

  // Populate header time slots
  headerRow.innerHTML = "<th>Day</th>";
  allTimeSlots.forEach(slot => {
    const th = document.createElement("th");
    th.textContent = slot;
    headerRow.appendChild(th);
  });

  body.innerHTML = "";

  const days = ["MON", "TUE", "WED", "THU", "FRI"];
  days.forEach(day => {
    const tr = document.createElement("tr");
    
    // Day column
    const tdDay = document.createElement("td");
    tdDay.textContent = day;
    tr.appendChild(tdDay);

    // Slots columns
    allTimeSlots.forEach(slot => {
      const tdSlot = document.createElement("td");
      
      // Find classes for this teacher on this day/slot
      const classes = TIMETABLE_DATA.classes.filter(c => 
        c.teachers.includes(state.selectedTeacher) &&
        c.day === day &&
        c.time_slot === slot
      );

      if (classes.length > 0) {
        classes.forEach(c => {
          const card = document.createElement("div");
          card.className = "table-cell-card";
          card.innerHTML = `
            <span class="cell-subject">${c.course_name}</span>
            <span class="cell-code">${c.course_code || 'Core'} - ${c.type || 'L'}</span>
            <div class="cell-meta">
              <span><i data-lucide="users"></i> ${c.section}</span>
              <span class="cell-room">${c.room}</span>
            </div>
          `;
          tdSlot.appendChild(card);
        });
      } else {
        tdSlot.innerHTML = `<span class="cell-free">Free</span>`;
      }
      
      tr.appendChild(tdSlot);
    });

    body.appendChild(tr);
  });

  lucide.createIcons();
}

/* ==================== TAB 3: SECTION TIMETABLES ==================== */
function renderSectionsTab() {
  if (!state.selectedSec) return;

  document.getElementById("section-title-text").innerHTML = `
    <i data-lucide="layout-grid"></i> Class Schedule for ${state.selectedSem} - ${state.selectedSec}
  `;

  const headerRow = document.getElementById("sec-table-header");
  const body = document.getElementById("sec-table-body");

  // Filter slots applicable to this semester to avoid empty columns
  const secClasses = TIMETABLE_DATA.classes.filter(c => 
    c.semester === state.selectedSem && c.section === state.selectedSec
  );

  const activeSlots = [...new Set(secClasses.map(c => c.time_slot))].sort((a, b) => {
    return getSlotMinutes(a) - getSlotMinutes(b);
  });

  // Populate header time slots
  headerRow.innerHTML = "<th>Day</th>";
  activeSlots.forEach(slot => {
    const th = document.createElement("th");
    th.textContent = slot;
    headerRow.appendChild(th);
  });

  body.innerHTML = "";

  const days = ["MON", "TUE", "WED", "THU", "FRI"];
  days.forEach(day => {
    const tr = document.createElement("tr");
    
    // Day column
    const tdDay = document.createElement("td");
    tdDay.textContent = day;
    tr.appendChild(tdDay);

    // Slots columns
    activeSlots.forEach(slot => {
      const tdSlot = document.createElement("td");
      
      const classes = secClasses.filter(c => 
        c.day === day && c.time_slot === slot
      );

      if (classes.length > 0) {
        classes.forEach(c => {
          const teachersStr = c.teachers.length > 0 ? c.teachers.join(", ") : "Self-Study";
          const card = document.createElement("div");
          card.className = "table-cell-card";
          card.innerHTML = `
            <span class="cell-subject">${c.course_name}</span>
            <span class="cell-code">${c.course_code || 'Core'} - ${c.type || 'L'}</span>
            <div class="cell-meta">
              <span title="${teachersStr}"><i data-lucide="graduation-cap"></i> ${c.teachers[0] || 'Study'}</span>
              <span class="cell-room">${c.room}</span>
            </div>
          `;
          tdSlot.appendChild(card);
        });
      } else {
        tdSlot.innerHTML = `<span class="cell-free">Free</span>`;
      }
      
      tr.appendChild(tdSlot);
    });

    body.appendChild(tr);
  });

  lucide.createIcons();
}
