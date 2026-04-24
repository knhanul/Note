import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import theme

Rectangle {
    id: root

    signal logoClicked()
    signal syncClicked()
    signal importClicked()
    signal exportClicked()

    property string syncIconSource: ""
    property string importIconSource: ""
    property string exportIconSource: ""

    height: Metrics.headerHeight
    color: "transparent"

    // ── Left: Logo + App name (클릭으로 패널 사이클) ──────────
    Item {
        id: titleBlock
        anchors.left: parent.left
        anchors.leftMargin: Metrics.xl
        anchors.verticalCenter: parent.verticalCenter
        implicitWidth: headerRow.implicitWidth
        implicitHeight: headerRow.implicitHeight

        RowLayout {
            id: headerRow
            anchors.verticalCenter: parent.verticalCenter
            spacing: 6

            // Logo image
            Image {
                Layout.alignment: Qt.AlignVCenter
                source: (typeof appLogoPath !== "undefined" && appLogoPath !== "")
                        ? "file:///" + appLogoPath.replace(/\\/g, "/")
                        : ""
                Layout.preferredHeight: 64
                Layout.preferredWidth: 64
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
                visible: status === Image.Ready

                // Fallback circle
                Rectangle {
                    anchors.fill: parent
                    radius: width / 2
                    visible: parent.status !== Image.Ready
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: Colors.accentOrange }
                        GradientStop { position: 1.0; color: Colors.accentRose }
                    }
                    Rectangle {
                        width: 3; height: 3; radius: 1.5
                        color: "white"; opacity: 0.9
                        anchors.centerIn: parent
                        anchors.horizontalCenterOffset: -2; anchors.verticalCenterOffset: -2
                    }
                    Rectangle {
                        width: 2; height: 2; radius: 1
                        color: "white"; opacity: 0.7
                        anchors.centerIn: parent
                        anchors.horizontalCenterOffset: 2; anchors.verticalCenterOffset: -1
                    }
                    Rectangle {
                        width: 3; height: 3; radius: 1.5
                        color: "white"; opacity: 0.8
                        anchors.centerIn: parent
                        anchors.horizontalCenterOffset: -1; anchors.verticalCenterOffset: 2
                    }
                }
            }

            // App name
            Text {
                Layout.alignment: Qt.AlignVCenter
                text: (typeof appName !== "undefined" && appName) ? appName : "누니노트"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightSemibold
                font.pixelSize: 26
                color: Colors.textPrimary
                font.letterSpacing: Typography.letterSpacingTight
            }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: root.logoClicked()
        }
    }

    // ── Right: Toolbar + Status ──────────────────────────────────────────
    RowLayout {
        anchors.right: parent.right
        anchors.rightMargin: Metrics.xl
        anchors.verticalCenter: parent.verticalCenter
        spacing: Metrics.sm

        Rectangle {
            id: importBtn
            width: 32
            height: 32
            radius: 8
            color: importMA.containsMouse ? "#F0F5FF" : "transparent"
            border.width: 0

            Image {
                anchors.centerIn: parent
                width: 19
                height: 19
                source: root.importIconSource
                fillMode: Image.PreserveAspectFit
                visible: !!root.importIconSource
            }

            Text {
                anchors.centerIn: parent
                visible: !root.importIconSource
                text: "⤓"
                font.pixelSize: 18
                color: Colors.textSecondary
            }

            MouseArea {
                id: importMA
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.importClicked()
            }

            ToolTip.visible: importMA.containsMouse
            ToolTip.delay: 400
            ToolTip.text: "가져오기"
        }

        Rectangle {
            id: exportBtn
            width: 32
            height: 32
            radius: 8
            color: exportMA.containsMouse ? "#F0F5FF" : "transparent"
            border.width: 0

            Image {
                anchors.centerIn: parent
                width: 19
                height: 19
                source: root.exportIconSource
                fillMode: Image.PreserveAspectFit
                visible: !!root.exportIconSource
            }

            Text {
                anchors.centerIn: parent
                visible: !root.exportIconSource
                text: "⤒"
                font.pixelSize: 18
                color: Colors.textSecondary
            }

            MouseArea {
                id: exportMA
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.exportClicked()
            }

            ToolTip.visible: exportMA.containsMouse
            ToolTip.delay: 400
            ToolTip.text: "보내기"
        }

        // Sync button (between export and status)
        Rectangle {
            id: syncBtn
            width: 32
            height: 32
            radius: 8
            color: syncMA.containsMouse ? "#F0F5FF" : "transparent"
            border.width: 0

            Image {
                anchors.centerIn: parent
                width: 19
                height: 19
                source: root.syncIconSource
                fillMode: Image.PreserveAspectFit
                visible: !!root.syncIconSource
            }

            Text {
                anchors.centerIn: parent
                visible: !root.syncIconSource
                text: "⟳"
                font.pixelSize: 18
                color: Colors.textSecondary
            }

            MouseArea {
                id: syncMA
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.syncClicked()
            }

            ToolTip.visible: syncMA.containsMouse
            ToolTip.delay: 400
            ToolTip.text: "동기화"
        }

        // Separator
        Rectangle {
            Layout.alignment: Qt.AlignVCenter
            width: 1
            height: 20
            color: Colors.borderLight
            opacity: 0.9
        }

        // Status indicator
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
