// The spring in qml/motion/curves.js against the checks of the clean-project motion contract. node tests/motion.test.js
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const source = fs.readFileSync(path.join(__dirname, "../src/calendary/qml/motion/curves.js"), "utf8");
const { critical, settled } = new Function(source.replace(".pragma library", "") + "; return { critical, settled };")();
const omega = 2 * Math.PI / 0.34;
const close = (a, b, tolerance, what) => assert.ok(Math.abs(a - b) <= tolerance, `${what}: ${a} vs ${b}`);

// Start is exact: position and velocity at t = 0 are the ones handed in.
for (const [x0, v0] of [[36, 0], [-36, 0], [0.5, -400], [0, 250]]) {
    const s = critical(x0, v0, omega, 0);
    assert.strictEqual(s.x, x0);
    assert.strictEqual(s.v, v0);
}

// v is the derivative of x (central differences), and the error never crosses zero from rest: no overshoot.
for (let t = 0.001; t < 1; t += 0.01) {
    const h = 1e-6;
    close(critical(36, 0, omega, t).v, (critical(36, 0, omega, t + h).x - critical(36, 0, omega, t - h).x) / (2 * h), 1e-3, `derivative at ${t}`);
    assert.ok(critical(36, 0, omega, t).x > 0, `no overshoot at ${t}`);
}

// The path depends on time only: 60, 120 and 144 Hz land on the same values at the instants they share
// (every 1/12 s), with frame times derived as exact fractions, never by summing rounded frame durations.
for (let m = 0; m <= 12; m++) {
    const at60 = critical(36, 0, omega, (5 * m) / 60).x;
    assert.strictEqual(critical(36, 0, omega, (10 * m) / 120).x, at60);
    assert.strictEqual(critical(36, 0, omega, (12 * m) / 144).x, at60);
}

// A retarget mid-flight continues from the sampled position and velocity: no jump, no velocity reset.
const before = critical(36, 0, omega, 0.12);
const oldTarget = 0, newTarget = -20;
const shown = oldTarget + before.x;
const after = critical(shown - newTarget, before.v, omega, 0);
assert.strictEqual(newTarget + after.x, shown);
assert.strictEqual(after.v, before.v);

// It settles within about 1.2 response periods for a page-sized travel, and the settle test is strict about speed.
const settleTime = (() => { let t = 0; while (!settled(critical(36, 0, omega, t), 0.1)) t += 1 / 240; return t; })();
assert.ok(settleTime > 0.2 && settleTime < 0.45, `settles after ${settleTime}s`);
assert.ok(!settled({ x: 0.01, v: 30 }, 0.1), "a fast crossing is not settled");
console.log("motion: ok, settles after " + settleTime.toFixed(3) + " s");
