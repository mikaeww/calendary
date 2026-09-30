.pragma library

// Critically damped spring, solved analytically: error x = value - target decays as (x0 + (v0 + w x0) t) e^(-w t).
// Evaluated from absolute local time, so the path is the same at any refresh rate.
function critical(x0, v0, omega, t) {
    var decay = Math.exp(-omega * t);
    var slope = v0 + omega * x0;
    return { x: (x0 + slope * t) * decay, v: (v0 - omega * t * slope) * decay };
}

// Settled when the rest and the next frame's predicted move are both below the visible precision.
function settled(state, precision) {
    return Math.abs(state.x) < precision && Math.abs(state.v) / 60 < precision;
}
