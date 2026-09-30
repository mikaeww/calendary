pragma ComponentBehavior: Bound

import QtQuick
import Calendary
import "../theme"
import "../controls"

// Accounts (sign in with one button, sign out with a confirmation) and how the calendar looks.
Sheet {
    id: root

    required property var app
    property string leaving: ""

    cardWidth: 480
    onDismissed: app.settingsOpen = false
    onAccepted: app.settingsOpen = false
    onOpenChanged: leaving = ""

    Text {
        text: "Einstellungen"
        color: Theme.fg
        font.family: Theme.fontUi
        font.pixelSize: Theme.fsHead
        font.bold: true
        font.letterSpacing: -0.3
    }

    SectionLabel {
        topPadding: Theme.space2
        text: "Google-Konten"
    }

    Repeater {
        model: Calendar.accounts

        Item {
            id: account

            required property var modelData
            readonly property bool confirming: root.leaving === modelData.email

            width: root.card.width - 2 * Theme.space4
            height: Theme.ctlH

            Text {
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width - signOut.width - Theme.space3
                text: account.modelData.email
                color: Theme.fg
                font.family: Theme.fontUi
                font.pixelSize: Theme.fsBody
                elide: Text.ElideMiddle
            }

            Button {
                id: signOut

                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                label: account.confirming ? "Wirklich abmelden?" : "Abmelden"
                strong: account.confirming
                onClicked: {
                    if (!account.confirming) {
                        root.leaving = account.modelData.email;
                        return;
                    }
                    Calendar.signOut(account.modelData.email);
                    root.leaving = "";
                }
            }
        }
    }

    Row {
        spacing: Theme.space2

        Button {
            visible: !Calendar.signingIn
            enabled: Calendar.ready
            label: Calendar.accounts.length ? "Weiteres Konto anmelden" : "Mit Google anmelden"
            primary: true
            onClicked: Calendar.signIn()
        }

        Button {
            visible: Calendar.signingIn
            label: "Anmeldung abbrechen"
            onClicked: Calendar.cancelSignIn()
        }

        Text {
            visible: Calendar.signingIn
            anchors.verticalCenter: parent.verticalCenter
            text: "Im Browser anmelden …"
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsBody
        }
    }

    Text {
        visible: !Calendar.ready
        width: parent.width
        wrapMode: Text.Wrap
        text: "Die Google-Anmeldung ist in dieser Installation nicht eingerichtet: google-client.json fehlt im App-Ordner. Die README beschreibt den einmaligen Schritt."
        color: Theme.sub
        font.family: Theme.fontUi
        font.pixelSize: Theme.fsSmall
    }

    SectionLabel {
        topPadding: Theme.space3
        text: "Darstellung"
    }

    Grid {
        columns: 2
        columnSpacing: Theme.space3
        rowSpacing: Theme.space2
        verticalItemAlignment: Grid.AlignVCenter

        Text {
            text: "Erscheinungsbild"
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsBody
        }

        Segmented {
            options: [["system", "System"], ["dark", "Dunkel"], ["light", "Hell"]]
            current: Theme.mode
            onPicked: value => Theme.setMode(value)
        }

        Text {
            text: "Woche beginnt"
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsBody
        }

        Segmented {
            options: [["1", "Montag"], ["0", "Sonntag"]]
            current: String(root.app.weekStart)
            onPicked: value => root.app.setPreference("weekStart", Number(value))
        }

        Text {
            text: "Woche zeigt"
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsBody
        }

        Segmented {
            options: [["7", "7 Tage"], ["5", "Mo – Fr"]]
            current: root.app.workWeek ? "5" : "7"
            onPicked: value => root.app.setPreference("workWeek", value === "5")
        }
    }

    Item {
        width: parent.width
        height: Theme.ctlH

        Button {
            anchors.right: parent.right
            label: "Fertig"
            onClicked: root.app.settingsOpen = false
        }
    }
}
