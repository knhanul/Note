import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import theme

Rectangle {
    id: root
    color: Colors.bgPrimary
    border.color: Colors.borderLight
    border.width: 1
    radius: 0
    Layout.minimumWidth: 320
    Layout.preferredWidth: 360
    Layout.maximumWidth: 440
    clip: true

    signal openSettingsDialog()
    property string responseText: ""
    property bool aiConnected: typeof aiAssistantController !== "undefined" && aiAssistantController !== null ? aiAssistantController.isConnected : false
    property string aiChatModel: typeof aiAssistantController !== "undefined" && aiAssistantController !== null ? aiAssistantController.chatModel : ""
    property string aiEmbeddingModel: typeof aiAssistantController !== "undefined" && aiAssistantController !== null ? aiAssistantController.embeddingModel : ""
    property string aiPerformanceMode: typeof aiAssistantController !== "undefined" && aiAssistantController !== null ? aiAssistantController.performanceMode : "low"
    property var aiModelList: typeof aiAssistantController !== "undefined" && aiAssistantController !== null ? aiAssistantController.modelList : []
    property bool aiRunning: typeof assistantController !== "undefined" && assistantController !== null ? assistantController.isRunning : false

    function getController() {
        return typeof aiAssistantController !== "undefined" && aiAssistantController !== null ? aiAssistantController : null
    }

    function getAssistantController() {
        return typeof assistantController !== "undefined" && assistantController !== null ? assistantController : null
    }

    function safeGet(prop, defaultVal) {
        var c = getController()
        return c && c[prop] !== undefined ? c[prop] : defaultVal
    }

    function safeAssistantGet(prop, defaultVal) {
        var c = getAssistantController()
        return c && c[prop] !== undefined ? c[prop] : defaultVal
    }

    function canUseAI() {
        return safeGet("isConnected", false) && safeGet("chatModel", "") !== ""
    }

    Component.onCompleted: {
        var ac = getAssistantController()
        if (ac) {
            ac.tokenReceived.connect(function(token) {
                root.responseText += token
            })
            ac.runningChanged.connect(function(running) {
                if (!running) {
                    console.log("[AIAssistantPanel] Task finished")
                }
            })
            ac.errorOccurred.connect(function(error) {
                root.responseText += "\n[오류] " + error
            })
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.lg
        spacing: Metrics.md

        ScrollView {
            id: panelScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ScrollBar.vertical.policy: ScrollBar.AsNeeded

            Column {
                id: sidebarContent
                width: root.width - (Metrics.lg * 2)
                spacing: Metrics.lg

                Column {
                    spacing: Metrics.xs

                    RowLayout {
                        spacing: Metrics.sm

                        Text {
                            text: "AI 업무비서"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodyLarge
                            font.bold: true
                            color: Colors.textPrimary
                        }

                        Rectangle {
                            height: 24
                            radius: Metrics.radiusFull
                            color: Colors.bgSecondary
                            border.color: safeGet("isConnected", false) ? Colors.success : Colors.borderLight
                            border.width: 1
                            Row {
                                anchors.centerIn: parent
                                spacing: Metrics.xs

                                Rectangle {
                                    width: 6
                                    height: 6
                                    radius: Metrics.radiusFull
                                    color: safeGet("isConnected", false) ? Colors.success : Colors.textTertiary
                                }

                                Text {
                                    text: safeGet("isConnected", false) ? "연결됨" : "연결 안 됨"
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: safeGet("isConnected", false) ? Colors.textPrimary : Colors.textSecondary
                                }
                            }
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            Layout.preferredWidth: 32
                            Layout.preferredHeight: 32
                            radius: Metrics.radiusSm
                            color: settingsMA.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                            border.color: Colors.borderLight
                            border.width: 1

                            Text {
                                anchors.centerIn: parent
                                text: "⚙"
                                font.pixelSize: Typography.bodyLarge
                                color: Colors.textSecondary
                            }

                            MouseArea {
                                id: settingsMA
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: root.openSettingsDialog()
                            }
                        }
                    }

                    Flow {
                        width: parent.width
                        spacing: Metrics.xs

                        Rectangle {
                            height: 28
                            radius: Metrics.radiusFull
                            color: Colors.bgSecondary
                            border.color: Colors.borderLight
                            border.width: 1
                            Row {
                                anchors.centerIn: parent
                                spacing: Metrics.xs
                                Text {
                                    text: safeGet("chatModel", "") !== "" ? safeGet("chatModel", "") : "모델 미선택"
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.textSecondary
                                }
                            }
                        }

                        Rectangle {
                            height: 28
                            radius: Metrics.radiusFull
                            color: Colors.bgSecondary
                            border.color: Colors.borderLight
                            border.width: 1
                            Row {
                                anchors.centerIn: parent
                                spacing: Metrics.xs
                                Text {
                                    text: "성능 " + safeGet("performanceMode", "low")
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.textSecondary
                                }
                            }
                        }
                    }

                    Rectangle {
                        visible: !canUseAI()
                        width: parent.width
                        radius: Metrics.radiusMd
                        color: Colors.primary50
                        border.color: Colors.primary200
                        border.width: 1
                        anchors.margins: 0

                        Text {
                            anchors.fill: parent
                            anchors.margins: Metrics.md
                            text: "Ollama 연결 후 사용할 수 있습니다. 모델을 선택하고 연결을 확인해주세요."
                            wrapMode: Text.WordWrap
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: Colors.primary700
                        }
                    }
                }


                Rectangle {
                    width: parent.width
                    radius: Metrics.radiusLg
                    color: Colors.surface
                    border.color: Colors.borderLight
                    implicitHeight: quickActionsColumn.implicitHeight + (Metrics.md * 2)

                    Column {
                        id: quickActionsColumn
                        width: parent.width - (Metrics.md * 2)
                        spacing: Metrics.sm
                        anchors.centerIn: parent

                        Text {
                            text: "빠른 실행"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            font.weight: Typography.weightMedium
                            color: Colors.textPrimary
                        }

                        Text {
                            text: "현재 문서를 기반으로 바로 실행할 수 있는 도구입니다."
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: Colors.textSecondary
                        }

                        GridLayout {
                            columns: 2
                            columnSpacing: Metrics.sm
                            rowSpacing: Metrics.sm
                            width: parent.width

                            Button {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                text: "현재 문서 요약"
                                enabled: canUseAI() && !root.aiRunning && typeof window !== "undefined" && window.currentNote && window.currentNote.content
                                contentItem: Text {
                                    text: parent.text
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    font.weight: Typography.weightMedium
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    color: parent.enabled ? Colors.textPrimary : Colors.textTertiary
                                }
                                background: Rectangle {
                                    color: Colors.bgSecondary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                    opacity: parent.enabled ? 1 : 0.5
                                }
                                onClicked: {
                                    root.responseText = ""
                                    var ac = getAssistantController()
                                    if (ac && window.currentNote && window.currentNote.content) {
                                        ac.runTask("summarize_note", window.currentNote.content)
                                    }
                                }
                            }

                            Button {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                text: root.aiRunning ? "중지" : "선택 문장 다듬기"
                                enabled: canUseAI() && typeof window !== "undefined" && window.currentNote && window.currentNote.content
                                contentItem: Text {
                                    text: parent.text
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    font.weight: Typography.weightMedium
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    color: parent.enabled ? Colors.textPrimary : Colors.textTertiary
                                }
                                background: Rectangle {
                                    color: Colors.bgSecondary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                    opacity: parent.enabled ? 1 : 0.5
                                }
                                onClicked: {
                                    var ac = getAssistantController()
                                    if (!ac) return
                                    if (root.aiRunning) {
                                        ac.cancel()
                                        return
                                    }
                                    root.responseText = ""
                                    if (window.currentNote && window.currentNote.content) {
                                        ac.runTask("polish_selection", window.currentNote.content)
                                    }
                                }
                            }

                            Button {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                text: "할 일 추출"
                                enabled: canUseAI() && !root.aiRunning && typeof window !== "undefined" && window.currentNote && window.currentNote.content
                                contentItem: Text {
                                    text: parent.text
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    font.weight: Typography.weightMedium
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    color: parent.enabled ? Colors.textPrimary : Colors.textTertiary
                                }
                                background: Rectangle {
                                    color: Colors.bgSecondary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                    opacity: parent.enabled ? 1 : 0.5
                                }
                                onClicked: {
                                    root.responseText = ""
                                    var ac = getAssistantController()
                                    if (ac && window.currentNote && window.currentNote.content) {
                                        ac.runTask("extract_todo", window.currentNote.content)
                                    }
                                }
                            }

                            Button {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                text: "제목/태그 추천"
                                enabled: canUseAI() && !root.aiRunning && typeof window !== "undefined" && window.currentNote && window.currentNote.content
                                contentItem: Text {
                                    text: parent.text
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    font.weight: Typography.weightMedium
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    color: parent.enabled ? Colors.textPrimary : Colors.textTertiary
                                }
                                background: Rectangle {
                                    color: Colors.bgSecondary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                    opacity: parent.enabled ? 1 : 0.5
                                }
                                onClicked: {
                                    root.responseText = ""
                                    var ac = getAssistantController()
                                    if (ac && window.currentNote && window.currentNote.content) {
                                        ac.runTask("suggest_title_tags", window.currentNote.content)
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    radius: Metrics.radiusLg
                    color: Colors.surface
                    border.color: Colors.borderLight
                    implicitHeight: questionColumn.implicitHeight + (Metrics.md * 2)

                    Column {
                        id: questionColumn
                        width: parent.width - (Metrics.md * 2)
                        spacing: Metrics.sm
                        anchors.centerIn: parent

                        Text {
                            text: "현재 문서 질문"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            font.weight: Typography.weightMedium
                            color: Colors.textPrimary
                        }

                        TextField {
                            id: questionInput
                            width: parent.width
                            placeholderText: "문서에 대해 질문을 입력하세요"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            enabled: canUseAI() && !root.aiRunning && typeof window !== "undefined" && window.currentNote && window.currentNote.content
                        }

                        Button {
                            width: parent.width
                            Layout.preferredHeight: 40
                            text: "질문하기"
                            enabled: questionInput.text !== "" && canUseAI() && !root.aiRunning && typeof window !== "undefined" && window.currentNote && window.currentNote.content
                            contentItem: Text {
                                text: parent.text
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                color: Colors.white
                            }
                            background: Rectangle {
                                color: Colors.primary500
                                radius: Metrics.radiusSm
                                border.color: Colors.primary600
                                opacity: parent.enabled ? 1 : 0.5
                            }
                            onClicked: {
                                root.responseText = ""
                                var ac = getAssistantController()
                                if (ac && window.currentNote && window.currentNote.content && questionInput.text) {
                                    ac.askQuestion(window.currentNote.content, questionInput.text)
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    radius: Metrics.radiusLg
                    color: Colors.surface
                    border.color: Colors.borderLight
                    implicitHeight: resultPreviewLayout.implicitHeight + (Metrics.md * 2)

                    ColumnLayout {
                        id: resultPreviewLayout
                        anchors.fill: parent
                        anchors.margins: Metrics.md
                        spacing: Metrics.sm

                        Text {
                            text: "결과 미리보기"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            font.weight: Typography.weightMedium
                            color: Colors.textPrimary
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 220

                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                visible: root.responseText === ""

                                Column {
                                    anchors.centerIn: parent
                                    spacing: Metrics.xs
                                    Text {
                                        text: "아직 결과가 없습니다"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textSecondary
                                    }
                                    Text {
                                        text: "AI 작업을 실행하면 요약이나 답변이 이곳에 표시됩니다."
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        color: Colors.textTertiary
                                        horizontalAlignment: Text.AlignHCenter
                                        wrapMode: Text.WordWrap
                                    }
                                }
                            }

                            ScrollView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                visible: root.responseText !== ""
                                ScrollBar.vertical.policy: ScrollBar.AsNeeded

                                TextArea {
                                    text: root.responseText
                                    readOnly: true
                                    wrapMode: TextEdit.Wrap
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textPrimary
                                    background: null
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.sm

                            Button {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                text: "본문에 삽입"
                                enabled: root.responseText !== ""
                                contentItem: Text {
                                    text: parent.text
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    font.weight: Typography.weightMedium
                                    color: Colors.white
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    color: Colors.primary500
                                    radius: Metrics.radiusSm
                                    border.color: Colors.primary600
                                    opacity: parent.enabled ? 1 : 0.5
                                }
                                onClicked: {
                                    console.log("[AIAssistantPanel] 본문에 삽입 clicked")
                                }
                            }

                            Button {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                text: "새 노트로 저장"
                                enabled: root.responseText !== "" && typeof noteController !== "undefined"
                                contentItem: Text {
                                    text: parent.text
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    font.weight: Typography.weightMedium
                                    color: Colors.textPrimary
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    color: Colors.bgSecondary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                    opacity: parent.enabled ? 1 : 0.5
                                }
                                onClicked: {
                                    var ac = getAssistantController()
                                    if (ac && root.responseText) {
                                        ac.createNewNote("AI 결과", root.responseText, "")
                                    }
                                }
                            }

                            Button {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                text: "복사"
                                enabled: root.responseText !== ""
                                contentItem: Text {
                                    text: parent.text
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    font.weight: Typography.weightMedium
                                    color: Colors.textPrimary
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    color: Colors.surface
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                    opacity: parent.enabled ? 1 : 0.5
                                }
                                onClicked: {
                                    console.log("[AIAssistantPanel] 복사 clicked")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

