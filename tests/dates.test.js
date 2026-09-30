// docs/verification/dates.md: exhaustive against UTC day arithmetic, in two time zones. node tests/dates.test.js
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const ZONES = ["Europe/Berlin", "America/New_York"];
if (!process.env.TZ) {
    for (const zone of ZONES)
        execFileSync(process.execPath, [__filename], { env: { ...process.env, TZ: zone }, stdio: "inherit" });
    console.log("dates: ok in " + ZONES.join(", "));
    process.exit(0);
}

const source = fs.readFileSync(path.join(__dirname, "../src/calendary/qml/calendar/dates.js"), "utf8");
const dates = new Function(source.replace(".pragma library", "") +
    "; return { day, addDays, addMonths, startOfWeek, monthGrid, parseDate, parseTime, atMinutes, time, date };")();

// Oracle: whole days since the epoch on the UTC calendar, which has no daylight saving.
const utcDay = (y, m, d) => Date.UTC(y, m, d) / 86400000;
const fromUtcDay = n => { const u = new Date(n * 86400000); return [u.getUTCFullYear(), u.getUTCMonth(), u.getUTCDate()]; };
const local = (y, m, d, h = 0, min = 0) => new Date(y, m, d, h, min).getTime();
const parts = ms => { const d = new Date(ms); return [d.getFullYear(), d.getMonth(), d.getDate(), d.getHours(), d.getMinutes()]; };

let checked = 0;
for (let n = utcDay(2020, 0, 1); n <= utcDay(2035, 11, 31); n++) {
    const [y, m, d] = fromUtcDay(n);
    const noon = local(y, m, d, 12, 30);
    for (let k = -40; k <= 40; k++) {
        const [ey, em, ed] = fromUtcDay(n + k);
        assert.deepStrictEqual(parts(dates.addDays(noon, k)), [ey, em, ed, 12, 30], `addDays ${y}-${m + 1}-${d} ${k}`);
    }
    for (let k = -25; k <= 25; k++) {
        const target = new Date(Date.UTC(y, m + k, 1));
        const last = new Date(Date.UTC(target.getUTCFullYear(), target.getUTCMonth() + 1, 0)).getUTCDate();
        assert.deepStrictEqual(parts(dates.addMonths(noon, k)),
            [target.getUTCFullYear(), target.getUTCMonth(), Math.min(d, last), 0, 0], `addMonths ${y}-${m + 1}-${d} ${k}`);
    }
    for (const weekStart of [0, 1]) {
        const weekday = new Date(n * 86400000).getUTCDay();
        const [sy, sm, sd] = fromUtcDay(n - ((weekday - weekStart + 7) % 7));
        assert.deepStrictEqual(parts(dates.startOfWeek(noon, weekStart)), [sy, sm, sd, 0, 0]);
        const firstWeekday = new Date(Date.UTC(y, m, 1)).getUTCDay();
        const [gy, gm, gd] = fromUtcDay(utcDay(y, m, 1) - ((firstWeekday - weekStart + 7) % 7));
        assert.deepStrictEqual(parts(dates.monthGrid(noon, weekStart)), [gy, gm, gd, 0, 0]);
    }
    checked++;
}
assert.strictEqual(checked, 5844);

for (const year of [2024, 2026]) {
    for (let d = 0; d <= 32; d++) {
        for (let m = 0; m <= 13; m++) {
            const real = m >= 1 && m <= 12 && d >= 1 && d <= new Date(Date.UTC(year, m, 0)).getUTCDate();
            const parsed = dates.parseDate(`${d}.${m}.${year}`, 1999);
            assert.strictEqual(isNaN(parsed), !real, `${d}.${m}.${year}`);
            if (real)
                assert.deepStrictEqual(parts(parsed), [year, m - 1, d, 0, 0]);
        }
    }
}
assert.strictEqual(dates.parseDate("1.10.", 2027), local(2027, 9, 1));
assert.strictEqual(dates.parseDate("30.9.26", 1999), local(2026, 8, 30));
assert.ok(isNaN(dates.parseDate("morgen", 2026)) && isNaN(dates.parseDate("1.1.123", 2026)));
for (let h = 0; h <= 25; h++) {
    for (let min = 0; min <= 61; min++) {
        const valid = h <= 23 && min <= 59;
        for (const text of [`${h}:${String(min).padStart(2, "0")}`, `${String(h).padStart(2, "0")}${String(min).padStart(2, "0")}`,
                            `${h}.${String(min).padStart(2, "0")}`]) {
            const parsed = dates.parseTime(text);
            assert.strictEqual(valid ? parsed : isNaN(parsed), valid ? h * 60 + min : true, text);
        }
    }
    assert.strictEqual(dates.parseTime(String(h)), h <= 23 ? h * 60 : NaN);
}
assert.strictEqual(dates.time(local(2026, 9, 1, 9, 5)), "09:05");
assert.strictEqual(dates.date(local(2026, 9, 1)), "01.10.2026");
assert.strictEqual(dates.atMinutes(local(2026, 9, 25), 570), local(2026, 9, 25, 9, 30));
