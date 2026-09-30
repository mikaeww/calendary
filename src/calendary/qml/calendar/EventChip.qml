pragma ComponentBehavior: Bound

import QtQuick
import "../theme"
import "dates.js" as Dates

// One line for an event: a raised bar for all-day events, a dot, time and title for timed ones in the month.
Rectangle {
    id: chip

    required property var ev
    property bool filled: ev.allDay
    property bool past: false
    signal clicked

    implicitHeight: Theme.fsSmall * 2 - 2
    radius: Theme.radiusSmall - 2
    color: filled ? (hover.hovered ? Theme.raise3 : Theme.raise2) : hover.hovered ? Theme.raise2 : "transparent"
    Accessible.role: Accessible.Button
    Accessible.name: ev.title + ", " + Dates.span(ev)

    Behavior on color {
        ColorAnimation {
            duration: Theme.motionFast
        }
    }

    Row {
        x: Theme.space1 + 2
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width - 2 * x
        spacing: Theme.space1 + 2

        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: 6
            height: 6
            radius: 3
            color: chip.ev.color
            opacity: chip.past ? 0.5 : 1
        }

        Text {
            id: when

            visible: !chip.ev.allDay
            text: Dates.time(chip.ev.start)
            color: Theme.faint
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsMicro
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            width: parent.width - 12 - (when.visible ? when.implicitWidth + 6 : 0)
            anchors.verticalCenter: parent.verticalCenter
            text: chip.ev.title || "(Ohne Titel)"
            color: chip.past ? Theme.sub : Theme.fg
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsSmall
            font.bold: chip.filled
            elide: Text.ElideRight
        }
    }

    HoverHandler {
        id: hover

        cursorShape: Qt.PointingHandCursor
    }

    TapHandler {
        onTapped: chip.clicked()
    }
}
