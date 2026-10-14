import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Effects
import theme

Item {
    id: root
    visible: false
    anchors.fill: parent
    z: 20020

    signal closed()

    // Program-level info injected via context properties
    property string imagePath: (typeof aboutImagePath !== "undefined") ? aboutImagePath : ""
    property string appNameText: (typeof appName !== "undefined" && appName) ? appName : ""
    property string versionText: (typeof appVersion !== "undefined" && appVersion) ? appVersion : "정보 없음"
    property string buildDateText: (typeof appBuildDate !== "undefined" && appBuildDate) ? appBuildDate : "정보 없음"
    property string creatorText: (typeof appCreator !== "undefined" && appCreator) ? appCreator : "정보 없음"
    property color accentColor: (typeof appAccentColor !== "undefined" && appAccentColor !== "") ? appAccentColor : Colors.primary600

    function open() {
        root.visible = true
    }

    function close() {
        root.visible = false
        root.closed()
    }

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
        id: card
        anchors.centerIn: parent
        width: Math.min(360, root.width - 40)
        height: cardContent.implicitHeight + 40
        radius: 15
        color: "#FCFAF7"
        border.color: "#E8E5E1"
        border.width: 1

        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }

        ColumnLayout {
            id: cardContent
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 20
            spacing: 10

            // ── 대표 이미지 ──────────────────────────────────────────
            Item {
                id: imageArea
                Layout.fillWidth: true
                visible: aboutImage.status === Image.Ready && aboutImage.implicitWidth > 0
                readonly property real aspect: aboutImage.implicitWidth > 0
                                               ? aboutImage.implicitHeight / aboutImage.implicitWidth : 0
                Layout.preferredHeight: visible ? Math.round(Math.min(width * aspect, 200)) : 0
                Layout.bottomMargin: visible ? 4 : 0

                Image {
                    id: aboutImage
                    anchors.centerIn: parent
                    width: imageArea.aspect > 0
                           ? Math.min(imageArea.width, 200 / imageArea.aspect) : 0
                    height: width * imageArea.aspect
                    source: root.imagePath !== "" ? "file:///" + root.imagePath.replace(/\\/g, "/") : ""
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                    asynchronous: true
                    visible: false
                }

                MultiEffect {
                    source: aboutImage
                    anchors.fill: aboutImage
                    visible: imageArea.visible
                    maskEnabled: true
                    maskSource: imageMask
                }

                Item {
                    id: imageMask
                    width: aboutImage.width
                    height: aboutImage.height
                    visible: false
                    layer.enabled: true
                    layer.smooth: true

                    Rectangle {
                        anchors.fill: parent
                        radius: 11
                        color: "black"
                    }
                }
            }

            // ── 프로그램명 ──────────────────────────────────────────
            Text {
                Layout.fillWidth: true
                text: root.appNameText
                font.family: Typography.fontPrimary
                font.pixelSize: 24
                font.weight: Typography.weightSemibold
                color: root.accentColor
                wrapMode: Text.Wrap
                horizontalAlignment: Text.AlignLeft
            }

            // ── 구분선 ──────────────────────────────────────────────
            Rectangle {
                Layout.fillWidth: true
                Layout.topMargin: 2
                Layout.bottomMargin: 4
                height: 1
                color: "#E8E5E1"
            }

            // ── 상세 정보 (버전 / 빌드일자 / 제작) ─────────────────────
            GridLayout {
                Layout.fillWidth: true
                columns: 2
                columnSpacing: 16
                rowSpacing: 8

                Repeater {
                    model: [
                        { label: "버전", value: root.versionText },
                        { label: "빌드일자", value: root.buildDateText },
                        { label: "제작", value: root.creatorText }
                    ]

                    delegate: RowLayout {
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true
                        Layout.columnSpan: 2
                        spacing: 0

                        Text {
                            Layout.preferredWidth: 64
                            Layout.alignment: Qt.AlignTop
                            text: modelData.label
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            color: "#777777"
                        }

                        Text {
                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignTop
                            text: modelData.value
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            color: "#343434"
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }

            // ── 닫기 버튼 ───────────────────────────────────────────
            Rectangle {
                Layout.alignment: Qt.AlignRight
                Layout.topMargin: 6
                Layout.preferredWidth: closeLabel.implicitWidth + 28
                Layout.preferredHeight: 30
                radius: 8
                color: closeMA.containsMouse ? "#E8E5E1" : "#EFEDE9"
                border.width: 1
                border.color: "#E0DDD8"

                Text {
                    id: closeLabel
                    anchors.centerIn: parent
                    text: "닫기"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    font.weight: Typography.weightMedium
                    color: "#343434"
                }

                MouseArea {
                    id: closeMA
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.close()
                }

                Accessible.role: Accessible.Button
                Accessible.name: "정보 팝업 닫기"
            }
        }
    }

    Shortcut {
        sequence: "Escape"
        enabled: root.visible
        onActivated: root.close()
    }
}
