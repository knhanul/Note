import QtQuick
import QtQuick.Layouts
import theme

Item {
    id: root

    property string title: "Untitled Note"
    property string preview: ""
    property string date: ""
    property var tags: []
    property bool isSelected: false
    property bool isHovered: false
    property bool isPinned: false

    signal clicked()
    signal pinClicked()

    height: 88
    Layout.fillWidth: true

    GlassCard {
        id: card
        anchors.fill: parent
        anchors.margins: Metrics.xs
        hovered: root.isHovered
        selected: root.isSelected
        radius: Metrics.radiusXl

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Metrics.lg
            spacing: Metrics.xs

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.sm

                Text {
                    Layout.fillWidth: true
                    text: root.title
                    font.family: Typography.fontPrimary
                    font.weight: root.isSelected ? Typography.weightSemibold : Typography.weightMedium
                    font.pixelSize: Typography.bodyRegular
                    color: root.isSelected ? Colors.textInverse : Colors.textPrimary
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }

                // Spacer for star button (star button is at root level)
                Item {
                    width: 24
                    height: 24
                }
            }

            Text {
                Layout.fillWidth: true
                text: root.preview || ""
                font.family: Typography.fontPrimary
                font.weight: Typography.weightRegular
                font.pixelSize: Typography.bodySmall
                color: root.isSelected ? Qt.rgba(1, 1, 1, 0.85) : Colors.textSecondary
                elide: Text.ElideRight
                maximumLineCount: 2
                lineHeight: Typography.lineHeightNormal
                visible: root.preview !== ""
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.sm

                Text {
                    text: root.date
                    font.family: Typography.fontPrimary
                    font.weight: Typography.weightRegular
                    font.pixelSize: Typography.caption
                    color: root.isSelected ? Qt.rgba(1, 1, 1, 0.7) : Colors.textTertiary
                }

                Item { Layout.fillWidth: true }

                Row {
                    spacing: Metrics.xs
                    visible: root.tags.length > 0

                    Repeater {
                        model: Math.min(root.tags.length, 2)

                        delegate: Rectangle {
                            height: 16
                            width: tagText.width + 8
                            radius: Metrics.radiusSm
                            color: root.isSelected ? Qt.rgba(1, 1, 1, 0.25) : Colors.primary100

                            Text {
                                id: tagText
                                anchors.centerIn: parent
                                text: root.tags[index]
                                font.family: Typography.fontPrimary
                                font.weight: Typography.weightMedium
                                font.pixelSize: 9
                                color: root.isSelected ? Colors.textInverse : Colors.primary600
                            }
                        }
                    }

                    Rectangle {
                        visible: root.tags.length > 2
                        height: 16
                        width: moreText.width + 8
                        radius: Metrics.radiusSm
                        color: root.isSelected ? Qt.rgba(1, 1, 1, 0.25) : Colors.bgTertiary

                        Text {
                            id: moreText
                            anchors.centerIn: parent
                            text: "+" + (root.tags.length - 2)
                            font.family: Typography.fontPrimary
                            font.weight: Typography.weightMedium
                            font.pixelSize: 9
                            color: root.isSelected ? Colors.textInverse : Colors.textTertiary
                        }
                    }
                }
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
        anchors.margins: Metrics.lg + Metrics.sm
        width: 24
        height: 24
        radius: Metrics.radiusFull
        color: root.isSelected ? Qt.rgba(1, 1, 1, 0.2) : (root.isPinned ? Colors.accentOrangeLight : Colors.bgTertiary)
        z: 10

        Text {
            anchors.centerIn: parent
            text: root.isPinned ? "★" : "☆"
            font.pixelSize: 14
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
