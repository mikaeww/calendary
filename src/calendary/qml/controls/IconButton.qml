pragma ComponentBehavior: Bound

import QtQuick
import "../theme"

// A square button with one glyph, centred; quiet until hovered.
Rectangle {
    id: button

    property string glyph: ""
    property string label: ""
    signal clicked

    implicitWidth: Theme.ctlH
    implicitHeight: Theme.ctlH
    radius: Theme.radiusSmall
    opacity: enabled ? 1 : 0.45
    color: activeFocus || hover.hovered ? Theme.raise2 : "transparent"
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: label
    Accessible.onPressAction: clicked()
    Keys.onSpacePressed: clicked()
    Keys.onReturnPressed: clicked()

    Behavior on color {
        ColorAnimation {
            duration: Theme.motionFast
        }
    }

    Text {
        anchors.centerIn: parent
        text: button.glyph
        color: Theme.fg
        font.family: Theme.iconFont
        font.pixelSize: Theme.fsTitle
    }

    HoverHandler {
        id: hover

        cursorShape: Qt.PointingHandCursor
    }

    TapHandler {
        onTapped: button.clicked()
    }
}
