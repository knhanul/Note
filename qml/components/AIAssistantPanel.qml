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

    property bool showSettings: false
    property string responseText: ""

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

                    Text {
                        text: "AI 업무비서"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.bodyLarge
                        font.bold: true
                        color: Colors.textPrimary
                    }

                    Text {
                        text: "로컬 Ollama 기반 문서 도우미"
                        wrapMode: Text.WordWrap
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.caption
                        color: Colors.textSecondary
                    }

                    Flow {
                        width: parent.width
                        spacing: Metrics.xs

                        Rectangle {
                            height: 28
                            radius: Metrics.radiusFull
                            color: Colors.bgSecondary
                            border.color: safeGet("isConnected", false) ? Colors.success : Colors.borderLight
                            border.width: 1
                            Row {
                                anchors.centerIn: parent
                                spacing: Metrics.xs

                                Rectangle {
                                    width: 8
                                    height: 8
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
                            height: 28
                            radius: Metrics.radiusFull
                            color: Colors.bgSecondary
                            border.color: Colors.borderLight
                            border.width: 1
                            Row {
                                anchors.centerIn: parent
                                spacing: Metrics.xs
                                Text {
                                    text: safeGet("chatModel", "모델 미선택")
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

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.sm

                        Button {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 40
                            text: "연결 확인"
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
                                if (typeof aiAssistantController !== "undefined") {
                                    aiAssistantController.check_connection()
                                }
                            }
                        }

                        Button {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 40
                            text: root.showSettings ? "설정 닫기" : "모델 설정"
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
                            }
                            onClicked: root.showSettings = !root.showSettings
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
                    visible: root.showSettings
                    width: parent.width
                    radius: Metrics.radiusLg
                    color: Colors.bgSecondary
                    border.color: Colors.borderLight

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Metrics.md
                        spacing: Metrics.sm

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.xs

                            Text {
                                text: "생성 모델"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            ComboBox {
                                Layout.fillWidth: true
                                model: safeGet("modelList", [])
                                currentIndex: safeGet("modelList", []).indexOf(safeGet("chatModel", ""))
                                onCurrentIndexChanged: {
                                    var list = safeGet("modelList", [])
                                    if (currentIndex >= 0 && currentIndex < list.length) {
                                        var c = getController()
                                        if (c) c.setChatModel(list[currentIndex])
                                    }
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.xs

                            Text {
                                text: "임베딩 모델"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            ComboBox {
                                Layout.fillWidth: true
                                model: safeGet("modelList", [])
                                currentIndex: safeGet("modelList", []).indexOf(safeGet("embeddingModel", ""))
                                onCurrentIndexChanged: {
                                    var list = safeGet("modelList", [])
                                    if (currentIndex >= 0 && currentIndex < list.length) {
                                        var c = getController()
                                        if (c) c.setEmbeddingModel(list[currentIndex])
                                    }
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.xs

                            Text {
                                text: "성능 모드"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.sm

                                Repeater {
                                    model: [
                                        { label: "저사양", value: "low" },
                                        { label: "일반", value: "normal" },
                                        { label: "고성능", value: "high" }
                                    ]

                                    delegate: Button {
                                        Layout.fillWidth: true
                                        text: modelData.label
                                        checkable: true
                                        checked: safeGet("performanceMode", "low") === modelData.value
                                        onClicked: {
                                            var c = getController()
                                            if (c) c.setPerformanceMode(modelData.value)
                                        }
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

                    Column {
                        width: parent.width
                        spacing: Metrics.sm
                        anchors.margins: Metrics.md

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
                                enabled: canUseAI() && !safeAssistantGet("isRunning", false) && typeof window !== "undefined" && window.currentNote && window.currentNote.content
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
                                text: safeAssistantGet("isRunning", false) ? "중지" : "선택 문장 다듬기"
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
                                    if (safeAssistantGet("isRunning", false)) {
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
                                enabled: canUseAI() && !safeAssistantGet("isRunning", false) && typeof window !== "undefined" && window.currentNote && window.currentNote.content
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
                                enabled: canUseAI() && !safeAssistantGet("isRunning", false) && typeof window !== "undefined" && window.currentNote && window.currentNote.content
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

                    Column {
                        width: parent.width
                        spacing: Metrics.sm
                        anchors.margins: Metrics.md

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
                            enabled: canUseAI() && !safeAssistantGet("isRunning", false) && typeof window !== "undefined" && window.currentNote && window.currentNote.content
                        }

                        Button {
                            width: parent.width
                            Layout.preferredHeight: 40
                            text: "질문하기"
                            enabled: questionInput.text !== "" && canUseAI() && !safeAssistantGet("isRunning", false) && typeof window !== "undefined" && window.currentNote && window.currentNote.content
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

                    ColumnLayout {
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

