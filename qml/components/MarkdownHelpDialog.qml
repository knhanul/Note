import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import theme

Item {
    id: root
    visible: false
    anchors.fill: parent
    z: 20000

    signal closed()

    property int maxModalWidth: 1200
    property int modalWidth: parent.width < 700 ? Math.min(parent.width * 0.95, maxModalWidth) : Math.min(parent.width * 0.85, maxModalWidth)
    property int modalHeight: Math.min(parent.height * 0.85, 820)

    Rectangle {
        id: overlay
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.35)

        MouseArea {
            anchors.fill: parent
            onClicked: root.close()
        }
    }

    Rectangle {
        id: modalCard
        anchors.centerIn: parent
        width: root.modalWidth
        height: root.modalHeight
        radius: Metrics.radiusXxl
        color: Colors.bgPrimary
        border.color: Colors.borderLight
        border.width: 1

        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Metrics.lg
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.sm

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        Layout.fillWidth: true
                        text: "AI 마크다운 문법 도움말"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.h4
                        font.weight: Typography.weightSemibold
                        color: Colors.textPrimary
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "마크다운 문법을 활용하면 문서를 구조화하고 AI가 더 쉽게 이해할 수 있습니다."
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.bodySmall
                        color: Colors.textSecondary
                        wrapMode: Text.Wrap
                    }
                }

                Rectangle {
                    width: 32
                    height: 32
                    radius: Metrics.radiusSm
                    color: closeBtnMA.containsMouse ? Colors.bgSecondary : "transparent"
                    border.width: 0

                    Text {
                        anchors.centerIn: parent
                        text: "✕"
                        font.pixelSize: 16
                        font.weight: Typography.weightMedium
                        color: closeBtnMA.containsMouse ? Colors.textPrimary : Colors.textTertiary
                    }

                    MouseArea {
                        id: closeBtnMA
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.close()
                    }

                    Accessible.role: Accessible.Button
                    Accessible.name: "도움말 닫기"
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.topMargin: Metrics.md
                Layout.bottomMargin: Metrics.md
                height: 1
                color: Colors.borderLight
            }

            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: helpImage.implicitHeight + Metrics.lg * 2
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AsNeeded
                }

                Image {
                    id: helpImage
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: Metrics.lg
                    width: Math.min(parent.width - Metrics.lg * 2, implicitWidth)
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                    source: "file:///" + (typeof appImagePath !== "undefined" && appImagePath !== ""
                                          ? appImagePath
                                          : "").replace(/\\/g, "/")
                }
            }
        }
    }

    function open() {
        root.visible = true
        modalCard.forceActiveFocus()
    }

    function close() {
        root.visible = false
        root.closed()
    }

    Shortcut {
        sequence: "Escape"
        enabled: root.visible
        onActivated: root.close()
    }

    onVisibleChanged: {
        if (visible) {
            modalCard.forceActiveFocus()
        }
    }
}
