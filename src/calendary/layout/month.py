"""Events per cell of a month grid, all-day ones first. Not for the grid's dates; QML owns those."""
from calendary.layout.days import day_edges, on_day


def month(events, start, days=42):
    """For each of `days` cells from the day of `start`, the events touching that day, in the order given."""
    edges = day_edges(start, days)
    return [[e for e in events if on_day(e, edges[i], edges[i + 1])] for i in range(days)]
