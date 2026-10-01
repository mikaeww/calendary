pragma ComponentBehavior: Bound

import QtQuick
import Calendary
import "../theme"
import "../controls"
import "../calendar"

// The narrow column on the left: name, the small month, the calendars, and settings with the sync state.
Item {
    id: root

    required property var app

    Row {
        id: brand

        x: Theme.space2
        height: Theme.ctlH + Theme.space2
        spacing: Theme.space2

        Image {
            anchors.verticalCenter: parent.verticalCenter
            width: Theme.fsHead + 3
            height: width
            source: "../../../../assets/icons/calendary.svg"
            sourceSize: Qt.size(width * 2, height * 2)
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "Calendary"
            color: Theme.fg
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsHead
            font.bold: true
            font.letterSpacing: -0.3
        }
    }

    MiniMonth {
        id: mini

        y: brand.height + Theme.space3
        width: parent.width
        anchor: root.app.anchor
        rangeStart: root.app.rangeStart
        rangeEnd: root.app.rangeEnd
        now: root.app.now
        weekStart: root.app.weekStart
        onPicked: day => root.app.jump(day)
    }

    Flickable {
        id: scroll

        anchors.top: mini.bottom
        anchors.topMargin: Theme.space5
        anchors.bottom: footer.top
        anchors.bottomMargin: Theme.space2
        width: parent.width
        contentHeight: list.height
        boundsBehavior: Flickable.StopAtBounds
        clip: true

        CalendarList {
            id: list

            width: scroll.width
            app: root.app
        }
    }

    Row {
        id: footer

        anchors.bottom: parent.bottom
        width: parent.width
        spacing: Theme.space1

        IconButton {
            glyph: Theme.glyph.settings
            label: qsTr("Einstellungen")
            onClicked: root.app.settingsOpen = true
        }

        IconButton {
            id: syncButton

            glyph: Theme.glyph.sync
            label: qsTr("Jetzt synchronisieren")
            enabled: Calendar.accounts.length > 0
            onClicked: Calendar.refresh()
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - 2 * Theme.ctlH - 2 * Theme.space1
            leftPadding: Theme.space1
            text: Calendar.signingIn ? qsTr("Warte auf den Browser …") : Calendar.busy ? qsTr("Synchronisiere …") : ""
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsSmall
            elide: Text.ElideRight
        }
    }
}
