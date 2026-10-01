pragma ComponentBehavior: Bound

import QtQuick
import Calendary
import "../theme"
import "dates.js" as Dates

// Six weeks of raised tiles with gaps between them; as many events as fit, the rest as "+n weitere".
Item {
    id: root

    required property real start
    required property real month
    required property real now
    required property int weekStart
    property real selected: -1
    signal openEvent(var ev)
    signal create(real start, real end, bool allDay)
    signal openDay(real day)

    readonly property var cells: Calendar.revision >= 0 ? Calendar.month(start) : []
    readonly property real column: width / 7
    readonly property real row: (height - names.height) / 6
    readonly property real line: Theme.fsSmall * 2 - 1
    readonly property int fits: Math.max(0, Math.floor((row - Theme.ctlH - Theme.space2) / line))

    Row {
        id: names

        height: Theme.ctlH + Theme.space1

        Repeater {
            model: 7

            Text {
                required property int index

                width: root.column
                height: names.height
                leftPadding: Theme.space3
                verticalAlignment: Text.AlignVCenter
                text: Dates.weekdayShort((root.weekStart + index) % 7)
                color: Theme.sub
                font.family: Theme.fontUi
                font.pixelSize: Theme.fsSmall
                font.bold: true
            }
        }
    }

    Repeater {
        model: 42

        Rectangle {
            id: cell

            required property int index
            readonly property real day: Dates.addDays(root.start, index)
            readonly property var events: root.cells[index] || []
            readonly property bool inMonth: new Date(day).getMonth() === new Date(root.month).getMonth()
            readonly property bool today: Dates.sameDay(day, root.now)
            readonly property int shown: events.length > root.fits ? Math.max(0, root.fits - 1) : events.length

            x: (index % 7) * root.column + Theme.space1 / 2
            y: names.height + Math.floor(index / 7) * root.row + Theme.space1 / 2
            width: root.column - Theme.space1
            height: root.row - Theme.space1
            radius: Theme.radius
            color: !inMonth ? "transparent" : root.selected === day ? Theme.raise2 : Theme.raise1

            Behavior on color {
                ColorAnimation {
                    duration: Theme.motionFast
                }
            }

            MouseArea {
                anchors.fill: parent
                onClicked: root.selected = cell.day
                onDoubleClicked: root.create(cell.day, Dates.addDays(cell.day, 1), true)
            }

            Rectangle {
                x: Theme.space1 + 2
                y: Theme.space1 + 2
                width: dayNumber.implicitWidth + 2 * Theme.space2
                height: Theme.ctlH - 4
                radius: Theme.radiusSmall - 2
                color: cell.today ? Theme.chipOn : numberHover.hovered ? Theme.raise3 : "transparent"
                Accessible.role: Accessible.Button
                Accessible.name: dayNumber.text

                Text {
                    id: dayNumber

                    anchors.centerIn: parent
                    text: new Date(cell.day).getDate() + (new Date(cell.day).getDate() === 1 ? ". " + Dates.monthName(new Date(cell.day).getMonth()) : "")
                    color: cell.today ? Theme.chipOnFg : cell.inMonth ? Theme.fg : Theme.faint
                    font.family: Theme.fontUi
                    font.pixelSize: Theme.fsBody
                    font.bold: cell.today || new Date(cell.day).getDate() === 1
                }

                HoverHandler {
                    id: numberHover

                    cursorShape: Qt.PointingHandCursor
                }

                TapHandler {
                    onTapped: root.openDay(cell.day)
                }
            }

            Column {
                x: Theme.space1
                y: Theme.ctlH + Theme.space1 + 2
                width: parent.width - 2 * Theme.space1
                opacity: cell.inMonth ? 1 : 0.55

                Repeater {
                    model: cell.events.slice(0, cell.shown)

                    EventChip {
                        required property var modelData

                        ev: modelData
                        width: parent.width
                        height: root.line - 1
                        past: modelData.end <= root.now
                        onClicked: root.openEvent(modelData)
                    }
                }

                Text {
                    visible: cell.events.length > cell.shown
                    leftPadding: Theme.space2
                    height: root.line
                    verticalAlignment: Text.AlignVCenter
                    text: qsTr("+%1 weitere").arg(cell.events.length - cell.shown)
                    color: Theme.sub
                    font.family: Theme.fontUi
                    font.pixelSize: Theme.fsMicro

                    TapHandler {
                        onTapped: root.openDay(cell.day)
                    }
                }
            }
        }
    }
}
