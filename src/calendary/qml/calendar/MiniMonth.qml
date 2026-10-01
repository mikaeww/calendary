pragma ComponentBehavior: Bound

import QtQuick
import "../theme"
import "../controls"
import "dates.js" as Dates

// The small month in the sidebar: pages on its own, marks the range on screen, a click jumps there.
Rectangle {
    id: root

    required property real anchor
    required property real rangeStart
    required property real rangeEnd
    required property real now
    required property int weekStart
    property real shown: anchor
    signal picked(real day)

    readonly property real gridStart: Dates.monthGrid(shown, weekStart)
    readonly property real cell: (width - 2 * Theme.pad) / 7
    // Grid index of the first day on screen, only when a week is on screen; a whole month needs no mark.
    readonly property int rangeIndex: {
        if (Dates.addDays(rangeStart, 8) <= rangeEnd)
            return -1;
        for (let i = 0; i < 42; i++)
            if (Dates.addDays(gridStart, i) === rangeStart)
                return i;
        return -1;
    }
    readonly property int rangeDays: Math.round((rangeEnd - rangeStart) / 86400000)

    onAnchorChanged: shown = anchor
    implicitHeight: content.implicitHeight + 2 * Theme.pad
    radius: Theme.radius
    color: Theme.raise1

    Column {
        id: content

        x: Theme.pad
        y: Theme.pad
        width: parent.width - 2 * Theme.pad
        spacing: Theme.space1

        Item {
            width: parent.width
            height: Theme.ctlH

            Text {
                anchors.verticalCenter: parent.verticalCenter
                x: Theme.space1
                text: Dates.monthName(new Date(root.shown).getMonth()) + " " + new Date(root.shown).getFullYear()
                color: Theme.fg
                font.family: Theme.fontUi
                font.pixelSize: Theme.fsBody
                font.bold: true
            }

            Row {
                anchors.right: parent.right

                IconButton {
                    glyph: Theme.glyph.left
                    label: qsTr("Voriger Monat")
                    onClicked: root.shown = Dates.addMonths(root.shown, -1)
                }

                IconButton {
                    glyph: Theme.glyph.right
                    label: qsTr("Nächster Monat")
                    onClicked: root.shown = Dates.addMonths(root.shown, 1)
                }
            }
        }

        Item {
            width: days.width
            height: days.height

            Rectangle {
                visible: root.rangeIndex >= 0
                x: (root.rangeIndex % 7) * root.cell
                y: Theme.fsMicro * 2 + Math.floor(root.rangeIndex / 7) * (Theme.ctlH - 4)
                width: root.rangeDays * root.cell
                height: Theme.ctlH - 4
                radius: Theme.radiusSmall - 2
                color: Theme.raise2
            }

            Grid {
                id: days

                columns: 7

                Repeater {
                    model: 7

                    Text {
                        required property int index

                        width: root.cell
                        height: Theme.fsMicro * 2
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        text: Dates.weekdayShort((root.weekStart + index) % 7).charAt(0)
                        color: Theme.faint
                        font.family: Theme.fontUi
                        font.pixelSize: Theme.fsMicro
                    }
                }

                Repeater {
                    model: 42

                    Rectangle {
                        id: day

                        required property int index
                        readonly property real date: Dates.addDays(root.gridStart, index)
                        readonly property bool today: Dates.sameDay(date, root.now)

                        width: root.cell
                        height: Theme.ctlH - 4
                        radius: Theme.radiusSmall - 2
                        color: today ? Theme.chipOn : hover.hovered ? Theme.raise3 : "transparent"
                        Accessible.role: Accessible.Button
                        Accessible.name: Dates.date(date)

                        Text {
                            anchors.centerIn: parent
                            text: new Date(day.date).getDate()
                            color: day.today ? Theme.chipOnFg : new Date(day.date).getMonth() === new Date(root.shown).getMonth() ? Theme.fg : Theme.faint
                            font.family: Theme.fontUi
                            font.pixelSize: Theme.fsSmall
                            font.bold: day.today
                        }

                        HoverHandler {
                            id: hover

                            cursorShape: Qt.PointingHandCursor
                        }

                        TapHandler {
                            onTapped: root.picked(day.date)
                        }
                    }
                }
            }
        }
    }
}
