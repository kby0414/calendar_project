"use strict";

// 1. 상태(state)는 '보고 있는 월'과 '선택한 날짜'를 분리합니다.
// 예: 10월 달력에 함께 보이는 11월 1일을 선택해도 보고 있는 월은 10월입니다.
const now = new Date();
const state = {
    year: now.getFullYear(),
    month: now.getMonth() + 1, // JS의 월은 0~11, 서버의 월은 1~12입니다.
    selectedDate: localDateKey(now),
    days: [],
    loading: false,
};
const elements = Object.fromEntries([
    "todayLabel", "monthYear", "monthSummary", "prevBtn", "nextBtn", "todayBtn",
    "calendarTable", "calendarGrid", "statusMessage", "retryBtn",
    "selectedDateTitle", "selectedDateSubtitle", "daySchedules",
].map(id => [id, document.getElementById(id)]));
let activeRequest = null;
let requestNumber = 0;

// 2. '오늘'은 사용자의 로컬 날짜로 비교합니다.
// toISOString()은 UTC로 변환하므로 한국의 새벽에는 전날이 될 수 있습니다.
function localDateKey(date) {
    const pad = value => String(value).padStart(2, "0");
    return `${String(date.getFullYear()).padStart(4, "0")}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function dateLabel(dateKey) {
    // 날짜만 있는 문자열을 UTC로 해석하지 않도록 로컬 정오를 명시합니다.
    return new Intl.DateTimeFormat("ko-KR", {
        month: "long", day: "numeric", weekday: "long",
    }).format(new Date(`${dateKey}T12:00:00`));
}

function makeElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    // 3. DB의 일정 제목과 장소는 HTML이 아닌 글자로 넣습니다.
    // innerHTML을 쓰면 사용자가 입력한 <태그> 등이 실제 HTML로 실행될 수 있습니다.
    if (text !== undefined) element.textContent = text;
    return element;
}

function updateHeading() {
    elements.monthYear.textContent = `${state.year}년 ${state.month}월`;
    elements.todayLabel.textContent = `오늘 · ${dateLabel(localDateKey(new Date()))}`;
    elements.prevBtn.disabled = state.year === 1 && state.month === 1;
    elements.nextBtn.disabled = state.year === 9998 && state.month === 12;
}

function showStatus(message, isError = false) {
    elements.statusMessage.textContent = message;
    elements.statusMessage.parentElement.classList.toggle("is-error", isError);
    elements.retryBtn.hidden = !isError;
}

function showPlaceholder(message) {
    const fragment = document.createDocumentFragment();
    for (let week = 0; week < 6; week += 1) {
        const row = document.createElement("tr");
        for (let day = 0; day < 7; day += 1) {
            const cell = makeElement("td", "placeholder-cell");
            cell.setAttribute("aria-hidden", "true");
            cell.append(makeElement("div", "skeleton"));
            row.append(cell);
        }
        fragment.append(row);
    }
    elements.calendarGrid.replaceChildren(fragment);
    elements.monthSummary.textContent = message;
    elements.selectedDateTitle.textContent = "선택한 날짜";
    elements.selectedDateSubtitle.textContent = message;
    elements.daySchedules.replaceChildren();
}

// 4. API → 상태 저장 → 달력 표시 → 선택 날짜 상세 표시 순서입니다.
// 윤년, 앞뒤 달 날짜, 42칸 계산은 Python 서버가 담당하므로 JS에서 재계산하지 않습니다.
async function loadCalendar() {
    if (activeRequest) activeRequest.abort();
    const controller = new AbortController();
    activeRequest = controller;
    const thisRequest = ++requestNumber;
    const { year, month } = state;
    state.loading = true;
    state.days = [];
    updateHeading();
    elements.calendarTable.setAttribute("aria-busy", "true");
    showPlaceholder("일정을 불러오고 있어요.");
    showStatus("달력을 불러오는 중입니다.");
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, 12000);

    try {
        // 같은 FastAPI 서버가 화면과 API를 모두 제공하므로 주소/포트를 하드코딩하지 않습니다.
        const response = await fetch(`/calendar/${year}/${month}`, { signal: controller.signal });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        // 월 이동 버튼을 빠르게 누르면 오래된 응답이 뒤늦게 올 수 있습니다.
        // 최신 요청만 반영하여 11월 제목 아래 10월이 그려지는 문제를 막습니다.
        if (thisRequest !== requestNumber) return;
        if (data.year !== year || data.month !== month || !Array.isArray(data.grid)
            || data.grid.length !== 6 || data.grid.some(week => !Array.isArray(week) || week.length !== 7)) {
            throw new Error("올바르지 않은 달력 응답");
        }
        state.days = data.grid.flat();
        const today = localDateKey(new Date());
        if (!state.days.some(day => day.date === state.selectedDate)) {
            state.selectedDate = state.days.find(day => day.date === today && day.type === "current")?.date
                ?? state.days.find(day => day.type === "current").date;
        }
        renderCalendar();
        renderAgenda();
        const count = state.days.filter(day => day.type === "current")
            .reduce((sum, day) => sum + day.schedules.length, 0);
        elements.monthSummary.textContent = count ? `이번 달에 ${count}개의 일정이 있어요.` : "이번 달에 등록된 일정이 없어요.";
        showStatus(`${year}년 ${month}월 일정을 불러왔습니다.`);
    } catch (error) {
        if (thisRequest !== requestNumber) return;
        state.days = [];
        showPlaceholder("달력을 불러오지 못했어요.");
        showStatus(timedOut ? "응답이 늦어지고 있어요. 잠시 후 다시 시도해주세요."
            : "서버 연결을 확인한 뒤 다시 불러와주세요.", true);
    } finally {
        clearTimeout(timer);
        if (thisRequest === requestNumber) {
            state.loading = false;
            activeRequest = null;
            elements.calendarTable.setAttribute("aria-busy", "false");
        }
    }
}

function renderCalendar() {
    const today = localDateKey(new Date());
    const fragment = document.createDocumentFragment();
    for (let week = 0; week < 6; week += 1) {
        const row = document.createElement("tr");
        for (let column = 0; column < 7; column += 1) {
            const day = state.days[week * 7 + column];
            const cell = document.createElement("td");
            const button = makeElement("button", "day-cell");
            button.type = "button";
            button.dataset.date = day.date;
            button.classList.toggle("is-outside", day.type !== "current");
            button.classList.toggle("is-today", day.date === today);
            button.classList.toggle("saturday", column === 5);
            button.classList.toggle("sunday", column === 6);
            button.setAttribute("aria-label", `${day.date}, ${dateLabel(day.date)}, 일정 ${day.schedules.length}개${day.date === today ? ", 오늘" : ""}`);
            if (day.date === today) button.setAttribute("aria-current", "date");
            button.append(makeElement("span", "day-number", day.day));
            day.schedules.slice(0, 2).forEach(schedule => {
                const preview = makeElement("span", "event-preview", schedule.title || "제목 없는 일정");
                preview.title = schedule.title || "제목 없는 일정";
                button.append(preview);
            });
            if (day.schedules.length > 2) {
                button.append(makeElement("span", "event-more", `+${day.schedules.length - 2}개 더`));
            }
            cell.append(button);
            row.append(cell);
        }
        fragment.append(row);
    }
    elements.calendarGrid.replaceChildren(fragment);
    updateSelection();
}

function updateSelection() {
    // 날짜를 선택할 때는 버튼을 다시 만들지 않아 키보드 포커스가 사라지지 않습니다.
    elements.calendarGrid.querySelectorAll(".day-cell").forEach(button => {
        const selected = button.dataset.date === state.selectedDate;
        button.classList.toggle("is-selected", selected);
        button.setAttribute("aria-pressed", String(selected));
    });
}

function renderAgenda() {
    const day = state.days.find(item => item.date === state.selectedDate);
    if (!day) return;
    elements.selectedDateTitle.textContent = dateLabel(day.date);
    elements.selectedDateSubtitle.textContent = `${day.date.slice(0, 4)}년 · ${day.schedules.length}개의 일정`;
    if (day.schedules.length === 0) {
        const empty = makeElement("div", "empty-state");
        const icon = makeElement("span", "empty-icon", "✓");
        icon.setAttribute("aria-hidden", "true");
        empty.append(icon, makeElement("strong", "", "등록된 일정이 없어요"),
            makeElement("p", "", "다른 날짜를 눌러 일정을 살펴보세요."));
        elements.daySchedules.replaceChildren(empty);
        return;
    }
    const list = makeElement("ul", "schedule-list");
    day.schedules.forEach(schedule => {
        const card = makeElement("li", "schedule-card");
        card.append(makeElement("span", "schedule-category", schedule.category || "미분류"),
            makeElement("h3", "", schedule.title || "제목 없는 일정"));
        if (schedule.location) card.append(makeElement("p", "schedule-location", `장소 · ${schedule.location}`));
        list.append(card);
    });
    elements.daySchedules.replaceChildren(list);
}

function changeMonth(amount) {
    // 0부터 세는 '전체 개월 수'로 바꾸면 12월↔1월의 연도 변경도 같은 방식으로 처리됩니다.
    const monthIndex = (state.year - 1) * 12 + state.month - 1 + amount;
    if (monthIndex < 0 || monthIndex >= 9998 * 12) return;
    state.year = Math.floor(monthIndex / 12) + 1;
    state.month = monthIndex % 12 + 1;
    state.selectedDate = `${String(state.year).padStart(4, "0")}-${String(state.month).padStart(2, "0")}-01`;
    loadCalendar();
}

elements.prevBtn.addEventListener("click", () => changeMonth(-1));
elements.nextBtn.addEventListener("click", () => changeMonth(1));
elements.todayBtn.addEventListener("click", () => {
    const today = new Date();
    state.year = today.getFullYear();
    state.month = today.getMonth() + 1;
    state.selectedDate = localDateKey(today);
    loadCalendar();
});
elements.retryBtn.addEventListener("click", loadCalendar);

// 5. 이벤트 위임: 매번 생성되는 42개 버튼 대신 부모 한 곳에서 클릭을 받습니다.
elements.calendarGrid.addEventListener("click", event => {
    const button = event.target.closest("button[data-date]");
    if (!button || state.loading) return;
    state.selectedDate = button.dataset.date;
    updateSelection();
    renderAgenda();
});

loadCalendar();
