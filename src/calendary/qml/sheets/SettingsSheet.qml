pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Dialogs
import Calendary
import "../theme"
import "../controls"

// Accounts (Google with one button, iCloud with Apple ID and app password, sign out with a confirmation) and looks.
Sheet {
    id: root

    required property var app
    property string leaving: ""
    property bool addingICloud: false
    // True while a connect started here is running; its end decides whether the form closes.
    property bool submitted: false

    function closeICloud() {
        addingICloud = false;
        submitted = false;
        appleId.text = "";
        appPassword.text = "";
    }

    cardWidth: 480
    onDismissed: app.settingsOpen = false
    onAccepted: app.settingsOpen = false
    onOpenChanged: leaving = ""

    Connections {
        function onSigningChanged() {
            if (root.submitted && !Calendar.connecting) {
                root.submitted = false;
                if (Calendar.accounts.some(account => account.key === "icloud:" + appleId.text.trim().toLowerCase()))
                    root.closeICloud();
            }
        }

        target: Calendar
    }

    Text {
        text: qsTr("Einstellungen")
        color: Theme.fg
        font.family: Theme.fontUi
        font.pixelSize: Theme.fsHead
        font.bold: true
        font.letterSpacing: -0.3
    }

    SectionLabel {
        topPadding: Theme.space2
        text: qsTr("Konten")
    }

    Repeater {
        model: Calendar.accounts

        Item {
            id: account

            required property var modelData
            readonly property bool confirming: root.leaving === modelData.key

            width: root.card.width - 2 * Theme.space4
            height: Theme.ctlH

            Row {
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width - signOut.width - Theme.space3
                spacing: Theme.space2

                Text {
                    width: Math.min(implicitWidth, parent.width - provider.implicitWidth - Theme.space2)
                    text: account.modelData.name
                    color: Theme.fg
                    font.family: Theme.fontUi
                    font.pixelSize: Theme.fsBody
                    elide: Text.ElideMiddle
                }

                Text {
                    id: provider

                    text: account.modelData.provider === "icloud" ? "iCloud" : "Google"
                    color: Theme.faint
                    font.family: Theme.fontUi
                    font.pixelSize: Theme.fsBody
                }
            }

            Button {
                id: signOut

                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                label: account.confirming ? qsTr("Wirklich abmelden?") : qsTr("Abmelden")
                strong: account.confirming
                onClicked: {
                    if (!account.confirming) {
                        root.leaving = account.modelData.key;
                        return;
                    }
                    Calendar.signOut(account.modelData.key);
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
            label: qsTr("Mit Google anmelden")
            primary: true
            onClicked: Calendar.signIn()
        }

        Button {
            visible: Calendar.signingIn
            label: qsTr("Anmeldung abbrechen")
            onClicked: Calendar.cancelSignIn()
        }

        Button {
            visible: !root.addingICloud
            label: qsTr("iCloud verbinden")
            onClicked: {
                root.addingICloud = true;
                appleId.input.forceActiveFocus();
            }
        }

        Text {
            visible: Calendar.signingIn
            anchors.verticalCenter: parent.verticalCenter
            text: qsTr("Im Browser anmelden …")
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsBody
        }
    }

    Column {
        visible: !Calendar.ready
        width: parent.width
        spacing: Theme.space2

        Text {
            width: parent.width
            wrapMode: Text.Wrap
            text: qsTr("Für Google braucht jede Installation einen eigenen OAuth-Client: in der Google Cloud Console ein Projekt anlegen, die Calendar API aktivieren, einen Client vom Typ Desktop-App erstellen und dessen JSON-Datei hier wählen.")
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsSmall
        }

        Row {
            spacing: Theme.space2

            Button {
                label: qsTr("Client-Datei wählen …")
                onClicked: clientPicker.open()
            }

            Button {
                label: qsTr("Anleitung")
                onClicked: Qt.openUrlExternally("https://github.com/mikaeww/calendary#google-setup")
            }
        }
    }

    FileDialog {
        id: clientPicker

        title: qsTr("Google-Client-Datei wählen")
        nameFilters: [qsTr("Google-Client (*.json)")]
        onAccepted: Calendar.importClient(selectedFile.toString())
    }

    Column {
        visible: root.addingICloud
        width: parent.width
        spacing: Theme.space2

        Text {
            width: parent.width
            wrapMode: Text.Wrap
            text: qsTr("iCloud braucht deine Apple-ID und ein app-spezifisches Passwort, nicht dein normales Passwort. Du erstellst es auf account.apple.com unter „Anmeldung und Sicherheit“.")
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsSmall
        }

        Field {
            id: appleId

            width: parent.width
            placeholder: qsTr("Apple-ID (E-Mail)")
        }

        Field {
            id: appPassword

            width: parent.width
            placeholder: qsTr("App-spezifisches Passwort (xxxx-xxxx-xxxx-xxxx)")
            input.echoMode: TextInput.Password
        }

        Row {
            spacing: Theme.space2

            Button {
                enabled: !Calendar.connecting
                label: Calendar.connecting ? qsTr("Prüfe bei iCloud …") : qsTr("Verbinden")
                strong: true
                onClicked: root.submitted = Calendar.connectICloud(appleId.text, appPassword.text)
            }

            Button {
                label: qsTr("Passwort erstellen")
                onClicked: Qt.openUrlExternally("https://account.apple.com/account/manage")
            }

            Button {
                label: qsTr("Abbrechen")
                onClicked: root.closeICloud()
            }
        }
    }

    SectionLabel {
        topPadding: Theme.space3
        text: qsTr("Darstellung")
    }

    Grid {
        columns: 2
        columnSpacing: Theme.space3
        rowSpacing: Theme.space2
        verticalItemAlignment: Grid.AlignVCenter

        Text {
            text: qsTr("Erscheinungsbild")
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsBody
        }

        Segmented {
            options: [["system", qsTr("System")], ["dark", qsTr("Dunkel")], ["light", qsTr("Hell")]]
            current: Theme.mode
            onPicked: value => Theme.setMode(value)
        }

        Text {
            text: qsTr("Woche beginnt")
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsBody
        }

        Segmented {
            options: [["1", qsTr("Montag")], ["0", qsTr("Sonntag")]]
            current: String(root.app.weekStart)
            onPicked: value => root.app.setPreference("weekStart", Number(value))
        }

        Text {
            text: qsTr("Woche zeigt")
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsBody
        }

        Segmented {
            options: [["7", qsTr("7 Tage")], ["5", qsTr("Mo – Fr")]]
            current: root.app.workWeek ? "5" : "7"
            onPicked: value => root.app.setPreference("workWeek", value === "5")
        }

        Text {
            text: qsTr("Sprache")
            color: Theme.sub
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsBody
        }

        // Each language carries its own name, so it stays findable whichever one is shown.
        Segmented {
            options: [["system", qsTr("System")], ["de", "Deutsch"], ["en", "English"]]
            current: Qt.uiLanguage
            onPicked: value => {
                Preferences.set("language", value);
                Qt.uiLanguage = value;
            }
        }
    }

    Item {
        width: parent.width
        height: Theme.ctlH

        Button {
            anchors.right: parent.right
            label: qsTr("Fertig")
            onClicked: root.app.settingsOpen = false
        }
    }
}
