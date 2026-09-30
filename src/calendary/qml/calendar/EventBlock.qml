pragma ComponentBehavior: Bound

import QtQuick
import Calendary
import "../theme"
import "dates.js" as Dates

// A timed event in the week grid: click opens it, dragging moves it (across days too), the lower edge resizes it.
Rectangle {
    id: block

    required property var ev
    required property var view
    property bool past: false
    property int dayShift: 0
    property int minuteShift: 0
    property int endShift: 0
    property string mode: ""
    readonly property bool dragging: mode !== ""
    readonly property real shownStart: Dates.addDays(ev.start, dayShift) + minuteShift * 60000
    readonly property real shownEnd: mode === "resize" ? Math.max(ev.start + 900000, ev.end + endShift * 60000) : Dates.addDays(ev.end, dayShift) + minuteShift * 60000

    radius: Theme.radiusSmall
    color: dragging || pointer.containsMouse ? Theme.raise3 : Theme.raise2
    z: dragging ? 10 : 1
    clip: true
    Accessible.role: Accessible.Button
    Accessible.name: ev.title + ", " + Dates.span(ev)

    Behavior on color {
        ColorAnimation {
            duration: Theme.motionFast
        }
    }

    transform: Translate {
        x: block.dayShift * block.view.column
        y: block.minuteShift * block.view.hourHeight / 60
    }

    Column {
        x: Theme.space2
        y: block.height >= 34 ? Theme.space1 + 2 : Math.max(0, (block.height - Theme.fsSmall - 4) / 2)
        width: block.width - 2 * Theme.space2

        Row {
            width: parent.width
            spacing: Theme.space1 + 2

            Rectangle {
                y: (Theme.fsSmall + 4 - height) / 2
                width: 6
                height: 6
                radius: 3
                color: block.ev.color
                opacity: block.past ? 0.5 : 1
            }

            Text {
                width: parent.width - 12
                text: block.ev.title || "(Ohne Titel)"
                color: block.past && !block.dragging ? Theme.sub : Theme.fg
                font.family: Theme.fontUi
                font.pixelSize: Theme.fsSmall
                font.bold: true
                elide: Text.ElideRight
                wrapMode: Text.Wrap
                maximumLineCount: Math.max(1, Math.floor((block.height - 24) / (Theme.fsSmall + 3)))
            }
        }

        Text {
            visible: block.height >= 34
            width: parent.width
            text: Dates.time(block.shownStart) + " – " + Dates.time(block.shownEnd) + (block.ev.location ? " · " + block.ev.location : "")
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsMicro
            elide: Text.ElideRight
        }
    }

    MouseArea {
        id: pointer

        property real pressX: 0
        property real pressY: 0
        property bool pressedEdge: false

        anchors.fill: parent
        hoverEnabled: true
        preventStealing: true
        cursorShape: block.mode === "move" ? Qt.ClosedHandCursor : block.ev.writable && mouseY > height - 7 ? Qt.SizeVerCursor : Qt.PointingHandCursor

        onPressed: mouse => {
            const at = mapToItem(block.view, mouse.x, mouse.y);
            pressX = at.x;
            pressY = at.y;
            pressedEdge = mouse.y > height - 7;
        }
        onPositionChanged: mouse => {
            if (!pressed || !block.ev.writable)
                return;
            const at = mapToItem(block.view, mouse.x, mouse.y);
            const dx = at.x - pressX;
            const dy = at.y - pressY;
            if (!block.dragging) {
                if (Math.abs(dx) < 5 && Math.abs(dy) < 5)
                    return;
                block.mode = pressedEdge ? "resize" : "move";
            }
            const minutes = block.view.snap(dy * 60 / block.view.hourHeight);
            if (block.mode === "resize") {
                block.endShift = minutes;
            } else {
                block.minuteShift = minutes;
                block.dayShift = Math.round(dx / block.view.column);
            }
        }
        onReleased: {
            if (!block.dragging) {
                block.view.openEvent(block.ev);
                return;
            }
            const changed = block.dayShift !== 0 || block.minuteShift !== 0 || block.endShift !== 0;
            const fields = {
                key: block.ev.key,
                calendarKey: block.ev.calendarKey,
                title: block.ev.title,
                location: block.ev.location,
                notes: block.ev.notes,
                allDay: false,
                start: block.shownStart,
                end: block.shownEnd
            };
            block.reset();
            if (changed)
                Calendar.save(fields);
        }
        onCanceled: block.reset()
    }

    function reset() {
        mode = "";
        dayShift = 0;
        minuteShift = 0;
        endShift = 0;
    }
}
