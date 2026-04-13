import QtQuick
import QtQuick.Layouts
import theme

ColumnLayout {
    id: root

    property string title: "Section"
    property var items: []
    property int selectedIndex: -1

    spacing: Metrics.sm
    Layout.fillWidth: true

    RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: Metrics.lg
        Layout.rightMargin: Metrics.lg

        Text {
            text: root.title.toUpperCase()
            font.family: Typography.fontPrimary
            font.weight: Typography.weightSemibold
            font.pixelSize: Typography.caption
            color: Colors.textTertiary
            font.letterSpacing: Typography.letterSpacingWide
        }

        Item { Layout.fillWidth: true }

        Rectangle {
            width: 20
            height: 20
            radius: Metrics.radiusFull
            color: addArea.containsMouse ? Colors.primary100 : "transparent"
            border.width: 1
            border.color: addArea.containsMouse ? Colors.primary200 : "transparent"

            Behavior on color {
                ColorAnimation { duration: Metrics.durationFast }
            }

            MouseArea {
                id: addArea
                anchors.fill: parent
                hoverEnabled: true
                onPressed: parent.scale = 0.95
                onReleased: parent.scale = 1.0
            }

            Text {
                anchors.centerIn: parent
                text: "+"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightSemibold
                font.pixelSize: 14
                color: addArea.containsMouse ? Colors.primary600 : Colors.textTertiary
            }
        }

        Rectangle {
            width: 20
            height: 20
            radius: Metrics.radiusFull
            color: collapseArea.containsMouse ? Colors.primary100 : "transparent"

            MouseArea {
                id: collapseArea
                anchors.fill: parent
                hoverEnabled: true
            }

            Text {
                anchors.centerIn: parent
                text: "-"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightSemibold
                font.pixelSize: 14
                color: collapseArea.containsMouse ? Colors.primary600 : Colors.textTertiary
            }
        }
    }

    ColumnLayout {
        id: itemsContainer
        Layout.fillWidth: true
        spacing: Metrics.xs

        Repeater {
            model: root.items

            delegate: Item {
                Layout.fillWidth: true
                height: 36

                property bool isSelected: index === root.selectedIndex
                property bool isHovered: false

                Rectangle {
                    anchors.fill: parent
                    anchors.leftMargin: Metrics.md
                    anchors.rightMargin: Metrics.md
                    radius: Metrics.radiusLg
                    color: {
                        if (isSelected) return Colors.primary50
                        if (isHovered) return Colors.bgSecondary
                        return "transparent"
                    }
                    border.width: isSelected ? 1 : 0
                    border.color: Colors.primary200

                    Behavior on color {
                        ColorAnimation { duration: Metrics.durationFast }
                    }

                    Rectangle {
                        visible: isSelected
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: 3
                        radius: Metrics.radiusFull
                        color: Colors.primary500
                        anchors.leftMargin: 8
                        anchors.topMargin: 8
                        anchors.bottomMargin: 8
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: Metrics.xl
                    anchors.rightMargin: Metrics.xl
                    spacing: Metrics.sm

                    Rectangle {
                        visible: modelData.color !== undefined
                        width: 10
                        height: 10
                        radius: 2
                        color: modelData.color || Colors.primary400
                    }

                    Rectangle {
                        visible: modelData.isSmart !== undefined && modelData.isSmart
                        width: 10
                        height: 10
                        radius: 1
                        color: Colors.textTertiary
                        opacity: 0.5
                    }

                    Text {
                        Layout.fillWidth: true
                        text: modelData.name || modelData
                        font.family: Typography.fontPrimary
                        font.weight: isSelected ? Typography.weightMedium : Typography.weightRegular
                        font.pixelSize: Typography.bodySmall
                        color: isSelected ? Colors.primary700 : Colors.textSecondary
                        elide: Text.ElideRight
                    }

                    Rectangle {
                        visible: modelData.count !== undefined && modelData.count > 0
                        height: 16
                        width: countText.width + 12
                        radius: Metrics.radiusFull
                        color: isSelected ? Colors.primary500 : Colors.bgTertiary

                        Text {
                            id: countText
                            anchors.centerIn: parent
                            text: modelData.count || "0"
                            font.family: Typography.fontPrimary
                            font.weight: Typography.weightMedium
                            font.pixelSize: 10
                            color: isSelected ? Colors.textInverse : Colors.textTertiary
                        }
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: isHovered = true
                    onExited: isHovered = false
                    onClicked: root.selectedIndex = index
                    onPressed: parent.scale = 0.99
                    onReleased: parent.scale = 1.0
                }

                Behavior on scale {
                    NumberAnimation { duration: Metrics.durationFast }
                }
            }
        }
    }
}
