pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Window
import Calendary
import "theme"
import "motion"
import "controls"
import "calendar"
import "sidebar"
import "sheets"
import "calendar/dates.js" as Dates

// The window: sidebar left, toolbar and the week or month right, sheets on top.
Window {
    id: win

    property string view: Preferences.get("view", "week")
    property int weekStart: Preferences.get("weekStart", 1)
    property bool workWeek: Preferences.get("workWeek", false)
    // The day everything is about; the views derive their range from it.
    property real anchor: Dates.day(Date.now())
    property real now: Date.now()
    property bool settingsOpen: false

    readonly property bool compact: width < 900
    readonly property bool sheetOpen: settingsOpen || editor.open
    readonly property real rangeStart: view === "month" ? Dates.monthGrid(anchor, weekStart) : Dates.startOfWeek(anchor, workWeek ? 1 : weekStart)
    readonly property int days: view === "month" ? 42 : workWeek ? 5 : 7
    readonly property real rangeEnd: Dates.addDays(rangeStart, days)
    readonly property real middle: view === "month" ? anchor : Dates.addDays(rangeStart, Math.floor(days / 2))

    function setPreference(key, value) {
        Preferences.set(key, value);
        if (key === "weekStart")
            weekStart = value;
        else if (key === "workWeek")
            workWeek = value;
    }

    function setView(next) {
        if (next === view)
            return;
        view = next;
        Preferences.set("view", next);
    }

    // One page back or forth; the stage slides in from the side it is heading to.
    function go(delta) {
        anchor = view === "month" ? Dates.addMonths(anchor, delta) : Dates.addDays(anchor, 7 * delta);
        stage.nudge(delta);
    }

    function jump(day) {
        const before = rangeStart;
        anchor = Dates.day(day);
        if (rangeStart !== before)
            stage.nudge(rangeStart > before ? 1 : -1);
    }

    function today() {
        jump(Date.now());
        weekView.scrollToMorning();
    }

    function create(start, end, allDay) {
        if (!Calendar.accounts.some(account => account.calendars.some(cal => cal.writable))) {
            weekView.ghost = null;
            toast.show(Calendar.accounts.length ? "Kein beschreibbarer Kalender" : "Zuerst mit Google anmelden", false);
            return;
        }
        editor.ev = {
            start: start,
            end: end,
            allDay: allDay
        };
    }

    function createNow() {
        const start = Dates.atMinutes(anchor, Math.min(22 * 60, (new Date().getHours() + 1) * 60));
        create(start, start + 3600000, false);
    }

    width: Preferences.get("width", 1240)
    height: Preferences.get("height", 800)
    minimumWidth: 560
    minimumHeight: 480
    visible: true
    color: Theme.bg
    title: "Calendary – " + Dates.monthNames[new Date(middle).getMonth()] + " " + new Date(middle).getFullYear()

    Component.onCompleted: Calendar.show(rangeStart, rangeEnd)
    onRangeStartChanged: Calendar.show(rangeStart, rangeEnd)
    onDaysChanged: Calendar.show(rangeStart, rangeEnd)
    onActiveChanged: if (active)
        Calendar.show(rangeStart, rangeEnd)
    onWidthChanged: sizeSave.restart()
    onHeightChanged: sizeSave.restart()

    Connections {
        function onNotice(text, bad) {
            toast.show(text, bad);
        }

        target: Calendar
    }

    Timer {
        interval: 30000
        running: true
        repeat: true
        onTriggered: win.now = Date.now()
    }

    Timer {
        id: sizeSave

        interval: 400
        onTriggered: {
            Preferences.set("width", win.width);
            Preferences.set("height", win.height);
        }
    }

    Shortcut {
        sequence: "T"
        enabled: !win.sheetOpen
        onActivated: win.today()
    }

    Shortcut {
        sequence: "W"
        enabled: !win.sheetOpen
        onActivated: win.setView("week")
    }

    Shortcut {
        sequence: "M"
        enabled: !win.sheetOpen
        onActivated: win.setView("month")
    }

    Shortcut {
        sequences: ["Left", "J"]
        enabled: !win.sheetOpen
        onActivated: win.go(-1)
    }

    Shortcut {
        sequences: ["Right", "K"]
        enabled: !win.sheetOpen
        onActivated: win.go(1)
    }

    Shortcut {
        sequences: ["N", "Ctrl+N"]
        enabled: !win.sheetOpen
        onActivated: win.createNow()
    }

    Shortcut {
        sequence: "Ctrl+R"
        onActivated: Calendar.refresh()
    }

    Shortcut {
        sequence: "Ctrl+,"
        onActivated: win.settingsOpen = !win.settingsOpen
    }

    Shortcut {
        sequence: "Ctrl+Q"
        onActivated: win.close()
    }

    Sidebar {
        id: sidebar

        visible: !win.compact
        x: Theme.space4
        y: Theme.space4
        width: win.compact ? 0 : 248
        height: win.height - 2 * Theme.space4
        app: win
    }

    Item {
        id: main

        x: win.compact ? Theme.space4 : sidebar.x + sidebar.width + Theme.space5
        y: Theme.space4
        width: win.width - x - Theme.space4
        height: win.height - 2 * Theme.space4

        Item {
            id: toolbar

            width: parent.width
            height: Theme.ctlH + Theme.space2

            Row {
                anchors.verticalCenter: parent.verticalCenter
                spacing: Theme.space2

                Text {
                    anchors.baseline: year.baseline
                    text: Dates.monthNames[new Date(win.middle).getMonth()]
                    color: Theme.fg
                    font.family: Theme.fontUi
                    font.pixelSize: Theme.fsDisplay
                    font.bold: true
                    font.letterSpacing: -0.5
                }

                Text {
                    id: year

                    text: new Date(win.middle).getFullYear()
                    color: Theme.sub
                    font.family: Theme.fontUi
                    font.pixelSize: Theme.fsDisplay
                }
            }

            Row {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: Theme.space2

                Segmented {
                    options: [["week", "Woche"], ["month", "Monat"]]
                    current: win.view
                    onPicked: value => win.setView(value)
                }

                Row {
                    spacing: Theme.space1

                    IconButton {
                        glyph: Theme.glyph.left
                        label: win.view === "month" ? "Voriger Monat" : "Vorige Woche"
                        onClicked: win.go(-1)
                    }

                    Button {
                        label: "Heute"
                        onClicked: win.today()
                    }

                    IconButton {
                        glyph: Theme.glyph.right
                        label: win.view === "month" ? "Nächster Monat" : "Nächste Woche"
                        onClicked: win.go(1)
                    }
                }

                IconButton {
                    glyph: Theme.glyph.plus
                    label: "Neuer Termin"
                    onClicked: win.createNow()
                }

                IconButton {
                    visible: win.compact
                    glyph: Theme.glyph.settings
                    label: "Einstellungen"
                    onClicked: win.settingsOpen = true
                }
            }
        }

        Item {
            id: stage

            // Pixels a page travels; reduced motion swaps the travel for a plain fade.
            readonly property real distance: Theme.reducedMotion ? 0 : 36
            readonly property real fade: 1 - Math.min(1, Math.abs(slide.value) / 36) * 0.85

            function nudge(direction) {
                slide.jump(direction * 36);
                slide.target = 0;
            }

            y: toolbar.height + Theme.space3
            width: parent.width
            height: parent.height - y
            clip: true

            Spring {
                id: slide

                instant: false
            }

            Spring {
                id: morph

                precision: 0.002
                target: win.view === "month" ? 1 : 0
            }

            WeekView {
                id: weekView

                width: stage.width
                height: stage.height
                start: win.view === "month" ? Dates.startOfWeek(win.anchor, win.workWeek ? 1 : win.weekStart) : win.rangeStart
                days: win.workWeek ? 5 : 7
                now: win.now
                visible: opacity > 0.01
                enabled: win.view === "week"
                opacity: (1 - morph.value) * (win.view === "week" ? stage.fade : 1)
                onOpenEvent: ev => editor.ev = ev
                onCreate: (start, end, allDay) => win.create(start, end, allDay)
                onOpenDay: day => win.jump(day)

                transform: Translate {
                    x: win.view === "week" ? slide.value * stage.distance / 36 : 0
                }
            }

            MonthView {
                width: stage.width
                height: stage.height
                start: win.view === "month" ? win.rangeStart : Dates.monthGrid(win.anchor, win.weekStart)
                month: win.anchor
                now: win.now
                weekStart: win.weekStart
                visible: opacity > 0.01
                enabled: win.view === "month"
                opacity: morph.value * (win.view === "month" ? stage.fade : 1)
                onOpenEvent: ev => editor.ev = ev
                onCreate: (start, end, allDay) => win.create(start, end, allDay)
                onOpenDay: day => {
                    win.jump(day);
                    win.setView("week");
                }

                transform: Translate {
                    y: win.view === "month" ? slide.value * stage.distance / 36 : 0
                }
            }
        }
    }

    Toast {
        id: toast

        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height - height - Theme.space5
    }

    EventEditor {
        id: editor

        onEvChanged: if (!ev)
            weekView.ghost = null
    }

    SettingsSheet {
        app: win
        open: win.settingsOpen
    }
}
