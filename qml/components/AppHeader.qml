import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import theme

Rectangle {
    id: root

    signal logoClicked()
    signal importClicked()
    signal importFilesClicked()
    signal printCurrentNoteClicked()
    signal currentNoteExportClicked()
    signal exportClicked()
    signal settingsClicked()
    signal hwpConversionToolClicked()
    signal ollamaModelToolClicked()
    signal helpClicked()

    property string currentNoteExportIconSource: ""
    property string printIconSource: ""
    property string importIconSource: ""
    property string exportIconSource: ""
    property bool printButtonEnabled: true
    property bool currentNoteExportEnabled: true

    function openMenuAt(menuRef, anchorItem) {
        if (!menuRef || !anchorItem) return
        var point = anchorItem.mapToItem(root, 0, anchorItem.height)
        menuRef.x = point.x
        menuRef.y = point.y + 4
        menuRef.open()
    }

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
            id: noteMenuButton
            Layout.preferredHeight: 32
            Layout.preferredWidth: noteMenuLabel.implicitWidth + noteMenuArrow.implicitWidth + Metrics.md * 2
            radius: Metrics.radiusSm
            color: (noteMenuMA.containsMouse || noteActionsMenu.visible) ? Colors.bgSecondary : "transparent"
            border.width: 1
            border.color: (noteMenuMA.containsMouse || noteActionsMenu.visible) ? Colors.borderLight : "transparent"

            RowLayout {
                anchors.fill: parent
                anchors.margins: Metrics.sm
                spacing: Metrics.xs

                Text {
                    id: noteMenuLabel
                    text: "노트 작업"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    font.weight: Typography.weightMedium
                    color: Colors.textPrimary
                }

                Text {
                    id: noteMenuArrow
                    text: "▼"
                    font.pixelSize: 12
                    color: Colors.textSecondary
                }
            }

            MouseArea {
                id: noteMenuMA
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (noteActionsMenu.visible) {
                        noteActionsMenu.close()
                    } else {
                        root.openMenuAt(noteActionsMenu, noteMenuButton)
                    }
                }
            }
        }

        Rectangle {
            id: fileMenuButton
            Layout.preferredHeight: 32
            Layout.preferredWidth: fileMenuLabel.implicitWidth + fileMenuArrow.implicitWidth + Metrics.md * 2
            radius: Metrics.radiusSm
            color: (fileMenuMA.containsMouse || fileActionsMenu.visible) ? Colors.bgSecondary : "transparent"
            border.width: 1
            border.color: (fileMenuMA.containsMouse || fileActionsMenu.visible) ? Colors.borderLight : "transparent"

            RowLayout {
                anchors.fill: parent
                anchors.margins: Metrics.sm
                spacing: Metrics.xs

                Text {
                    id: fileMenuLabel
                    text: "파일 작업"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    font.weight: Typography.weightMedium
                    color: Colors.textPrimary
                }

                Text {
                    id: fileMenuArrow
                    text: "▼"
                    font.pixelSize: 12
                    color: Colors.textSecondary
                }
            }

            MouseArea {
                id: fileMenuMA
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (fileActionsMenu.visible) {
                        fileActionsMenu.close()
                    } else {
                        root.openMenuAt(fileActionsMenu, fileMenuButton)
                    }
                }
            }
        }

        Rectangle {
            id: toolsMenuButton
            Layout.preferredHeight: 32
            Layout.preferredWidth: toolsMenuLabel.implicitWidth + toolsMenuArrow.implicitWidth + Metrics.md * 2
            radius: Metrics.radiusSm
            color: (toolsMenuMA.containsMouse || toolsActionsMenu.visible) ? Colors.bgSecondary : "transparent"
            border.width: 1
            border.color: (toolsMenuMA.containsMouse || toolsActionsMenu.visible) ? Colors.borderLight : "transparent"

            RowLayout {
                anchors.fill: parent
                anchors.margins: Metrics.sm
                spacing: Metrics.xs

                Text {
                    id: toolsMenuLabel
                    text: "도구"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    font.weight: Typography.weightMedium
                    color: Colors.textPrimary
                }

                Text {
                    id: toolsMenuArrow
                    text: "▼"
                    font.pixelSize: 12
                    color: Colors.textSecondary
                }
            }

            MouseArea {
                id: toolsMenuMA
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (toolsActionsMenu.visible) {
                        toolsActionsMenu.close()
                    } else {
                        root.openMenuAt(toolsActionsMenu, toolsMenuButton)
                    }
                }
            }
        }

        Rectangle {
            id: settingsTextButton
            Layout.preferredHeight: 32
            Layout.preferredWidth: settingsLabel.implicitWidth + Metrics.md * 2
            radius: Metrics.radiusSm
            color: settingsMA.containsMouse ? Colors.bgSecondary : "transparent"
            border.width: 1
            border.color: settingsMA.containsMouse ? Colors.borderLight : "transparent"

            Text {
                id: settingsLabel
                anchors.centerIn: parent
                text: "설정"
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.bodySmall
                font.weight: Typography.weightMedium
                color: Colors.textPrimary
            }

            MouseArea {
                id: settingsMA
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.settingsClicked()
            }
        }

        Rectangle {
            id: helpIconButton
            Layout.preferredHeight: 32
            Layout.preferredWidth: 32
            radius: Metrics.radiusSm
            color: helpIconMA.containsMouse ? Colors.bgSecondary : "transparent"
            border.width: 1
            border.color: helpIconMA.containsMouse ? Colors.borderLight : "transparent"

            Image {
                anchors.fill: parent
                anchors.margins: 4
                source: "../assets/icons/grammar_icon.png"
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
            }

            ToolTip.visible: helpIconMA.containsMouse
            ToolTip.text: "도움말"
            ToolTip.delay: 500

            MouseArea {
                id: helpIconMA
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.helpClicked()
            }

            Accessible.role: Accessible.Button
            Accessible.name: "AI 마크다운 문법 도움말 열기"
        }
    }

    Menu {
        id: noteActionsMenu
        parent: root
        visible: false
        implicitWidth: 200
        padding: Metrics.xs
        background: Rectangle {
            color: Colors.bgPrimary
            radius: Metrics.radiusLg
            border.color: Colors.borderLight
            border.width: 1
        }

        MenuItem {
            text: "현재 노트 출력"
            enabled: root.printButtonEnabled
            width: noteActionsMenu.implicitWidth
            implicitHeight: 34
            font.family: Typography.fontPrimary
            font.pixelSize: Typography.bodySmall
            onTriggered: root.printCurrentNoteClicked()
            background: Rectangle {
                color: control.down ? Colors.primary100 : (control.hovered ? Colors.bgSecondary : "transparent")
                radius: Metrics.radiusSm
            }
        }

        MenuItem {
            text: "노트 변환"
            enabled: root.currentNoteExportEnabled
            width: noteActionsMenu.implicitWidth
            implicitHeight: 34
            font.family: Typography.fontPrimary
            font.pixelSize: Typography.bodySmall
            onTriggered: root.currentNoteExportClicked()
            background: Rectangle {
                color: control.down ? Colors.primary100 : (control.hovered ? Colors.bgSecondary : "transparent")
                radius: Metrics.radiusSm
            }
        }
    }

    Menu {
        id: fileActionsMenu
        parent: root
        visible: false
        implicitWidth: 200
        padding: Metrics.xs
        background: Rectangle {
            color: Colors.bgPrimary
            radius: Metrics.radiusLg
            border.color: Colors.borderLight
            border.width: 1
        }

        MenuItem {
            text: "파일 가져오기"
            width: fileActionsMenu.implicitWidth
            implicitHeight: 34
            font.family: Typography.fontPrimary
            font.pixelSize: Typography.bodySmall
            onTriggered: root.importFilesClicked()
            background: Rectangle {
                color: control.down ? Colors.primary100 : (control.hovered ? Colors.bgSecondary : "transparent")
                radius: Metrics.radiusSm
            }
        }

        MenuItem {
            text: "폴더 가져오기"
            width: fileActionsMenu.implicitWidth
            implicitHeight: 34
            font.family: Typography.fontPrimary
            font.pixelSize: Typography.bodySmall
            onTriggered: root.importClicked()
            background: Rectangle {
                color: control.down ? Colors.primary100 : (control.hovered ? Colors.bgSecondary : "transparent")
                radius: Metrics.radiusSm
            }
        }

        MenuItem {
            text: "폴더 일괄 내보내기"
            width: fileActionsMenu.implicitWidth
            implicitHeight: 34
            font.family: Typography.fontPrimary
            font.pixelSize: Typography.bodySmall
            onTriggered: root.exportClicked()
            background: Rectangle {
                color: control.down ? Colors.primary100 : (control.hovered ? Colors.bgSecondary : "transparent")
                radius: Metrics.radiusSm
            }
        }
    }

    Menu {
        id: toolsActionsMenu
        parent: root
        visible: false
        implicitWidth: 200
        padding: Metrics.xs
        background: Rectangle {
            color: Colors.bgPrimary
            radius: Metrics.radiusLg
            border.color: Colors.borderLight
            border.width: 1
        }

        MenuItem {
            text: "한글 파일 변환"
            width: toolsActionsMenu.implicitWidth
            implicitHeight: 34
            font.family: Typography.fontPrimary
            font.pixelSize: Typography.bodySmall
            onTriggered: root.hwpConversionToolClicked()
            ToolTip.visible: hovered
            ToolTip.text: "HWP 파일을 HWPX로 변환하는 외부 도구를 실행합니다."
            background: Rectangle {
                color: control.down ? Colors.primary100 : (control.hovered ? Colors.bgSecondary : "transparent")
                radius: Metrics.radiusSm
            }
        }

        MenuItem {
            text: "Ollama 모델 등록"
            width: toolsActionsMenu.implicitWidth
            implicitHeight: 34
            font.family: Typography.fontPrimary
            font.pixelSize: Typography.bodySmall
            onTriggered: root.ollamaModelToolClicked()
            ToolTip.visible: hovered
            ToolTip.text: "누니노트에서 사용할 Ollama 모델 등록 도구를 실행합니다."
            background: Rectangle {
                color: control.down ? Colors.primary100 : (control.hovered ? Colors.bgSecondary : "transparent")
                radius: Metrics.radiusSm
            }
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
