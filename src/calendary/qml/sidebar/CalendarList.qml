pragma ComponentBehavior: Bound

import QtQuick
import Calendary
import "../theme"
import "../controls"

// Every account with its calendars; a click shows or hides one. Without an account, the one way in: sign in.
Column {
    id: root

    required property var app

    spacing: Theme.space4

    Column {
        visible: Calendar.accounts.length === 0
        width: parent.width
        spacing: Theme.space3

        Text {
            width: parent.width
            text: Calendar.signingIn ? "Im Browser anmelden …" : "Noch kein Google-Konto verbunden."
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsBody
            wrapMode: Text.Wrap
        }

        Button {
            visible: !Calendar.signingIn
            label: "Mit Google anmelden"
            primary: true
            onClicked: Calendar.signIn()
        }

        Button {
            visible: Calendar.signingIn
            label: "Abbrechen"
            onClicked: Calendar.cancelSignIn()
        }

        Button {
            label: "iCloud verbinden"
            onClicked: root.app.settingsOpen = true
        }
    }

    Repeater {
        model: Calendar.accounts

        Column {
            id: account

            required property var modelData

            width: root.width
            spacing: 2

            SectionLabel {
                x: Theme.space2
                width: parent.width - 2 * Theme.space2
                bottomPadding: Theme.space1
                text: account.modelData.name
                elide: Text.ElideMiddle
            }

            Repeater {
                model: account.modelData.calendars

                Rectangle {
                    id: row

                    required property var modelData

                    width: account.width
                    height: Theme.ctlH + 2
                    radius: Theme.radiusSmall
                    color: hover.hovered || activeFocus ? Theme.raise1 : "transparent"
                    activeFocusOnTab: true
                    Accessible.role: Accessible.CheckBox
                    Accessible.name: modelData.name
                    Accessible.checked: modelData.visible
                    Keys.onSpacePressed: Calendar.setVisible(modelData.key, !modelData.visible)

                    Behavior on color {
                        ColorAnimation {
                            duration: Theme.motionFast
                        }
                    }

                    Rectangle {
                        x: Theme.space2 + 1
                        anchors.verticalCenter: parent.verticalCenter
                        width: 8
                        height: 8
                        radius: 4
                        color: row.modelData.visible ? row.modelData.color : Theme.raise3
                    }

                    Text {
                        x: Theme.space2 * 2 + 9
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.width - x - (lock.visible ? Theme.fsBody + Theme.space2 * 2 : Theme.space2)
                        text: row.modelData.name
                        color: row.modelData.visible ? Theme.fg : Theme.faint
                        font.family: Theme.fontUi
                        font.pixelSize: Theme.fsBody
                        elide: Text.ElideRight
                    }

                    Text {
                        id: lock

                        visible: !row.modelData.writable
                        anchors.right: parent.right
                        anchors.rightMargin: Theme.space2
                        anchors.verticalCenter: parent.verticalCenter
                        text: Theme.glyph.lock
                        color: Theme.faint
                        font.family: Theme.iconFont
                        font.pixelSize: Theme.fsBody
                        Accessible.name: "nur lesbar"
                    }

                    HoverHandler {
                        id: hover

                        cursorShape: Qt.PointingHandCursor
                    }

                    TapHandler {
                        onTapped: Calendar.setVisible(row.modelData.key, !row.modelData.visible)
                    }
                }
            }
        }
    }
}
