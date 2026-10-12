"use strict";

// 공휴일의 빨강과 별개인 '일정 제목' 색상입니다. 지정한 값만 사용합니다.
// 노랑은 흰 배경에서 읽을 수 있는 짙은 노랑을 사용합니다.
const SCHEDULE_COLORS = Object.freeze({
    '빨강': '#c03932', '주황': '#b9540d', '노랑': '#947000',
    '초록': '#28713e', '파랑': '#245fc2', '보라': '#8044b5', '검정': '#222222',
});
function scheduleColor(category) {
    return Object.hasOwn(SCHEDULE_COLORS, category) ? SCHEDULE_COLORS[category] : SCHEDULE_COLORS['검정'];
}

// 편집창은 입력과 API 저장만 담당합니다. 달력 이동/갱신은 onSaved로 app.js에 알립니다.
// 추가와 수정은 동일한 양식을 쓰되, 기존 일정의 id가 있을 때 PUT을 사용합니다.
function createScheduleEditor(onSaved) {
    const dialog = document.getElementById('scheduleDialog');
    const form = document.getElementById('scheduleForm');
    const fields = document.getElementById('editorFields');
    const inputs = document.getElementById('scheduleInputs');
    const title = document.getElementById('scheduleTitle');
    const date = document.getElementById('scheduleDate');
    const startDate = document.getElementById('scheduleStartDate');
    const category = document.getElementById('scheduleCategory');
    const location = document.getElementById('scheduleLocation');
    const error = document.getElementById('editorError');
    const save = document.getElementById('saveScheduleBtn');
    const summary = document.getElementById('deleteSummary');
    let original = null;
    let deleting = false;
    let busy = false;

    function updatePreview() {
        document.getElementById('colorPreview').textContent = title.value.trim() || '제목 미리보기';
        document.getElementById('colorPreview').style.color = scheduleColor(category.value);
        category.style.color = scheduleColor(category.value);
        date.min = startDate.value || '0002-01-01';
        // ISO 날짜(YYYY-MM-DD)는 같은 형식일 때 문자열로 앞뒤를 비교할 수 있습니다.
        // 일수는 UTC 자정 차이로 계산하여 서머타임 때문에 하루가 줄어들지 않게 합니다.
        const valid = startDate.value && date.value && date.value >= startDate.value;
        const days = valid ? Math.round((Date.parse(`${date.value}T00:00:00Z`) - Date.parse(`${startDate.value}T00:00:00Z`)) / 86400000) + 1 : 0;
        document.getElementById('periodHint').textContent = valid
            ? `${startDate.value} ~ ${date.value} · ${days}일 모두에 적용됩니다.`
            : '종료일은 시작일과 같거나 이후여야 합니다.';
    }
    [title, category, startDate, date].forEach(input => input.addEventListener('input', updatePreview));
    category.addEventListener('change', updatePreview);

    function open(schedule, remove = false) {
        if (busy) return;
        original = { ...schedule };
        deleting = remove;
        form.reset();
        fields.disabled = false;
        error.textContent = '';
        title.value = schedule.title || '';
        // 어느 날짜에서 열어도 원래 기간을 편집합니다. 클릭한 중간 날짜로 시작일을 덮지 않습니다.
        startDate.value = schedule.date;
        date.value = schedule.end_date || schedule.date;
        category.value = Object.hasOwn(SCHEDULE_COLORS, schedule.category) ? schedule.category : '검정';
        location.value = schedule.location || '';
        inputs.hidden = remove;
        // 숨긴 필수 입력칸이 삭제 제출을 막지 않도록 비활성화합니다.
        inputs.querySelectorAll('input, select').forEach(input => { input.disabled = remove; });
        summary.hidden = !remove;
        summary.textContent = remove ? `${schedule.title}\n${schedule.date} ~ ${schedule.end_date || schedule.date}\n이 기간 전체에서 삭제됩니다. 삭제한 일정은 되돌릴 수 없습니다.` : '';
        document.getElementById('editorTitle').textContent = remove ? '일정 삭제' : schedule.id ? '일정 수정' : '일정 추가';
        document.getElementById('editorDescription').textContent = remove ? '기간 전체의 일정을 삭제할까요?' : schedule.id
            ? '수정 내용은 시작일부터 종료일까지 전체에 적용됩니다.'
            : '선택한 날짜가 시작일입니다. 종료일까지 같은 제목으로 등록됩니다.';
        save.textContent = remove ? '삭제' : '저장';
        save.classList.toggle('danger-button', remove);
        updatePreview();
        dialog.showModal();
        (remove ? document.getElementById('cancelScheduleBtn') : title).focus();
    }

    document.getElementById('cancelScheduleBtn').addEventListener('click', () => {
        if (!busy) dialog.close();
    });
    dialog.addEventListener('cancel', event => {
        // 저장 중 Escape로 닫았다가 다시 저장하는 중복 요청을 방지합니다.
        if (busy) event.preventDefault();
    });

    form.addEventListener('submit', async event => {
        event.preventDefault();
        if (busy) return;
        error.textContent = '';
        if (!deleting && (!title.value.trim() || !Object.hasOwn(SCHEDULE_COLORS, category.value))) {
            error.textContent = '제목과 분류 색상을 확인해주세요.';
            return;
        }
        if (!deleting && date.value < startDate.value) {
            error.textContent = '종료일은 시작일과 같거나 이후여야 합니다.';
            return;
        }
        const payload = deleting ? null : {
            title: title.value.trim(), date: startDate.value, end_date: date.value, category: category.value,
            location: location.value.trim() || null,
            // 장소가 그대로면 기존 좌표를 보존하고, 바뀌면 서버에서 다시 검색합니다.
            latitude: location.value.trim() === (original.location || '') ? original.latitude ?? null : null,
            longitude: location.value.trim() === (original.location || '') ? original.longitude ?? null : null,
        };
        busy = true;
        fields.disabled = true;
        dialog.setAttribute('aria-busy', 'true');
        save.textContent = deleting ? '삭제 중…' : '저장 중…';
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 20000);
        let result;
        try {
            const url = original.id ? `/schedules/${original.id}` : '/schedules/';
            const response = await fetch(url, {
                method: deleting ? 'DELETE' : original.id ? 'PUT' : 'POST',
                headers: { 'Content-Type': 'application/json' },
                ...(payload ? { body: JSON.stringify(payload) } : {}),
                signal: controller.signal,
            });
            if (!response.ok) {
                if (response.status === 404) throw new Error('이미 삭제되었거나 존재하지 않는 일정입니다. 취소 후 달력을 다시 불러와주세요.');
                if (response.status === 422) throw new Error('제목·기간·분류 색상과 입력 길이를 확인해주세요.');
                throw new Error('요청을 완료하지 못했습니다. 입력 내용은 유지됩니다.');
            }
            // 삭제는 응답 본문 없이도 성공할 수 있습니다. 저장 성공의 기준은 HTTP 응답입니다.
            const selected = original.selectedDate || original.date;
            const returnDate = deleting ? selected : selected >= payload.date && selected <= payload.end_date ? selected : payload.date;
            result = { date: returnDate,
                message: deleting ? '기간 전체의 일정을 삭제했습니다.' : original.id ? '기간 전체의 일정을 수정했습니다.' : '선택한 기간에 일정을 추가했습니다.' };
        } catch (failure) {
            // 통신 실패는 서버가 저장하지 않았다는 뜻이 아닙니다. 자동으로 재전송하지 않습니다.
            error.textContent = failure.name === 'AbortError' || failure instanceof TypeError
                ? '응답을 확인하지 못했습니다. 입력은 유지됩니다. 취소 후 새로고침해 저장 여부를 확인해주세요.'
                : failure.message;
        } finally {
            clearTimeout(timer);
            busy = false;
            fields.disabled = false;
            dialog.removeAttribute('aria-busy');
            save.textContent = deleting ? '삭제' : '저장';
        }
        if (result) {
            dialog.close();
            // 저장 성공과 후속 조회 실패를 구분합니다. 조회 실패 때문에 다시 저장하지 않습니다.
            await onSaved(result);
        }
    });
    return { open, remove: schedule => open(schedule, true) };
}
