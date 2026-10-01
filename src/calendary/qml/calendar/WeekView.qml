pragma ComponentBehavior: Bound

import QtQuick
import Calendary
import "../theme"
import "dates.js" as Dates

// The week: a header, then one raised column per day on a scrolling hour scale you can draw events into.
Item {
    id: root

    required property real start
    required property int days
    required property real now
    property real hourHeight: Preferences.get("hourHeight", 52)
    // The slot being drawn or waiting in the editor: {day, from, to} in minutes, or null.
    property var ghost: null
    signal openEvent(var ev)
    signal create(real start, real end, bool allDay)
    signal openDay(real day)

    readonly property var layout: Calendar.revision >= 0 ? Calendar.week(start, days) : ({})
    readonly property real gutter: 64
    readonly property real column: (width - gutter) / days
    readonly property int todayIndex: {
        for (let i = 0; i < days; i++)
            if (Dates.sameDay(Dates.addDays(start, i), now))
                return i;
        return -1;
    }

    function snap(minutes) {
        return Math.round(minutes / 15) * 15;
    }

    function minutesAt(y) {
        return Math.max(0, Math.min(24 * 60, snap(y * 60 / hourHeight)));
    }

    function scrollToMorning() {
        const minutes = todayIndex >= 0 ? Dates.minutesOf(now) - 120 : 7 * 60;
        grid.contentY = Math.max(0, Math.min(grid.contentHeight - grid.height, minutes * hourHeight / 60));
    }

    Component.onCompleted: Qt.callLater(scrollToMorning)

    WeekHeader {
        id: header

        width: parent.width
        start: root.start
        days: root.days
        now: root.now
        layout: root.layout
        gutter: root.gutter
        column: root.column
        onOpenEvent: ev => root.openEvent(ev)
        onCreate: (start, end, allDay) => root.create(start, end, allDay)
        onOpenDay: day => root.openDay(day)
    }

    Flickable {
        id: grid

        y: header.height + Theme.space1
        width: parent.width
        height: parent.height - y
        contentWidth: width
        contentHeight: canvas.height
        boundsBehavior: Flickable.StopAtBounds
        clip: true

        WheelHandler {
            acceptedModifiers: Qt.ControlModifier
            onWheel: event => {
                const minutes = (grid.contentY + event.y) * 60 / root.hourHeight;
                root.hourHeight = Math.max(32, Math.min(120, root.hourHeight * (event.angleDelta.y > 0 ? 1.12 : 1 / 1.12)));
                grid.contentY = Math.max(0, Math.min(grid.contentHeight - grid.height, minutes * root.hourHeight / 60 - event.y));
                Preferences.set("hourHeight", Math.round(root.hourHeight));
            }
        }

        Item {
            id: canvas

            width: grid.width
            height: 24 * root.hourHeight

            Repeater {
                model: 23

                Text {
                    required property int index

                    width: root.gutter - Theme.space2
                    y: (index + 1) * root.hourHeight - height / 2
                    horizontalAlignment: Text.AlignRight
                    text: Dates.pad(index + 1) + ":00"
                    color: Theme.faint
                    font.family: Theme.fontUi
                    font.pixelSize: Theme.fsMicro
                }
            }

            Repeater {
                model: root.days

                Rectangle {
                    id: dayColumn

                    required property int index

                    x: root.gutter + index * root.column + Theme.space1 / 2
                    width: root.column - Theme.space1
                    height: canvas.height
                    radius: Theme.radius
                    color: index === root.todayIndex ? Theme.mix(Theme.raise1, Theme.raise2, 0.5) : Theme.raise1

                    // Every other hour a half step brighter; hours 23-24 stay plain so the band never cuts the corner.
                    Repeater {
                        model: 11

                        Rectangle {
                            required property int index

                            y: (2 * index + 1) * root.hourHeight
                            width: dayColumn.width
                            height: root.hourHeight
                            color: Theme.mix(dayColumn.color, Theme.raise2, 0.35)
                        }
                    }
                }
            }

            MouseArea {
                id: draw

                property real pressX: 0
                property real pressY: 0
                property bool drawing: false

                function slot(x, y1, y2) {
                    const day = Math.max(0, Math.min(root.days - 1, Math.floor(x / root.column)));
                    const a = root.minutesAt(Math.min(y1, y2));
                    const b = root.minutesAt(Math.max(y1, y2));
                    return {
                        day: day,
                        from: Math.min(a, 24 * 60 - 15),
                        to: Math.max(b, a + 15)
                    };
                }

                function propose(s) {
                    root.ghost = s;
                    const day = Dates.addDays(root.start, s.day);
                    root.create(Dates.atMinutes(day, s.from), Dates.atMinutes(day, s.to), false);
                }

                x: root.gutter
                width: parent.width - x
                height: parent.height
                preventStealing: true
                onPressed: mouse => {
                    pressX = mouse.x;
                    pressY = mouse.y;
                    drawing = false;
                }
                onPositionChanged: mouse => {
                    if (!drawing && Math.abs(mouse.y - pressY) > 6)
                        drawing = true;
                    if (drawing)
                        root.ghost = slot(pressX, pressY, mouse.y);
                }
                onReleased: {
                    if (drawing && root.ghost)
                        propose(root.ghost);
                    drawing = false;
                }
                onDoubleClicked: mouse => {
                    const from = Math.floor(mouse.y * 60 / root.hourHeight / 30) * 30;
                    propose({
                        day: slot(mouse.x, mouse.y, mouse.y).day,
                        from: Math.min(from, 23 * 60),
                        to: Math.min(24 * 60, from + 60)
                    });
                }
            }

            Rectangle {
                visible: root.ghost !== null
                x: root.gutter + (root.ghost ? root.ghost.day : 0) * root.column + Theme.space1
                y: (root.ghost ? root.ghost.from : 0) * root.hourHeight / 60 + 1
                width: root.column - 2 * Theme.space1
                height: root.ghost ? Math.max(Theme.ctlH, (root.ghost.to - root.ghost.from) * root.hourHeight / 60 - 2) : 0
                radius: Theme.radiusSmall
                color: Theme.raise3

                Text {
                    x: Theme.space2
                    y: Theme.space1 + 2
                    text: root.ghost ? qsTr("Neuer Termin") + "\n" + Dates.time(Dates.atMinutes(0, root.ghost.from)) + " – " + Dates.time(Dates.atMinutes(0, root.ghost.to)) : ""
                    color: Theme.fg
                    font.family: Theme.fontUi
                    font.pixelSize: Theme.fsSmall
                }
            }

            Repeater {
                model: root.layout.days || []

                Item {
                    id: timed

                    required property var modelData
                    required property int index

                    x: root.gutter + index * root.column + Theme.space1
                    width: root.column - 2 * Theme.space1
                    height: canvas.height

                    Repeater {
                        model: timed.modelData

                        EventBlock {
                            required property var modelData

                            ev: modelData
                            view: root
                            past: modelData.end <= root.now
                            x: modelData.col * timed.width / modelData.cols
                            y: modelData.top * root.hourHeight / 60 + 1
                            width: timed.width / modelData.cols - (modelData.cols > 1 ? 2 : 0)
                            height: Math.max(Theme.fsSmall + 8, (modelData.bottom - modelData.top + endShift) * root.hourHeight / 60 - 2)
                        }
                    }
                }
            }

            Item {
                visible: root.todayIndex >= 0
                y: Dates.minutesOf(root.now) * root.hourHeight / 60
                width: canvas.width
                z: 5

                Rectangle {
                    x: root.gutter + root.todayIndex * root.column + Theme.space1 / 2
                    y: -1
                    width: root.column - Theme.space1
                    height: 2
                    color: Theme.fg
                }

                Rectangle {
                    x: root.gutter - nowLabel.implicitWidth - Theme.space2 - 2
                    y: -height / 2
                    width: nowLabel.implicitWidth + Theme.space2
                    height: Theme.fsMicro + 8
                    radius: Theme.radiusSmall - 2
                    color: Theme.chipOn

                    Text {
                        id: nowLabel

                        anchors.centerIn: parent
                        text: Dates.time(root.now)
                        color: Theme.chipOnFg
                        font.family: Theme.fontUi
                        font.pixelSize: Theme.fsMicro
                        font.bold: true
                    }
                }
            }
        }
    }
}
