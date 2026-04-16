import QtQuick
import QtQuick.Layouts
import theme

Rectangle {
    id: root

    property bool sidebarHidden: false
    property bool noteListHidden: false
    signal toggleSidebar()
    signal toggleNoteList()

    height: Metrics.headerHeight
    color: "transparent"

    RowLayout {
        id: leftSection
        anchors.left: parent.left
        anchors.leftMargin: Metrics.xl
        anchors.verticalCenter: parent.verticalCenter
        spacing: Metrics.md

        Rectangle {
            id: menuBtn
            width: 36
            height: 36
            radius: Metrics.radiusMd
            color: menuArea.containsMouse ? Colors.primary100 : "transparent"
            border.width: 1
            border.color: menuArea.containsMouse ? Colors.primary200 : "transparent"

            Behavior on color {
                ColorAnimation { duration: Metrics.durationFast }
            }

            Behavior on scale {
                NumberAnimation { duration: Metrics.durationFast }
            }

            MouseArea {
                id: menuArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: root.toggleSidebar()
                onPressed: parent.scale = 0.97
                onReleased: parent.scale = 1.0
            }

            Column {
                anchors.centerIn: parent
                spacing: 4
                Rectangle {
                    width: 16
                    height: 2
                    radius: 1
                    color: root.sidebarHidden ? Colors.textTertiary : Colors.textPrimary
                }
                Rectangle {
                    width: root.sidebarHidden ? 10 : 16
                    height: 2
                    radius: 1
                    color: root.sidebarHidden ? Colors.textTertiary : Colors.textPrimary
                    Behavior on width { NumberAnimation { duration: Metrics.durationFast } }
                }
                Rectangle {
                    width: root.sidebarHidden ? 6 : 12
                    height: 2
                    radius: 1
                    color: root.sidebarHidden ? Colors.textTertiary : Colors.textPrimary
                    Behavior on width { NumberAnimation { duration: Metrics.durationFast } }
                }
            }
        }

        // Note list toggle button
        Rectangle {
            id: noteListBtn
            width: 36
            height: 36
            radius: Metrics.radiusMd
            color: noteListArea.containsMouse ? Colors.primary100 : (root.noteListHidden ? Colors.bgSecondary : "transparent")
            border.width: 1
            border.color: noteListArea.containsMouse ? Colors.primary200 : (root.noteListHidden ? Colors.borderLight : "transparent")

            Behavior on color {
                ColorAnimation { duration: Metrics.durationFast }
            }

            MouseArea {
                id: noteListArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: root.toggleNoteList()
                onPressed: parent.scale = 0.97
                onReleased: parent.scale = 1.0
            }

            // Note list icon: two vertical columns
            Row {
                anchors.centerIn: parent
                spacing: 3

                Column {
                    spacing: 3
                    anchors.verticalCenter: parent.verticalCenter
                    Rectangle { width: 6; height: 10; radius: 1; color: root.noteListHidden ? Colors.textTertiary : Colors.textPrimary }
                    Rectangle { width: 6; height: 4; radius: 1; color: root.noteListHidden ? Colors.textTertiary : Colors.textPrimary }
                }
                Column {
                    spacing: 3
                    anchors.verticalCenter: parent.verticalCenter
                    Rectangle { width: 6; height: 6; radius: 1; color: root.noteListHidden ? Colors.textTertiary : Colors.textPrimary }
                    Rectangle { width: 6; height: 8; radius: 1; color: root.noteListHidden ? Colors.textTertiary : Colors.textPrimary }
                }
            }
        }

        RowLayout {
            spacing: Metrics.sm
            Layout.alignment: Qt.AlignVCenter

            Rectangle {
                width: 28
                height: 28
                radius: Metrics.radiusFull
                gradient: Gradient {
                    GradientStop { position: 0.0; color: Colors.accentOrange }
                    GradientStop { position: 1.0; color: Colors.accentRose }
                }

                Rectangle {
                    width: 6
                    height: 6
                    radius: Metrics.radiusFull
                    color: "white"
                    opacity: 0.9
                    anchors.centerIn: parent
                    anchors.horizontalCenterOffset: -4
                    anchors.verticalCenterOffset: -4
                }
                Rectangle {
                    width: 4
                    height: 4
                    radius: Metrics.radiusFull
                    color: "white"
                    opacity: 0.7
                    anchors.centerIn: parent
                    anchors.horizontalCenterOffset: 3
                    anchors.verticalCenterOffset: -2
                }
                Rectangle {
                    width: 5
                    height: 5
                    radius: Metrics.radiusFull
                    color: "white"
                    opacity: 0.8
                    anchors.centerIn: parent
                    anchors.horizontalCenterOffset: -2
                    anchors.verticalCenterOffset: 5
                }
            }

            Text {
                text: "Nuni Note"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightSemibold
                font.pixelSize: Typography.h5
                color: Colors.textPrimary
                font.letterSpacing: Typography.letterSpacingTight
            }
        }
    }

    RowLayout {
        anchors.right: parent.right
        anchors.rightMargin: Metrics.xl
        anchors.verticalCenter: parent.verticalCenter
        spacing: Metrics.sm

        Rectangle {
            width: 8
            height: 8
            radius: Metrics.radiusFull
            color: Colors.success

            SequentialAnimation on scale {
                loops: Animation.Infinite
                NumberAnimation { to: 1.3; duration: 1000 }
                NumberAnimation { to: 1.0; duration: 1000 }
            }

            SequentialAnimation on opacity {
                loops: Animation.Infinite
                NumberAnimation { to: 0.5; duration: 1000 }
                NumberAnimation { to: 1.0; duration: 1000 }
            }
        }

        Text {
            text: "Ready"
            font.family: Typography.fontPrimary
            font.weight: Typography.weightMedium
            font.pixelSize: Typography.caption
            color: Colors.textSecondary
        }
    }

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 1
        color: Colors.borderLight
        opacity: 0.5
    }
}
