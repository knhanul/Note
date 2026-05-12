import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import theme

Rectangle {
    id: root
    visible: false
    anchors.centerIn: parent
    width: 400
    height: 280
    radius: Metrics.radiusXxl
    color: Colors.bgPrimary
    border.color: Colors.borderLight
    border.width: 1
    z: 9000

    property real initialScale: 1.0
    property real currentScale: 1.0

    signal applyRequested(real scale)
    signal cancelled()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.lg
        spacing: Metrics.md

        Text {
            Layout.fillWidth: true
            text: "UI 크기 설정"
            font.family: Typography.fontPrimary
            font.pixelSize: Typography.h4
            font.weight: Typography.weightSemibold
            color: Colors.textPrimary
        }

        Text {
            Layout.fillWidth: true
            text: "전체 UI의 글자 크기와 컴포넌트 크기를 조절합니다. 변경 사항을 적용하려면 앱을 재시작해야 합니다."
            font.family: Typography.fontPrimary
            font.pixelSize: Typography.bodySmall
            color: Colors.textSecondary
            wrapMode: Text.Wrap
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.sm

            Rectangle {
                width: 40
                height: 40
                radius: Metrics.radiusMd
                color: decreaseMA.containsMouse ? Colors.bgTertiary : "transparent"
                border.color: Colors.borderLight
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "−"
                    font.pixelSize: Typography.h4
                    color: Colors.textSecondary
                }

                MouseArea {
                    id: decreaseMA
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        var newScale = Math.max(0.75, Math.round((root.currentScale - 0.05) * 100) / 100)
                        root.currentScale = newScale
                    }
                }
            }

            Slider {
                Layout.fillWidth: true
                from: 0.75
                to: 1.5
                stepSize: 0.05
                value: root.currentScale
                onValueChanged: {
                    root.currentScale = Math.round(value * 100) / 100
                }
            }

            Rectangle {
                width: 40
                height: 40
                radius: Metrics.radiusMd
                color: increaseMA.containsMouse ? Colors.bgTertiary : "transparent"
                border.color: Colors.borderLight
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "+"
                    font.pixelSize: Typography.h4
                    color: Colors.textSecondary
                }

                MouseArea {
                    id: increaseMA
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        var newScale = Math.min(1.5, Math.round((root.currentScale + 0.05) * 100) / 100)
                        root.currentScale = newScale
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true

            Text {
                Layout.fillWidth: true
                text: Math.round(root.currentScale * 100) + "%"
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.h3
                font.weight: Typography.weightSemibold
                color: Colors.primary600
            }

            Button {
                text: "취소"
                onClicked: root.cancelled()
            }

            Button {
                text: "적용"
                highlighted: true
                onClicked: root.applyRequested(root.currentScale)
            }
        }
    }
}
