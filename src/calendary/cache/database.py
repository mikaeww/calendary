"""The SQLite cache: accounts, their calendars and the events of every window fetched so far.

Only the GUI thread uses a connection. Not for parsing Google resources (see events.py) or for layout.
"""
import os
import sqlite3

from calendary.cache.events import event_dict, event_key

DATABASE = os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"),
                        "calendary", "calendary.db")

SCHEMA = """
create table if not exists accounts (email text primary key);
create table if not exists calendars (
    account text, id text, name text, color text, writable int, main int,
    primary key (account, id));
create table if not exists events (
    account text, calendar text, id text, start int, end int, all_day int,
    title text, location text, notes text, recurring int, raw text,
    primary key (account, calendar, id));
create index if not exists events_span on events (start, end);
"""

# Overlap with [start, end); a zero-length event counts on its start. Shared by reads and window replacement.
OVERLAPS = "(e.end > ? or (e.end = e.start and e.start >= ?)) and e.start < ?"
EVENT_QUERY = ("select e.*, c.name as calendar_name, c.color, c.writable from events e"
               " join calendars c on c.account = e.account and c.id = e.calendar")


def connect(path=DATABASE):
    if path != ":memory:":
        os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def accounts(conn):
    return [row["email"] for row in conn.execute("select email from accounts order by rowid")]


def add_account(conn, email):
    with conn:
        conn.execute("insert or ignore into accounts values (?)", (email,))


def remove_account(conn, email):
    with conn:
        for table, column in (("events", "account"), ("calendars", "account"), ("accounts", "email")):
            conn.execute("delete from %s where %s = ?" % (table, column), (email,))


def calendars(conn, email):
    return conn.execute("select * from calendars where account = ? order by main desc, name", (email,)).fetchall()


def store_calendars(conn, email, items):
    """The account's calendar list becomes `items`; events of calendars that are gone go with them."""
    ids = [c["id"] for c in items]
    with conn:
        conn.execute("delete from calendars where account = ?", (email,))
        conn.executemany("insert into calendars values (?, ?, ?, ?, ?, ?)",
                         [(email, c["id"], c["name"], c["color"], c["writable"], c["main"]) for c in items])
        conn.execute("delete from events where account = ? and calendar not in (%s)" % ",".join("?" * len(ids)),
                     (email, *ids))


def put_events(conn, account, calendar, rows):
    conn.executemany(
        "insert or replace into events values (:account, :calendar, :id, :start, :end, :all_day,"
        " :title, :location, :notes, :recurring, :raw)",
        [dict(row, account=account, calendar=calendar) for row in rows])


def replace_window(conn, calendar_key, window, rows):
    """The events of one calendar overlapping window = (start, end) become exactly `rows`."""
    account, calendar = calendar_key
    with conn:
        conn.execute("delete from events as e where e.account = ? and e.calendar = ? and " + OVERLAPS,
                     (account, calendar, window[0], window[0], window[1]))
        put_events(conn, account, calendar, rows)


def delete_event(conn, account, calendar, event):
    """Part of the caller's transaction, so a delete and its replacement commit together."""
    conn.execute("delete from events where account = ? and calendar = ? and id = ?", (account, calendar, event))


def between(conn, start, end, hidden=()):
    """Visible events overlapping [start, end); a zero-length event counts on its start."""
    rows = conn.execute(
        EVENT_QUERY + " where " + OVERLAPS + " order by e.all_day desc, e.start, e.end desc", (start, start, end)).fetchall()
    return [event_dict(row) for row in rows if event_key(row["account"], row["calendar"]) not in hidden]
