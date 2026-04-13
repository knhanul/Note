import QtQuick
import QtQuick.Layouts
import theme

Rectangle {
    id: root

    property bool boldActive: false
    property bool italicActive: false
    property bool headingActive: false
    property bool codeActive: false

    signal formatBold()
    signal formatItalic()
    signal formatHeading()
    signal formatCode()
    signal insertLink()
    signal insertImage()
    signal insertTable()
    signal insertBulletList()
    signal insertNumberedList()
    signal insertQuote()

    width: toolbarRow.implicitWidth + Metrics.md
    height: Metrics.toolbarHeight
    radius: Metrics.radiusFull
    color: Colors.bgSecondary
    border.width: 1
    border.color: Colors.borderLight

    RowLayout {
        id: toolbarRow
        anchors.centerIn: parent
        spacing: Metrics.xs

        Row {
            spacing: Metrics.xs

            ToolButton {
                icon: "B"
                tooltip: "Bold"
                isActive: root.boldActive
                onClicked: root.formatBold()
            }

            ToolButton {
                icon: "I"
                tooltip: "Italic"
                isItalic: true
                isActive: root.italicActive
                onClicked: root.formatItalic()
            }

            Rectangle {
                width: 1
                height: 20
                color: Colors.borderMedium
                anchors.verticalCenter: parent.verticalCenter
            }

            ToolButton {
                icon: "H"
                tooltip: "Heading"
                isActive: root.headingActive
                onClicked: root.formatHeading()
            }

            ToolButton {
                icon: "</>"
                tooltip: "Code"
                fontSize: 10
                isActive: root.codeActive
                onClicked: root.formatCode()
            }

            Rectangle {
                width: 1
                height: 20
                color: Colors.borderMedium
                anchors.verticalCenter: parent.verticalCenter
            }

            ToolButton {
                icon: "🔗"
                tooltip: "Link"
                fontSize: 14
                onClicked: root.insertLink()
            }

            ToolButton {
                icon: "🖼️"
                tooltip: "Image"
                fontSize: 12
                onClicked: root.insertImage()
            }

            ToolButton {
                icon: "⊞"
                tooltip: "Table"
                fontSize: 14
                onClicked: root.insertTable()
            }

            Rectangle {
                width: 1
                height: 20
                color: Colors.borderMedium
                anchors.verticalCenter: parent.verticalCenter
            }

            ToolButton {
                icon: "•"
                tooltip: "Bullet List"
                onClicked: root.insertBulletList()
            }

            ToolButton {
                icon: "1."
                tooltip: "Numbered List"
                fontSize: 10
                onClicked: root.insertNumberedList()
            }

            ToolButton {
                icon: "❝"
                tooltip: "Quote"
                fontSize: 14
                onClicked: root.insertQuote()
            }
        }
    }

    component ToolButton: Rectangle {
        id: btn

        property string icon: ""
        property string tooltip: ""
        property bool isActive: false
        property bool isItalic: false
        property int fontSize: 12

        signal clicked()

        width: 32
        height: 32
        radius: Metrics.radiusMd
        color: {
            if (isActive) return Colors.primary500
            if (btnArea.containsMouse) return Colors.bgTertiary
            return "transparent"
        }

        Behavior on color {
            ColorAnimation { duration: Metrics.durationFast }
        }

        Behavior on scale {
            NumberAnimation { duration: Metrics.durationFast }
        }

        Text {
            anchors.centerIn: parent
            text: btn.icon
            font.family: isItalic ? Typography.fontPrimary : Typography.fontMono
            font.weight: Typography.weightSemibold
            font.italic: isItalic
            font.pixelSize: btn.fontSize
            color: btn.isActive ? Colors.textInverse : Colors.textSecondary
        }

        MouseArea {
            id: btnArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: btn.clicked()
            onPressed: btn.scale = 0.95
            onReleased: btn.scale = 1.0
        }
    }
}
