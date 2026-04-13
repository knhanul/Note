import QtQuick
import theme

Rectangle {
    id: root
    property bool hovered: false
    property bool pressed: false
    property bool selected: false
    property int elevation: hovered ? 2 : (pressed ? 1 : 0)
    property real baseOpacity: 0.85
    property real hoverLift: 2

    color: selected ? "transparent" : Qt.rgba(1, 1, 1, baseOpacity)
    radius: Metrics.radiusXxl
    border.width: selected ? 0 : 1
    border.color: Colors.borderLight

    property var selectedGradient: Gradient {
        GradientStop { position: 0.0; color: Colors.primary400 }
        GradientStop { position: 1.0; color: Colors.primary500 }
    }

    Behavior on scale {
        NumberAnimation { duration: Metrics.durationFast }
    }

    Behavior on y {
        NumberAnimation { duration: Metrics.durationFast }
    }

    Behavior on color {
        ColorAnimation { duration: Metrics.durationNormal }
    }

    Behavior on border.color {
        ColorAnimation { duration: Metrics.durationFast }
    }

    Rectangle {
        id: shadowLayer1
        anchors.fill: parent
        radius: parent.radius
        color: "transparent"
        visible: elevation > 0
        z: -1
        Rectangle {
            anchors.fill: parent
            radius: parent.radius
            color: Colors.textPrimary
            opacity: elevation >= 2 ? 0.06 : 0.04
            anchors.verticalCenterOffset: elevation >= 2 ? 6 : 3
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    Rectangle {
        id: shadowLayer2
        anchors.fill: parent
        radius: parent.radius
        color: "transparent"
        visible: elevation >= 2
        z: -2
        Rectangle {
            anchors.fill: parent
            radius: parent.radius
            color: Colors.primary500
            opacity: 0.03
            anchors.verticalCenterOffset: 12
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    Rectangle {
        id: gradientOverlay
        anchors.fill: parent
        radius: parent.radius
        gradient: root.selectedGradient
        visible: root.selected
        z: -1
        Behavior on opacity {
            NumberAnimation { duration: Metrics.durationNormal }
        }
    }

    Rectangle {
        id: innerGlow
        anchors.fill: parent
        radius: parent.radius
        color: "transparent"
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.5)
        opacity: 0.5
        visible: !root.selected
    }

    Rectangle {
        id: hoverGlow
        anchors.fill: parent
        radius: parent.radius
        color: Colors.primary100
        opacity: root.hovered && !root.selected ? 0.15 : 0
        visible: opacity > 0
        Behavior on opacity {
            NumberAnimation { duration: Metrics.durationFast }
        }
    }

    states: [
        State {
            name: "pressed"
            when: root.pressed
            PropertyChanges { target: root; scale: 0.98 }
        },
        State {
            name: "hovered"
            when: root.hovered && !root.pressed
            PropertyChanges { target: root; y: -root.hoverLift }
        }
    ]

    transitions: [
        Transition {
            from: "*"; to: "pressed"
            NumberAnimation { properties: "scale"; duration: Metrics.durationFast }
        },
        Transition {
            from: "pressed"; to: "*"
            NumberAnimation { properties: "scale"; duration: Metrics.durationNormal }
        },
        Transition {
            from: "*"; to: "hovered"
            NumberAnimation { properties: "y"; duration: Metrics.durationFast }
        },
        Transition {
            from: "hovered"; to: "*"
            NumberAnimation { properties: "y"; duration: Metrics.durationNormal }
        }
    ]
}
