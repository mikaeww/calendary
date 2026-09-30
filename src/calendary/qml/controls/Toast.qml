pragma ComponentBehavior: Bound

import QtQuick
import "../theme"
import "../motion"

// A short notice at the bottom; problems are told by bold text, not by colour.
Rectangle {
    id: toast

    property string message: ""
    property bool problem: false

    function show(text, bad) {
        message = text;
        problem = bad;
        rise.target = 1;
        timer.restart();
    }

    width: Math.min(caption.implicitWidth + 2 * Theme.space3, parent.width - 2 * Theme.space5)
    height: Theme.ctlH + Theme.space2
    radius: Theme.radiusSmall
    color: Theme.raise3
    opacity: rise.value
    visible: opacity > 0.01
    z: 20
    Accessible.role: Accessible.AlertMessage
    Accessible.name: message

    Spring {
        id: rise

        // A fade stays with reduced motion; only the travel goes.
        instant: false

        precision: 0.002
    }

    Timer {
        id: timer

        interval: 4200
        onTriggered: rise.target = 0
    }

    Text {
        id: caption

        anchors.centerIn: parent
        width: Math.min(implicitWidth, toast.width - 2 * Theme.space3)
        text: toast.message
        color: Theme.fg
        font.family: Theme.fontUi
        font.pixelSize: Theme.fsSmall
        font.bold: toast.problem
        elide: Text.ElideRight
    }
}
