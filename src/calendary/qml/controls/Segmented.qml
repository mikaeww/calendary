pragma ComponentBehavior: Bound

import QtQuick
import "../theme"
import "../motion"

// One page choice: the active option is a compact inverted block that glides on a spring to its new place.
Rectangle {
    id: root

    property var options: []
    property string current: ""
    signal picked(string value)

    readonly property int index: Math.max(0, options.findIndex(option => option[0] === current))

    implicitWidth: row.implicitWidth + 4
    implicitHeight: Theme.ctlH
    radius: Theme.radiusSmall
    color: Theme.raise2
    Accessible.role: Accessible.PageTabList

    Spring {
        id: glide

        target: repeater.count > root.index && repeater.itemAt(root.index) ? repeater.itemAt(root.index).x : 0
    }

    Spring {
        id: stretch

        target: repeater.count > root.index && repeater.itemAt(root.index) ? repeater.itemAt(root.index).width : 0
    }

    Rectangle {
        x: 2 + glide.value
        y: 2
        width: stretch.value
        height: root.height - 4
        radius: Theme.radiusSmall - 2
        color: Theme.chipOn
    }

    Row {
        id: row

        x: 2
        y: 2

        Repeater {
            id: repeater

            model: root.options

            Item {
                id: option

                required property var modelData
                readonly property bool active: root.current === modelData[0]

                width: label.implicitWidth + 2 * Theme.space2 + 4
                height: root.height - 4
                activeFocusOnTab: true
                Accessible.role: Accessible.PageTab
                Accessible.name: modelData[1]
                Accessible.selected: active
                Keys.onSpacePressed: root.picked(modelData[0])

                Rectangle {
                    anchors.fill: parent
                    visible: option.activeFocus && !option.active
                    radius: Theme.radiusSmall - 2
                    color: Theme.raise3
                }

                Text {
                    id: label

                    anchors.centerIn: parent
                    text: option.modelData[1]
                    color: option.active ? Theme.chipOnFg : Theme.sub
                    font.family: Theme.fontUi
                    font.pixelSize: Theme.fsBody
                    font.bold: option.active

                    Behavior on color {
                        ColorAnimation {
                            duration: Theme.motionFast
                        }
                    }
                }

                HoverHandler {
                    cursorShape: Qt.PointingHandCursor
                }

                TapHandler {
                    onTapped: root.picked(option.modelData[0])
                }
            }
        }
    }
}
