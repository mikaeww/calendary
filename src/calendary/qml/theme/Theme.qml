pragma Singleton
import QtQuick
import Calendary

// Every colour, radius, size and duration of the interface. Components use these tokens and nothing else.
QtObject {
    id: theme

    // "system", "dark" or "light"; saved in the preferences.
    property string mode: Preferences.get("theme", "system")
    // The linter types Qt.styleHints as QObject; QStyleHints.colorScheme exists at runtime since Qt 6.5.
    readonly property bool dark: mode === "dark" || (mode === "system" && Qt.styleHints.colorScheme !== Qt.ColorScheme.Light) // qmllint disable missing-property

    // Neutral grey only, R = G = B. raise1..3 are equal brightness steps away from bg.
    readonly property color bg: dark ? "#111111" : "#f6f6f6"
    readonly property color raise1: dark ? "#1b1b1b" : "#ececec"
    readonly property color raise2: dark ? "#262626" : "#e1e1e1"
    readonly property color raise3: dark ? "#313131" : "#d5d5d5"
    readonly property color fg: dark ? "#ececec" : "#161616"
    readonly property color sub: dark ? "#a3a3a3" : "#575757"
    readonly property color faint: dark ? "#6f6f6f" : "#8b8b8b"
    readonly property color chipOn: fg
    readonly property color chipOnFg: bg
    readonly property color scrim: Qt.rgba(bg.r, bg.g, bg.b, 0.72)

    readonly property int radius: 12
    readonly property int radiusSmall: 8

    readonly property int fsMicro: 10
    readonly property int fsSmall: 11
    readonly property int fsBody: 12
    readonly property int fsTitle: 14
    readonly property int fsHead: 17
    readonly property int fsDisplay: 24

    readonly property int space1: 4
    readonly property int space2: 8
    readonly property int space3: 12
    readonly property int space4: 16
    readonly property int space5: 24
    readonly property int pad: space3
    readonly property int ctlH: 26

    readonly property string fontUi: Preferences.fontUi
    readonly property string iconFont: "Monofur Nerd Font"
    // Material Design Icons code points from the Nerd Font.
    readonly property var glyph: ({
            left: "\u{F0141}",
            right: "\u{F0142}",
            plus: "\u{F0415}",
            settings: "\u{F08BB}",
            sync: "\u{F04E6}",
            place: "\u{F07D9}",
            lock: "\u{F033E}"
        })

    readonly property bool reducedMotion: Preferences.reducedMotion
    readonly property int motionFast: reducedMotion ? 0 : 120
    // Period of the critically damped spring in seconds; a page-sized move settles after about 1.3 of it (0.44 s).
    readonly property real springResponse: 0.34

    function mix(a, b, t) {
        return Qt.rgba(a.r + (b.r - a.r) * t, a.g + (b.g - a.g) * t, a.b + (b.b - a.b) * t, 1);
    }

    function setMode(next) {
        mode = next;
        Preferences.set("theme", next);
    }
}
