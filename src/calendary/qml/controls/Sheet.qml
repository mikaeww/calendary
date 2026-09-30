pragma ComponentBehavior: Bound

import QtQuick
import "../theme"
import "../motion"

// A dialog over a scrim. It rises a few pixels and fades in on a spring; with reduced motion it only fades.
Item {
    id: root

    property bool open: false
    property int cardWidth: 460
    default property alias content: column.data
    readonly property alias card: card
    signal dismissed
    signal accepted

    anchors.fill: parent
    visible: reveal.value > 0.001
    z: 10

    onOpenChanged: {
        reveal.target = open ? 1 : 0;
        if (open)
            card.forceActiveFocus();
    }

    Spring {
        id: reveal

        // A fade stays with reduced motion; only the travel goes.
        instant: false

        precision: 0.002
    }

    Rectangle {
        anchors.fill: parent
        color: Theme.scrim
        opacity: reveal.value
    }

    MouseArea {
        anchors.fill: parent
        onClicked: root.dismissed()
    }

    Rectangle {
        id: card

        width: Math.min(root.cardWidth, root.width - 2 * Theme.space5)
        height: Math.min(column.implicitHeight + 2 * Theme.space4, root.height - 2 * Theme.space5)
        x: Math.round((root.width - width) / 2)
        y: Math.round((root.height - height) / 2) + (Theme.reducedMotion ? 0 : (1 - reveal.value) * Theme.space3)
        radius: Theme.radius
        color: Theme.raise1
        opacity: reveal.value
        clip: true
        Keys.onEscapePressed: root.dismissed()
        Keys.onReturnPressed: root.accepted()
        Keys.onEnterPressed: root.accepted()

        // Takes presses inside the card exclusively, so they never reach the scrim and dismiss it.
        MouseArea {
            anchors.fill: parent
        }

        Column {
            id: column

            x: Theme.space4
            y: Theme.space4
            width: parent.width - 2 * Theme.space4
            spacing: Theme.space3
        }
    }
}
