"""A week's layout: all-day bars in lanes and timed events side by side where they overlap.

Minutes are counted from each local midnight. Not for drawing or for events that span the strip (see days.is_long).
"""
from calendary.layout.days import day_edges, is_long, on_day

MINIMUM_MINUTES = 20


def week(events, start, days):
    """{"bars": all-day bars with first/span/lane, "lanes": count, "days": timed events per day with top/bottom/col/cols}."""
    edges = day_edges(start, days)
    bars, lanes = all_day_bars([e for e in events if is_long(e)], edges)
    columns = []
    for i in range(days):
        timed = [e for e in events if not is_long(e) and on_day(e, edges[i], edges[i + 1])]
        length = (edges[i + 1] - edges[i]) / 60000
        columns.append(side_by_side([dict(e, top=max(0, (e["start"] - edges[i]) / 60000),
                                          bottom=min(length, (e["end"] - edges[i]) / 60000)) for e in timed]))
    return {"bars": bars, "lanes": lanes, "days": columns}


def all_day_bars(events, edges):
    """Greedy lanes in start order, which uses as few lanes as the busiest day needs."""
    days = len(edges) - 1
    bars, lane_free = [], []
    for ev in sorted(events, key=lambda e: (e["start"], -e["end"])):
        covered = [i for i in range(days) if on_day(ev, edges[i], edges[i + 1])]
        if not covered:
            continue
        first, last = covered[0], covered[-1]
        lane = next((i for i, free in enumerate(lane_free) if free <= first), len(lane_free))
        if lane == len(lane_free):
            lane_free.append(0)
        lane_free[lane] = last + 1
        bars.append(dict(ev, first=first, span=last - first + 1, lane=lane))
    return bars, len(lane_free)


def side_by_side(events):
    """Assigns col and cols: events that overlap share the width of their cluster, like Apple Calendar."""
    placed, cluster, cluster_end = [], [], -1
    for ev in sorted(events, key=lambda e: (e["top"], -e["bottom"])):
        ev["bottom"] = max(ev["bottom"], ev["top"] + MINIMUM_MINUTES)
        if cluster and ev["top"] >= cluster_end:
            placed += columns_for(cluster)
            cluster = []
        cluster_end = max(cluster_end, ev["bottom"]) if cluster else ev["bottom"]
        cluster.append(ev)
    return placed + columns_for(cluster)


def columns_for(cluster):
    """Greedy columns in start order; for intervals this needs exactly as many columns as the deepest overlap."""
    ends = []
    for ev in cluster:
        col = next((i for i, end in enumerate(ends) if end <= ev["top"]), len(ends))
        if col == len(ends):
            ends.append(0)
        ends[col] = ev["bottom"]
        ev["col"] = col
    for ev in cluster:
        ev["cols"] = len(ends)
    return cluster
