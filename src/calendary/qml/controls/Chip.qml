pragma ComponentBehavior: Bound

import QtQuick
import "../theme"

// A toggle or choice. With `dot` it shows a calendar's colour, the only hue the interface uses.
Rectangle {
    id: chip

    property string label: ""
    property bool active: false
    property color dot: "transparent"
    signal clicked

    implicitWidth: row.implicitWidth + 2 * Theme.space2 + 2
    implicitHeight: Theme.ctlH
    radius: Theme.radiusSmall
    opacity: enabled ? 1 : 0.45
    color: active ? Theme.chipOn : activeFocus || hover.hovered ? Theme.raise3 : Theme.raise2
    activeFocusOnTab: true
    Accessible.role: Accessible.CheckBox
    Accessible.name: label
    Accessible.checked: active
    Accessible.onPressAction: clicked()
    Keys.onSpacePressed: clicked()

    Behavior on color {
        ColorAnimation {
            duration: Theme.motionFast
        }
    }

    Row {
        id: row

        anchors.centerIn: parent
        spacing: Theme.space1 + 2

        Rectangle {
            visible: chip.dot.a > 0
            anchors.verticalCenter: parent.verticalCenter
            width: 8
            height: 8
            radius: 4
            color: chip.dot
        }

        Text {
            text: chip.label
            color: chip.active ? Theme.chipOnFg : Theme.fg
            font.family: Theme.fontUi
            font.pixelSize: Theme.fsBody
            font.bold: chip.active
        }
    }

    HoverHandler {
        id: hover

        cursorShape: Qt.PointingHandCursor
    }

    TapHandler {
        onTapped: chip.clicked()
    }
}
