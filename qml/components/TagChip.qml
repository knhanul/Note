import QtQuick
import QtQuick.Layouts
import theme

Rectangle {
    id: root

    property string text: "Tag"
    property bool isSelected: false
    property bool isRemovable: false
    property color tagColor: Colors.primary500

    signal clicked()
    signal removed()

    height: 28
    width: contentRow.width + (isRemovable ? 32 : 20)
    radius: Metrics.radiusFull
    color: {
        if (isSelected) return tagColor
        return Qt.rgba(tagColor.r, tagColor.g, tagColor.b, 0.1)
    }
    border.width: 1
    border.color: isSelected ? tagColor : Qt.rgba(tagColor.r, tagColor.g, tagColor.b, 0.2)

    Behavior on color {
        ColorAnimation { duration: Metrics.durationFast }
    }

    Behavior on scale {
        NumberAnimation { duration: Metrics.durationFast }
    }

    Rectangle {
        anchors.fill: parent
        radius: parent.radius
        color: tagColor
        opacity: mouseArea.containsMouse ? 0.05 : 0
        visible: !isSelected

        Behavior on opacity {
            NumberAnimation { duration: Metrics.durationFast }
        }
    }

    RowLayout {
        id: contentRow
        anchors.centerIn: parent
        spacing: Metrics.xs

        Rectangle {
            width: 6
            height: 6
            radius: Metrics.radiusFull
            color: isSelected ? Colors.textInverse : tagColor
            visible: !isRemovable
        }

        Text {
            text: root.text
            font.family: Typography.fontPrimary
            font.weight: Typography.weightMedium
            font.pixelSize: Typography.caption
            color: isSelected ? Colors.textInverse : tagColor
        }

        Rectangle {
            visible: isRemovable
            width: 16
            height: 16
            radius: Metrics.radiusFull
            color: removeArea.containsMouse ? Qt.rgba(0, 0, 0, 0.1) : "transparent"

            Text {
                anchors.centerIn: parent
                text: "x"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightSemibold
                font.pixelSize: 10
                color: isSelected ? Colors.textInverse : tagColor
            }

            MouseArea {
                id: removeArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    mouse.accepted = true
                    root.removed()
                }
            }
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.clicked()
        onPressed: root.scale = 0.97
        onReleased: root.scale = 1.0
    }
}
