pragma ComponentBehavior: Bound

import QtQuick
import Calendary
import "../theme"
import "../controls"

// New and existing events in one sheet. Read-only calendars show the same fields without actions.
Sheet {
    id: root

    // The event being edited ({key?, calendarKey?, start, end, allDay, ...}) or null when closed.
    property var ev: null
    property string calendarKey: ""
    property bool allDay: false
    property string repeat: ""
    property string error: ""
    property bool confirmDelete: false

    readonly property bool existing: !!(ev && ev.key)
    readonly property bool writable: !existing || !!ev.writable
    readonly property var calendars: Calendar.accounts.reduce((all, account) => all.concat(account.calendars.filter(cal => cal.writable || (root.ev && cal.key === root.ev.calendarKey))), [])
    readonly property var repeats: [["", "Einmalig"], ["DAILY", "Täglich"], ["WEEKLY", "Wöchentlich"], ["MONTHLY", "Monatlich"], ["YEARLY", "Jährlich"]]

    function save() {
        if (!writable) {
            dismissed();
            return;
        }
        const span = times.parse(new Date(ev.start).getFullYear());
        if (span.error || !calendarKey) {
            error = span.error || "Kein beschreibbarer Kalender";
            return;
        }
        Calendar.save({
            key: existing ? ev.key : "",
            calendarKey: calendarKey,
            title: title.text.trim(),
            location: place.text.trim(),
            notes: notes.text,
            allDay: allDay,
            start: span.start,
            end: span.end,
            repeat: existing ? "" : repeat
        });
        ev = null;
    }

    function remove() {
        if (!confirmDelete) {
            confirmDelete = true;
            return;
        }
        Calendar.remove(ev.key);
        ev = null;
    }

    open: ev !== null
    cardWidth: 460
    onDismissed: ev = null
    onAccepted: save()
    onEvChanged: {
        if (!ev)
            return;
        error = "";
        confirmDelete = false;
        allDay = !!ev.allDay;
        repeat = "";
        calendarKey = ev.calendarKey || (calendars.find(cal => cal.main && cal.writable) || calendars[0] || {
                key: ""
            }).key;
        title.text = ev.title || "";
        place.text = ev.location || "";
        notes.text = ev.notes || "";
        times.load(ev);
        if (!existing)
            Qt.callLater(() => title.input.forceActiveFocus());
    }

    Field {
        id: title

        width: parent.width
        size: Theme.fsHead
        placeholder: "Titel"
        input.readOnly: !root.writable
    }

    Flow {
        width: parent.width
        spacing: Theme.space1

        Repeater {
            model: root.calendars

            Chip {
                required property var modelData

                label: modelData.name
                dot: modelData.color
                active: root.calendarKey === modelData.key
                enabled: root.writable
                onClicked: root.calendarKey = modelData.key
            }
        }
    }

    EventTimes {
        id: times

        allDay: root.allDay
        editable: root.writable
    }

    Flow {
        visible: root.writable
        width: parent.width
        spacing: Theme.space1

        Chip {
            label: "Ganztägig"
            active: root.allDay
            onClicked: root.allDay = !root.allDay
        }

        Repeater {
            model: root.existing ? [] : root.repeats

            Chip {
                required property var modelData

                label: modelData[1]
                active: root.repeat === modelData[0]
                onClicked: root.repeat = modelData[0]
            }
        }
    }

    Text {
        visible: root.existing && (root.ev.recurring || !root.writable)
        width: parent.width
        text: !root.writable ? "Dieser Kalender ist nur lesbar." : "Teil einer Serie. Änderungen gelten nur für diesen Termin."
        color: Theme.sub
        font.family: Theme.fontUi
        font.pixelSize: Theme.fsSmall
        wrapMode: Text.Wrap
    }

    Field {
        id: place

        width: parent.width
        glyph: Theme.glyph.place
        placeholder: "Ort"
        input.readOnly: !root.writable
    }

    Rectangle {
        width: parent.width
        height: 5 * Theme.fsBody + 2 * Theme.space2
        radius: Theme.radiusSmall
        color: notes.activeFocus ? Theme.raise3 : Theme.raise2

        TextEdit {
            id: notes

            anchors.fill: parent
            anchors.margins: Theme.space2
            readOnly: !root.writable
            wrapMode: TextEdit.Wrap
            clip: true
            color: Theme.fg
            selectionColor: Theme.raise3
            selectedTextColor: Theme.fg
            selectByMouse: true
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsBody
            Accessible.name: "Notizen"

            Text {
                visible: notes.text === ""
                text: "Notizen"
                color: Theme.faint
                font: notes.font
            }
        }
    }

    Text {
        visible: root.error !== ""
        text: root.error
        color: Theme.fg
        font.family: Theme.fontUi
        font.pixelSize: Theme.fsBody
        font.bold: true
    }

    Item {
        width: parent.width
        height: Theme.ctlH

        Button {
            visible: root.existing && root.writable
            label: root.confirmDelete ? "Wirklich löschen?" : "Löschen"
            strong: root.confirmDelete
            onClicked: root.remove()
        }

        Row {
            anchors.right: parent.right
            spacing: Theme.space2

            Button {
                label: root.writable ? "Abbrechen" : "Schließen"
                onClicked: root.dismissed()
            }

            Button {
                visible: root.writable
                label: root.existing ? "Sichern" : "Anlegen"
                primary: true
                onClicked: root.save()
            }
        }
    }
}
