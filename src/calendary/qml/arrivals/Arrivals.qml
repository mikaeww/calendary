pragma ComponentBehavior: Bound

import QtQuick
import Calendary
import "../theme"
import "../motion"
import "../calendar/dates.js" as Dates

// Banners for events other people just added to calendars shared with the user (docs/verification/arrivals.md).
// The newest sits on top; each leaves after a while, on click or when a fourth arrives. A click shows its day.
Item {
    id: stack

    readonly property int most: 3
    // Every banner has the same three lines, so one measured height places them all.
    readonly property real bannerHeight: 2 * Theme.space3 + micro.height + body.height + small.height + 2 * Theme.space1
    readonly property real step: bannerHeight + Theme.space2

    signal openDay(real day)

    function add(banner) {
        list.insert(0, Object.assign({
            gone: false
        }, banner));
        for (let i = most; i < list.count; i++)
            list.setProperty(i, "gone", true);
    }

    function when(banner) {
        const d = new Date(banner.start);
        const day = (banner.count > 1 ? "ab " : "") + Dates.weekdayShort[d.getDay()] + " " + d.getDate() + "." + (d.getMonth() + 1) + ".";
        if (banner.count > 1 || banner.allDay)
            return day;
        return day + " · " + Dates.time(banner.start) + "–" + Dates.time(banner.end);
    }

    width: 300
    height: list.count * step

    FontMetrics {
        id: micro

        font.family: Theme.fontUi
        font.pixelSize: Theme.fsMicro
    }

    FontMetrics {
        id: body

        font.family: Theme.fontUi
        font.pixelSize: Theme.fsBody
        font.bold: true
    }

    FontMetrics {
        id: small

        font.family: Theme.fontUi
        font.pixelSize: Theme.fsSmall
    }

    Connections {
        function onArrived(banner) {
            stack.add(banner);
        }

        target: Calendar
    }

    ListModel {
        id: list
    }

    Repeater {
        model: list

        Item {
            id: banner

            required property int index
            required property bool gone
            required property string title
            required property real start
            required property real end
            required property bool allDay
            required property string who
            required property string calendar
            required property string color
            required property int count

            function leave() {
                list.setProperty(index, "gone", true);
            }

            width: stack.width
            height: stack.bannerHeight
            y: place.value
            opacity: enter.value
            Accessible.role: Accessible.AlertMessage
            Accessible.name: title + ", " + stack.when(banner) + (who ? ", von " + who : "") + ", in " + calendar

            transform: Translate {
                // Reduced motion keeps the fade and drops the travel.
                x: Theme.reducedMotion ? 0 : (1 - enter.value) * 32
            }

            Component.onCompleted: {
                place.jump(index * stack.step);
                Qt.callLater(() => enter.target = 1);
            }
            onIndexChanged: place.target = index * stack.step
            onGoneChanged: if (gone)
                enter.target = 0

            Spring {
                id: enter

                // A fade stays with reduced motion; only the travel goes.
                instant: false
                precision: 0.002
                onValueChanged: if (banner.gone && value === 0)
                    list.remove(banner.index)
            }

            Spring {
                id: place
            }

            Timer {
                interval: 8000
                running: !hover.hovered && !banner.gone
                onTriggered: banner.leave()
            }

            HoverHandler {
                id: hover

                cursorShape: Qt.PointingHandCursor
            }

            TapHandler {
                onTapped: {
                    stack.openDay(banner.start);
                    banner.leave();
                }
            }

            Rectangle {
                anchors.fill: parent
                radius: Theme.radius
                color: hover.hovered ? Theme.raise3 : Theme.raise2

                Behavior on color {
                    ColorAnimation {
                        duration: Theme.motionFast
                    }
                }
            }

            Column {
                x: Theme.space3
                y: Theme.space3
                width: parent.width - 2 * Theme.space3
                spacing: Theme.space1

                Row {
                    width: parent.width
                    height: micro.height
                    spacing: Theme.space2

                    // The calendar's own colour, as a dot like in the sidebar (ADR 0003).
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        width: 8
                        height: 8
                        radius: 4
                        color: banner.color
                    }

                    Text {
                        width: parent.width - 8 - parent.spacing
                        text: banner.calendar
                        color: Theme.faint
                        font.family: Theme.fontUi
                        font.pixelSize: Theme.fsMicro
                        elide: Text.ElideRight
                    }
                }

                Text {
                    width: parent.width
                    height: body.height
                    text: banner.title || "Ohne Titel"
                    color: Theme.fg
                    font.family: Theme.fontUi
                    font.pixelSize: Theme.fsBody
                    font.bold: true
                    elide: Text.ElideRight
                }

                Text {
                    width: parent.width
                    height: small.height
                    text: stack.when(banner) + (banner.who ? " · von " + banner.who : "")
                    color: Theme.sub
                    font.family: Theme.fontUi
                    font.pixelSize: Theme.fsSmall
                    elide: Text.ElideRight
                }
            }
        }
    }
}
