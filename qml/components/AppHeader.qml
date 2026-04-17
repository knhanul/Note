import QtQuick
import QtQuick.Layouts
import theme

Rectangle {
    id: root

    signal logoClicked()

    height: Metrics.headerHeight
    color: "transparent"

    // ── Left: Logo + App name (클릭으로 패널 사이클) ──────────
    Item {
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

    // ── Right: Status ──────────────────────────────────────────
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
