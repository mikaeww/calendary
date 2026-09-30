pragma ComponentBehavior: Bound

import QtQuick
import "../theme"
import "../controls"
import "../calendar/dates.js" as Dates

// Start and end of an event as editable date and time fields; parse() turns them into milliseconds or an error.
Grid {
    id: root

    property bool allDay: false
    property bool editable: true

    function load(ev) {
        startDate.text = Dates.date(ev.start);
        startTime.text = Dates.time(ev.start);
        // All-day ends are exclusive; the fields show the last day.
        endDate.text = Dates.date(ev.allDay ? Math.max(ev.start, Dates.addDays(ev.end, -1)) : ev.end);
        endTime.text = Dates.time(ev.end);
    }

    // {start, end} or {error}; the year falls back to the event's own year.
    function parse(year) {
        const first = Dates.parseDate(startDate.text, year);
        const last = Dates.parseDate(endDate.text, year);
        const from = Dates.parseTime(startTime.text);
        const to = Dates.parseTime(endTime.text);
        if (isNaN(first) || isNaN(last))
            return {
                error: "Datum als TT.MM.JJJJ eingeben"
            };
        if (!allDay && (isNaN(from) || isNaN(to)))
            return {
                error: "Uhrzeit als HH:MM eingeben"
            };
        const start = allDay ? first : Dates.atMinutes(first, from);
        const end = allDay ? Dates.addDays(last, 1) : Dates.atMinutes(last, to);
        return end > start ? {
            start: start,
            end: end
        } : {
            error: "Das Ende liegt vor dem Beginn"
        };
    }

    columns: 3
    columnSpacing: Theme.space2
    rowSpacing: Theme.space2
    verticalItemAlignment: Grid.AlignVCenter

    Text {
        width: 56
        text: "Beginn"
        color: Theme.sub
        font.family: Theme.fontUi
        font.pixelSize: Theme.fsBody
    }

    Field {
        id: startDate

        width: 124
        placeholder: "TT.MM.JJJJ"
        input.readOnly: !root.editable
    }

    Field {
        id: startTime

        visible: !root.allDay
        width: 72
        placeholder: "HH:MM"
        input.readOnly: !root.editable
    }

    Text {
        width: 56
        text: "Ende"
        color: Theme.sub
        font.family: Theme.fontUi
        font.pixelSize: Theme.fsBody
    }

    Field {
        id: endDate

        width: 124
        placeholder: "TT.MM.JJJJ"
        input.readOnly: !root.editable
    }

    Field {
        id: endTime

        visible: !root.allDay
        width: 72
        placeholder: "HH:MM"
        input.readOnly: !root.editable
    }
}
