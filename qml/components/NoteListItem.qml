import QtQuick
import QtQuick.Layouts
import theme

Item {
    id: root

    property string title: "Untitled Note"
    property string preview: ""
    property string date: ""           // deprecated: use updatedDate
    property string createdDate: ""
    property string updatedDate: ""
    property var tags: []
    property bool isSelected: false
    property bool isHovered: false
    property bool isPinned: false

    signal clicked()
    signal pinClicked()

    height: 56
    Layout.fillWidth: true

    GlassCard {
        id: card
        anchors.fill: parent
        anchors.margins: 2
        hovered: root.isHovered
        selected: root.isSelected
        radius: Metrics.radiusXl

        RowLayout {
            anchors.fill: parent
            anchors.margins: Metrics.sm
            spacing: Metrics.sm

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                // Title
                Text {
                    Layout.fillWidth: true
                    text: root.title
                    font.family: Typography.fontPrimary
                    font.weight: root.isSelected ? Typography.weightSemibold : Typography.weightMedium
                    font.pixelSize: 13
                    color: root.isSelected ? Colors.textInverse : Colors.textPrimary
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }

                // Dates row
                Text {
                    text: {
                        var c = root.createdDate || ""
                        var u = root.updatedDate || root.date || ""
                        var result = ""
                        if (c) result += "생성: " + c
                        if (c && u) result += "  |  "
                        if (u) result += "수정: " + u
                        return result
                    }
                    font.family: Typography.fontPrimary
                    font.weight: Typography.weightRegular
                    font.pixelSize: 11
                    color: root.isSelected ? Qt.rgba(1, 1, 1, 0.7) : Colors.textTertiary
                }
            }

            // Spacer for star button
            Item {
                width: 20
                height: 20
            }
        }
    }

    // Main click area - covers the card but lets star button handle its own clicks
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: root.isHovered = true
        onExited: root.isHovered = false
        onClicked: root.clicked()
    }

    // Star button at root level - above the main MouseArea
    Rectangle {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: Metrics.md
        width: 20
        height: 20
        radius: Metrics.radiusFull
        color: root.isSelected ? Qt.rgba(1, 1, 1, 0.2) : (root.isPinned ? Colors.accentOrangeLight : Colors.bgTertiary)
        z: 10

        Text {
            anchors.centerIn: parent
            text: root.isPinned ? "★" : "☆"
            font.pixelSize: 12
            color: root.isPinned ? Colors.accentOrange : (root.isSelected ? Colors.textInverse : Colors.textTertiary)
        }

        MouseArea {
            anchors.fill: parent
            onClicked: root.pinClicked()
        }
    }

    Component.onCompleted: {
        opacityAnimation.start()
    }

    NumberAnimation on opacity {
        id: opacityAnimation
        from: 0
        to: 1
        duration: Metrics.durationNormal
    }

    Behavior on y {
        NumberAnimation {
            duration: Metrics.durationFast
        }
    }
}
