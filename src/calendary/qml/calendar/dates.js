.pragma library

// Local calendar arithmetic for the views. Days move through the Date constructor, never in 24-hour steps, so
// daylight saving changes keep midnight at midnight. Verified in docs/verification/dates.md.

// Functions, not arrays: qsTr() runs again on every call, so a language switch reaches the bindings.
function weekdayShort(index) {
    return [qsTr("So"), qsTr("Mo"), qsTr("Di"), qsTr("Mi"), qsTr("Do"), qsTr("Fr"), qsTr("Sa")][index];
}

function monthName(index) {
    return [qsTr("Januar"), qsTr("Februar"), qsTr("März"), qsTr("April"), qsTr("Mai"), qsTr("Juni"), qsTr("Juli"),
            qsTr("August"), qsTr("September"), qsTr("Oktober"), qsTr("November"), qsTr("Dezember")][index];
}

function day(ms) {
    var d = new Date(ms);
    return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

function addDays(ms, n) {
    var d = new Date(ms);
    return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n, d.getHours(), d.getMinutes()).getTime();
}

// Same day of the month, or the last day of a shorter month.
function addMonths(ms, n) {
    var d = new Date(ms);
    var last = new Date(d.getFullYear(), d.getMonth() + n + 1, 0).getDate();
    return new Date(d.getFullYear(), d.getMonth() + n, Math.min(d.getDate(), last)).getTime();
}

function startOfWeek(ms, weekStart) {
    var d = new Date(day(ms));
    return addDays(d.getTime(), -((d.getDay() - weekStart + 7) % 7));
}

// Six weeks around a month, so the grid never changes height.
function monthGrid(ms, weekStart) {
    var d = new Date(ms);
    return startOfWeek(new Date(d.getFullYear(), d.getMonth(), 1).getTime(), weekStart);
}

function sameDay(a, b) {
    return day(a) === day(b);
}

function pad(n) {
    return (n < 10 ? "0" : "") + n;
}

function time(ms) {
    var d = new Date(ms);
    return pad(d.getHours()) + ":" + pad(d.getMinutes());
}

function date(ms) {
    var d = new Date(ms);
    return pad(d.getDate()) + "." + pad(d.getMonth() + 1) + "." + d.getFullYear();
}

// "D.M.", "D.M.YY" or "D.M.YYYY" to that day's local midnight, or NaN for anything that is not a real date.
function parseDate(text, fallbackYear) {
    var m = /^\s*(\d{1,2})\.(\d{1,2})\.(\d{2}|\d{4})?\s*$/.exec(text);
    if (!m)
        return NaN;
    var year = m[3] ? (m[3].length === 2 ? 2000 + Number(m[3]) : Number(m[3])) : fallbackYear;
    var d = new Date(year, Number(m[2]) - 1, Number(m[1]));
    return d.getFullYear() === year && d.getMonth() === Number(m[2]) - 1 && d.getDate() === Number(m[1]) ? d.getTime() : NaN;
}

// "9", "09", "9:30", "0930" or "9.30" to minutes after midnight, or NaN.
function parseTime(text) {
    var m = /^\s*(\d{1,2})(?:[:.]?(\d{2}))?\s*$/.exec(text);
    if (!m || Number(m[1]) > 23 || Number(m[2] || 0) > 59)
        return NaN;
    return Number(m[1]) * 60 + Number(m[2] || 0);
}

function atMinutes(dayMs, minutes) {
    var d = new Date(dayMs);
    return new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, minutes).getTime();
}

function minutesOf(ms) {
    var d = new Date(ms);
    return d.getHours() * 60 + d.getMinutes();
}

function span(ev) {
    return ev.allDay ? qsTr("ganztägig") : time(ev.start) + " – " + time(ev.end);
}
