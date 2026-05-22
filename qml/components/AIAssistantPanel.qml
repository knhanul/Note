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
    property bool aiRunning: false

    property var aiActionControllerObj: typeof aiActionController !== "undefined" && aiActionController !== null ? aiActionController : null
    property var enabledActionList: aiActionControllerObj ? aiActionControllerObj.enabledActionList : []
    property var selectedAction: ({})

    function getActionController() {
        return aiActionControllerObj
    }

    function refreshActionList() {
        var aac = getActionController()
        if (aac && aac.refresh) {
            aac.refresh()
        }
    }

    function getInputModeText(mode) {
        if (!mode || mode === "auto") return "자동 감지"
        if (mode === "note_required") return "현재 문서 기반"
        if (mode === "chat_only") return "채팅만 사용"
        if (mode === "note_and_chat") return "문서 + 질문"
        if (mode === "selection_required") return "선택 문장 기반"
        return "자동 감지"
    }

    function getResponseLengthText(value) {
        if (!value || value === "medium") return "보통"
        if (value === "short") return "짧게"
        if (value === "long") return "자세히"
        return "보통"
    }

    function getInputModePlaceholder(mode) {
        if (!mode || mode === "auto") return "선택한 AI 기능을 실행할 내용을 입력하세요."
        if (mode === "note_required") return "현재 열려 있는 문서를 기준으로 실행합니다. 필요한 요청이 있으면 입력하세요."
        if (mode === "chat_only") return "AI에게 물어볼 내용을 입력하세요."
        if (mode === "note_and_chat") return "현재 문서를 참고하고, 추가 질문도 함께 전달합니다."
        if (mode === "selection_required") return "문서에서 문장을 선택한 뒤 실행하세요."
        return "선택한 AI 기능을 실행할 내용을 입력하세요."
    }

    function isDefaultAction(actionId) {
        var defaults = ["summarize_note", "polish_selection", "extract_todo", "suggest_title_tags", "current_note_qa"]
        return defaults.indexOf(actionId) >= 0
    }

    function runSelectedAction() {
        var action = root.selectedAction
        if (!action || !action.action_id) return

        var ac = getAssistantController()
        if (!ac) return

        if (!canUseAI() || root.aiRunning) return

        var userInput = actionInput.text || ""
        var currentNoteJson = ""
        var selection = ""

        if (window.currentNote) {
            currentNoteJson = JSON.stringify({
                note_id: window.currentNote.note_id || "",
                title: window.currentNote.title || "",
                content: window.currentNote.content || "",
                tags: window.currentNote.tags || ""
            })
        }

        root.responseText = ""

        if (isDefaultAction(action.action_id)) {
            var content = ""
            if (window.currentNote && window.currentNote.content) {
                content = window.currentNote.content
            }
            ac.runTask(action.action_id, content)
        } else {
            ac.runCustomAction(action.action_id, userInput, currentNoteJson, selection, "[]")
        }
    }

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
        if (!ac)
            return

        root.aiRunning = ac.isRunning

        ac.tokenReceived.connect(function(token) {
            console.log("[AIAssistantPanel] Token received: length=" + token.length + ", responseText.length=" + root.responseText.length)
            root.responseText += token
        })

        ac.resultReady.connect(function(result) {
            console.log("[AIAssistantPanel] Result ready: length=" + result.length + ", responseText.length=" + root.responseText.length)
            if (result && result !== "") {
                root.responseText = result
            }
        })

        ac.runningChanged.connect(function(running) {
            root.aiRunning = running
            if (!running) {
                console.log("[AIAssistantPanel] Task finished, responseText.length=" + root.responseText.length)
            }
        })

        ac.errorOccurred.connect(function(error) {
            root.responseText += "\n[오류] " + error
        })

        root.refreshActionList()
    }

    Connections {
        target: aiActionControllerObj
        function onActionsChanged() {
            // Avoid recursion by not calling refreshActionList here
            // The actionList property will auto-update via signals
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
                    width: parent.width
                    spacing: Metrics.xs

                    RowLayout {
                        width: parent.width
                        spacing: Metrics.md

                        Text {
                            text: "AI 업무비서"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodyLarge
                            font.bold: true
                            color: Colors.textPrimary
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                        RowLayout {
                            spacing: Metrics.md

                            Rectangle {
                                Layout.preferredWidth: 80
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
                            text: "AI 기능 선택"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            font.weight: Typography.weightMedium
                            color: Colors.textPrimary
                        }

                        ComboBox {
                            id: actionSelector
                            width: parent.width
                            height: 36
                            model: root.enabledActionList.map(function(a) { return a.name || a.action_id })
                            currentIndex: 0
                            onCurrentIndexChanged: {
                                if (currentIndex >= 0 && currentIndex < root.enabledActionList.length) {
                                    root.selectedAction = root.enabledActionList[currentIndex]
                                }
                            }
                            Component.onCompleted: {
                                if (root.enabledActionList.length > 0) {
                                    root.selectedAction = root.enabledActionList[0]
                                }
                            }
                        }

                        Rectangle {
                            width: parent.width
                            radius: Metrics.radiusMd
                            color: Colors.bgSecondary
                            border.color: Colors.borderLight
                            visible: root.selectedAction && root.selectedAction.action_id

                            ColumnLayout {
                                width: parent.width - (Metrics.md * 2)
                                anchors.horizontalCenter: parent.horizontalCenter
                                anchors.margins: Metrics.sm
                                spacing: Metrics.xs

                                RowLayout {
                                    Layout.fillWidth: true

                                    Text {
                                        Layout.fillWidth: true
                                        text: root.selectedAction ? (root.selectedAction.name || "") : ""
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.bodySmall
                                        font.weight: Typography.weightMedium
                                        color: Colors.textPrimary
                                    }

                                    Rectangle {
                                        height: 20
                                        radius: Metrics.radiusFull
                                        color: Colors.primary100
                                        width: modeBadgeText.implicitWidth + 16

                                        Text {
                                            id: modeBadgeText
                                            anchors.centerIn: parent
                                            text: root.selectedAction ? getInputModeText(root.selectedAction.input_mode) : ""
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 10
                                            color: Colors.primary700
                                        }
                                    }
                                }

                                Text {
                                    width: parent.width
                                    text: root.selectedAction ? (root.selectedAction.description || "") : ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.textSecondary
                                    wrapMode: Text.Wrap
                                }

                                RowLayout {
                                    spacing: Metrics.xs

                                    Rectangle {
                                        height: 20
                                        radius: Metrics.radiusFull
                                        color: Colors.bgPrimary
                                        border.color: Colors.borderLight
                                        border.width: 1
                                        width: responseLengthBadge.implicitWidth + 16

                                        Text {
                                            id: responseLengthBadge
                                            anchors.centerIn: parent
                                            text: "응답 " + getResponseLengthText(root.selectedAction ? root.selectedAction.response_length : "medium")
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 10
                                            color: Colors.textSecondary
                                        }
                                    }

                                    Rectangle {
                                        height: 20
                                        radius: Metrics.radiusFull
                                        color: Colors.bgPrimary
                                        border.color: Colors.borderLight
                                        border.width: 1
                                        width: ragBadge.implicitWidth + 16

                                        Text {
                                            id: ragBadge
                                            anchors.centerIn: parent
                                            text: root.selectedAction && root.selectedAction.use_rag ? "문서 검색 사용" : "문서 검색 안 함"
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 10
                                            color: Colors.textSecondary
                                        }
                                    }
                                }

                                Text {
                                    text: "연결 프롬프트: " + (root.selectedAction && root.selectedAction.current_prompt && root.selectedAction.current_prompt.title ? root.selectedAction.current_prompt.title : "기본 프롬프트")
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: 10
                                    color: Colors.textTertiary
                                }
                            }
                        }

                        TextField {
                            id: actionInput
                            width: parent.width
                            placeholderText: root.selectedAction ? getInputModePlaceholder(root.selectedAction.input_mode) : "AI 기능을 선택하세요"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            enabled: canUseAI() && !root.aiRunning
                        }

                        RowLayout {
                            width: parent.width
                            spacing: Metrics.sm

                            Button {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                text: root.aiRunning ? "중지" : "실행"
                                enabled: canUseAI() && root.selectedAction && root.selectedAction.action_id
                                contentItem: Text {
                                    text: parent.text
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    font.weight: Typography.weightMedium
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    color: parent.enabled ? Colors.white : Colors.textTertiary
                                }
                                background: Rectangle {
                                    color: parent.enabled ? Colors.primary500 : Colors.bgTertiary
                                    radius: Metrics.radiusSm
                                }
                                onClicked: {
                                    if (root.aiRunning) {
                                        var ac = getAssistantController()
                                        if (ac) {
                                            ac.cancel()
                                            root.responseText += "\n[안내] 작업을 취소했습니다."
                                        }
                                    } else {
                                        runSelectedAction()
                                    }
                                }
                            }
                        }

                        Rectangle {
                            width: parent.width
                            height: 1
                            color: Colors.borderLight
                        }

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

    Item {
        anchors.fill: parent
        visible: root.aiRunning
        z: 999

        Rectangle {
            anchors.fill: parent
            color: Colors.bgPrimary
            opacity: 0.92
        }

        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }

        Column {
            anchors.centerIn: parent
            width: Math.min(root.width * 0.8, 360)
            spacing: Metrics.sm

            BusyIndicator {
                running: true
                width: 48
                height: 48
            }

            Text {
                text: "AI 작업 실행 중"
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.bodyLarge
                font.weight: Typography.weightSemibold
                color: Colors.textPrimary
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
            }

            Text {
                text: "작업이 완료될 때까지 다른 조작은 잠시 중단됩니다."
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.caption
                color: Colors.textSecondary
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                width: parent.width
            }

            Button {
                text: "작업 중지"
                width: 160
                Layout.alignment: Qt.AlignHCenter
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
                }
                onClicked: {
                    var ac = getAssistantController()
                    if (ac) ac.cancel()
                }
            }
        }
    }
}

