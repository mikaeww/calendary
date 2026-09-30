pragma ComponentBehavior: Bound

import QtQuick
import "../theme"
import "dates.js" as Dates

// Day names and numbers above the week, then the all-day strip with its bars in lanes.
Item {
    id: root

    required property real start
    required property int days
    required property real now
    required property var layout
    required property real gutter
    required property real column
    signal openEvent(var ev)
    signal create(real start, real end, bool allDay)
    signal openDay(real day)

    readonly property real lane: Theme.ctlH - 2

    implicitHeight: names.height + strip.height

    Item {
        id: names

        width: parent.width
        height: Theme.ctlH + Theme.space3

        Repeater {
            model: root.days

            Item {
                id: head

                required property int index
                readonly property real day: Dates.addDays(root.start, index)
                readonly property bool today: Dates.sameDay(day, root.now)

                x: root.gutter + index * root.column
                width: root.column
                height: names.height

                Rectangle {
                    anchors.centerIn: parent
                    width: label.implicitWidth + 2 * Theme.space2 + 2
                    height: Theme.ctlH
                    radius: Theme.radiusSmall
                    color: head.today ? Theme.chipOn : hover.hovered ? Theme.raise2 : "transparent"
                    Accessible.role: Accessible.Button
                    Accessible.name: label.text

                    Text {
                        id: label

                        anchors.centerIn: parent
                        text: Dates.weekdayShort[new Date(head.day).getDay()] + " " + new Date(head.day).getDate()
                        color: head.today ? Theme.chipOnFg : Theme.fg
                        font.family: Theme.fontUi
                        font.pixelSize: Theme.fsBody
                        font.bold: true
                    }

                    HoverHandler {
                        id: hover

                        cursorShape: Qt.PointingHandCursor
                    }

                    TapHandler {
                        onTapped: root.openDay(head.day)
                    }
                }
            }
        }
    }

    Item {
        id: strip

        y: names.height
        width: parent.width
        height: Math.max(1, root.layout.lanes || 0) * root.lane + Theme.space1

        Text {
            width: root.gutter - Theme.space2
            height: root.lane
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            text: "ganztägig"
            color: Theme.faint
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsMicro
        }

        MouseArea {
            x: root.gutter
            width: parent.width - x
            height: parent.height
            onDoubleClicked: mouse => {
                const day = Dates.addDays(root.start, Math.floor(mouse.x / root.column));
                root.create(day, Dates.addDays(day, 1), true);
            }
        }

        Repeater {
            model: root.layout.bars || []

            EventChip {
                required property var modelData

                ev: modelData
                filled: true
                past: modelData.end <= root.now
                x: root.gutter + modelData.first * root.column + Theme.space1 / 2
                y: modelData.lane * root.lane
                width: modelData.span * root.column - Theme.space1
                height: root.lane - Theme.space1 / 2
                onClicked: root.openEvent(modelData)
            }
        }
    }
}
