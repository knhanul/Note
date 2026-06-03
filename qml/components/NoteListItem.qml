import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
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
    property bool isBatchHighlighted: false
    property bool selectionMode: false
    property bool isHovered: false
    property bool isPinned: false
    property bool showPinButton: true
    property bool showDeleteButton: true
    property string folderPath: ""

    signal clicked()
    signal selectionClicked()
    signal pinClicked()
    signal deleteClicked()

    height: 56
    Layout.fillWidth: true
    focus: root.isSelected

    GlassCard {
        id: card
        anchors.fill: parent
        anchors.margins: 2
        hovered: root.isHovered
        selected: root.isSelected || root.isBatchHighlighted
        radius: Metrics.radiusXl

        RowLayout {
            anchors.fill: parent
            anchors.margins: Metrics.sm
            spacing: Metrics.sm

            Rectangle {
                visible: root.selectionMode
                width: 20
                height: 20
                radius: Metrics.radiusSm
                color: root.isBatchHighlighted ? Colors.primary500 : Colors.bgPrimary
                border.color: root.isBatchHighlighted ? Colors.primary500 : Colors.borderLight
                border.width: 1
                Layout.alignment: Qt.AlignVCenter

                Text {
                    anchors.centerIn: parent
                    text: root.isBatchHighlighted ? "✓" : ""
                    font.family: Typography.fontPrimary
                    font.pixelSize: 11
                    font.weight: Typography.weightBold
                    color: "white"
                }

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: root.selectionClicked()
                }
            }

            Item {
                visible: root.showPinButton && !root.selectionMode
                width: 20
                height: 20
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                // Title
                Text {
                    Layout.fillWidth: true
                    text: root.title
                    font.family: Typography.fontPrimary
                    font.weight: (root.isSelected || root.isBatchHighlighted) ? Typography.weightSemibold : Typography.weightMedium
                    font.pixelSize: 13
                    color: (root.isSelected || root.isBatchHighlighted) ? Colors.textInverse : Colors.textPrimary
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
                    color: (root.isSelected || root.isBatchHighlighted) ? Qt.rgba(1, 1, 1, 0.7) : Colors.textTertiary
                }
            }

            // Spacer for star + delete buttons
            Item {
                width: (root.isHovered && !root.selectionMode) ? 44 : 20
                height: 20
                Behavior on width { NumberAnimation { duration: Metrics.durationFast } }
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
        ToolTip.visible: root.folderPath !== "" && (containsMouse || root.isSelected)
        ToolTip.delay: 0
        ToolTip.timeout: 2500
        ToolTip.text: root.folderPath
    }

    // Delete button - visible on hover, left of star
    Rectangle {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.rightMargin: Metrics.md + 24
        anchors.topMargin: Metrics.md
        width: 20
        height: 20
        radius: Metrics.radiusFull
        visible: root.showDeleteButton && root.isHovered && !root.selectionMode
        opacity: root.isHovered ? 1 : 0
        color: deleteBtnMA.containsMouse
            ? ((root.isSelected || root.isBatchHighlighted) ? Qt.rgba(1, 0.3, 0.3, 0.4) : "#FEE2E2")
            : ((root.isSelected || root.isBatchHighlighted) ? Qt.rgba(1, 1, 1, 0.15) : Colors.bgTertiary)
        z: 11

        Behavior on opacity { NumberAnimation { duration: Metrics.durationFast } }

        Text {
            anchors.centerIn: parent
            text: "✕"
            font.pixelSize: 10
            color: deleteBtnMA.containsMouse
                ? "#DC2626"
                : ((root.isSelected || root.isBatchHighlighted) ? Colors.textInverse : Colors.textTertiary)
        }

        MouseArea {
            id: deleteBtnMA
            anchors.fill: parent
            hoverEnabled: true
            onClicked: {
                mouse.accepted = true
                root.deleteClicked()
            }
        }
    }

    // Star button at root level - above the main MouseArea
    Rectangle {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: Metrics.md
        width: 20
        height: 20
        radius: Metrics.radiusFull
        visible: !root.selectionMode
        color: (root.isSelected || root.isBatchHighlighted) ? Qt.rgba(1, 1, 1, 0.2) : (root.isPinned ? Colors.accentOrangeLight : Colors.bgTertiary)
        z: 10

        Text {
            anchors.centerIn: parent
            text: root.isPinned ? "★" : "☆"
            font.pixelSize: 12
            color: root.isPinned ? Colors.accentOrange : ((root.isSelected || root.isBatchHighlighted) ? Colors.textInverse : Colors.textTertiary)
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
