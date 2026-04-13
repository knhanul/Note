import QtQuick
import QtQuick.Layouts
import theme

Rectangle {
    id: root

    property string name: "Notebook"
    property color notebookColor: Colors.primary400
    property bool isSelected: false
    property int noteCount: 0

    signal clicked()

    height: 40
    radius: Metrics.radiusXl
    color: {
        if (isSelected) return Colors.primary50
        if (mouseArea.containsMouse) return Colors.bgSecondary
        return "transparent"
    }
    border.width: isSelected ? 1 : 0
    border.color: Colors.primary200

    Behavior on color {
        ColorAnimation { duration: Metrics.durationFast }
    }

    Behavior on scale {
        NumberAnimation { duration: Metrics.durationFast }
    }

    Rectangle {
        visible: root.isSelected
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 3
        radius: Metrics.radiusFull
        color: root.notebookColor
        anchors.leftMargin: 8
        anchors.topMargin: 10
        anchors.bottomMargin: 10
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Metrics.xl
        anchors.rightMargin: Metrics.lg
        spacing: Metrics.sm

        Rectangle {
            width: 16
            height: 12
            radius: 2
            color: root.notebookColor

            Rectangle {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: 4
                radius: 2
                color: "white"
                opacity: 0.2
            }
        }

        Text {
            Layout.fillWidth: true
            text: root.name
            font.family: Typography.fontPrimary
            font.weight: root.isSelected ? Typography.weightMedium : Typography.weightRegular
            font.pixelSize: Typography.bodySmall
            color: root.isSelected ? Colors.primary700 : Colors.textSecondary
            elide: Text.ElideRight
        }

        Rectangle {
            visible: root.noteCount > 0
            height: 18
            width: countText.width + 12
            radius: Metrics.radiusFull
            color: root.isSelected ? root.notebookColor : Colors.bgTertiary

            Behavior on color {
                ColorAnimation { duration: Metrics.durationFast }
            }

            Text {
                id: countText
                anchors.centerIn: parent
                text: root.noteCount
                font.family: Typography.fontPrimary
                font.weight: Typography.weightMedium
                font.pixelSize: 10
                color: root.isSelected ? Colors.textInverse : Colors.textTertiary
            }
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.clicked()
        onPressed: root.scale = 0.98
        onReleased: root.scale = 1.0
    }
}
