import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import theme

Rectangle {
    id: root
    color: Colors.bgSecondary
    radius: Metrics.radiusLg
    border.color: Colors.borderLight
    border.width: 1

    property var aiActionControllerObj: typeof aiActionController !== "undefined" && aiActionController !== null ? aiActionController : null
    property var promptControllerObj: typeof promptController !== "undefined" && promptController !== null ? promptController : null
    property var promptDocumentControllerObj: typeof promptDocumentController !== "undefined" && promptDocumentController !== null ? promptDocumentController : null

    property var actionList: aiActionControllerObj ? aiActionControllerObj.actionList : []
    property var promptDocumentList: promptControllerObj ? promptControllerObj.promptDocumentList : []
    property var currentAction: aiActionControllerObj ? aiActionControllerObj.currentAction : ({})

    property bool isNewMode: false
    property bool isEditMode: false
    property bool showDeleteConfirm: false
    property bool showAdvancedNew: false
    property bool showAdvancedEdit: false
    property string statusMessage: ""

    property var categoryOptions: ["문서 작업", "문서 질문", "요약/정리", "번역", "코드/수식", "기타"]
    property var inputModeOptions: [
        { "value": "auto", "label": "자동 감지", "description": "프롬프트 내용에 맞춰 입력 방식을 자동으로 판단합니다." },
        { "value": "note_required", "label": "현재 문서 기반", "description": "현재 열려 있는 문서를 기준으로 AI 기능을 실행합니다." },
        { "value": "chat_only", "label": "채팅만 사용", "description": "문서 없이 질문이나 요청만 입력해서 실행합니다." },
        { "value": "note_and_chat", "label": "문서 + 질문", "description": "현재 문서를 참고하고, 추가 질문도 함께 전달합니다." },
        { "value": "selection_required", "label": "선택 문장 기반", "description": "문서에서 선택한 문장만 대상으로 실행합니다." }
    ]
    property var responseLengthOptions: [
        { "value": "short", "label": "짧게", "description": "핵심만 빠르게 답변합니다." },
        { "value": "medium", "label": "보통", "description": "일반적인 업무용 답변 길이입니다." },
        { "value": "long", "label": "자세히", "description": "맥락과 설명을 더 충분히 제공합니다." }
    ]

    function getActionController() {
        return aiActionControllerObj
    }

    function getPromptController() {
        return promptControllerObj
    }

    function getPromptDocumentController() {
        return promptDocumentControllerObj
    }

    function findPromptById(promptDocId) {
        if (!promptDocId || !root.promptDocumentList)
            return null
        for (var i = 0; i < root.promptDocumentList.length; i++) {
            if (root.promptDocumentList[i].prompt_doc_id === promptDocId)
                return root.promptDocumentList[i]
        }
        return null
    }

    function indexOfPromptDocId(promptDocId) {
        if (!promptDocId || !root.promptDocumentList)
            return -1
        for (var i = 0; i < root.promptDocumentList.length; i++) {
            if (root.promptDocumentList[i].prompt_doc_id === promptDocId)
                return i
        }
        return -1
    }

    function selectedPromptFromCombo(combo) {
        if (!combo || combo.currentIndex < 0 || combo.currentIndex >= root.promptDocumentList.length)
            return null
        return root.promptDocumentList[combo.currentIndex]
    }

    function promptTitle(doc) {
        return doc ? (doc.title || doc.prompt_doc_id || "") : "선택 안 됨"
    }

    function promptTypeLabel(doc) {
        if (!doc)
            return "선택 안 됨"
        return (doc.source_type === "default" || doc.readonly) ? "기본 프롬프트" : "사용자 프롬프트"
    }

    function promptTypeDescription(doc) {
        if (!doc)
            return "아직 연결된 프롬프트가 없습니다."
        if (doc.source_type === "default" || doc.readonly)
            return "기본 제공 프롬프트입니다. 본문 편집은 메인 에디터에서 진행합니다."
        return "사용자가 만든 프롬프트입니다. 본문 편집은 메인 에디터에서 진행합니다."
    }

    function getInputModeLabel(mode) {
        for (var i = 0; i < root.inputModeOptions.length; i++) {
            if (root.inputModeOptions[i].value === mode)
                return root.inputModeOptions[i].label
        }
        return "자동 감지"
    }

    function getInputModeDescription(mode) {
        for (var i = 0; i < root.inputModeOptions.length; i++) {
            if (root.inputModeOptions[i].value === mode)
                return root.inputModeOptions[i].description
        }
        return root.inputModeOptions[0].description
    }

    function inputModeIndex(mode) {
        for (var i = 0; i < root.inputModeOptions.length; i++) {
            if (root.inputModeOptions[i].value === mode)
                return i
        }
        return 0
    }

    function getResponseLengthLabel(value) {
        for (var i = 0; i < root.responseLengthOptions.length; i++) {
            if (root.responseLengthOptions[i].value === value)
                return root.responseLengthOptions[i].label
        }
        return "보통"
    }

    function getResponseLengthDescription(value) {
        for (var i = 0; i < root.responseLengthOptions.length; i++) {
            if (root.responseLengthOptions[i].value === value)
                return root.responseLengthOptions[i].description
        }
        return root.responseLengthOptions[1].description
    }

    function responseLengthIndex(value) {
        for (var i = 0; i < root.responseLengthOptions.length; i++) {
            if (root.responseLengthOptions[i].value === value)
                return i
        }
        return 1
    }

    function selectedResponseLength(combo) {
        if (!combo || combo.currentIndex < 0 || combo.currentIndex >= root.responseLengthOptions.length)
            return "medium"
        return root.responseLengthOptions[combo.currentIndex].value
    }

    function currentPromptInfo() {
        return findPromptById(root.currentAction ? root.currentAction.binding_prompt_doc_id : "")
    }

    function selectAction(actionId) {
        var ac = getActionController()
        if (!ac || !actionId)
            return

        ac.load_action(actionId)
        root.isNewMode = false
        root.isEditMode = false
    }

    function refreshFromController() {
        // Properties are kept in sync via bindings and controller signals.
    }

    function bindSelectedPrompt(actionId, promptDocId) {
        var ac = getActionController()
        if (!ac || !actionId || !promptDocId)
            return false
        return ac.set_binding(actionId, promptDocId)
    }

    function startNewAction() {
        root.isNewMode = true
        root.isEditMode = false
        root.showAdvancedNew = false
        root.statusMessage = "업무용 AI 기능 정보를 입력하세요."

        newActionName.text = ""
        newActionDescription.text = ""
        newActionCategory.currentIndex = 0
        newActionInputMode.currentIndex = 0
        newActionUseRag.checked = false
        newActionResponseLength.currentIndex = 1
        newActionEnabled.checked = true
        newActionPromptBinding.currentIndex = -1
        newActionRequiredVars.text = "[]"
    }

    function cancelEdit() {
        root.isNewMode = false
        root.isEditMode = false
        root.showAdvancedNew = false
        root.showAdvancedEdit = false
        root.statusMessage = ""
    }

    function openPromptEditor(promptDocId) {
        var c = getPromptController()
        if (!c || !promptDocId)
            return
        c.requestOpenPromptDocument(promptDocId)
    }

    function createAndOpenPrompt() {
        var docController = getPromptDocumentController()
        var promptCtrl = getPromptController()
        if (!docController || !promptCtrl) {
            root.statusMessage = "프롬프트 편집 기능을 사용할 수 없습니다."
            return
        }

        var created = docController.createPromptDocument("새 AI 프롬프트", "", "")
        if (created && created.prompt_doc_id) {
            promptCtrl.refresh()
            promptCtrl.requestOpenPromptDocument(created.prompt_doc_id)
            root.statusMessage = "새 프롬프트를 열었습니다."
        } else {
            root.statusMessage = "새 프롬프트 생성에 실패했습니다."
        }
    }

    function saveNewAction() {
        var c = getActionController()
        if (!c) return

        var name = newActionName.text.trim()
        if (!name) {
            root.statusMessage = "기능 이름은 필수입니다."
            return
        }

        var actionId = c.generate_action_id(name)

        var description = newActionDescription.text.trim()
        var category = newActionCategory.currentText || "문서 작업"
        var inputMode = newActionInputMode.currentValue || "auto"
        var useRag = newActionUseRag.checked
        var responseLength = root.selectedResponseLength(newActionResponseLength)
        var enabled = newActionEnabled.checked
        var requiredVars = newActionRequiredVars.text.trim() || "[]"

        var result = c.create_action(name, actionId, description, category, inputMode, useRag, requiredVars, enabled, responseLength)
        if (result && result.action_id) {
            var promptDoc = root.selectedPromptFromCombo(newActionPromptBinding)
            if (promptDoc)
                c.set_binding(result.action_id, promptDoc.prompt_doc_id)
            root.isNewMode = false
            root.statusMessage = "'" + name + "' 기능을 만들었습니다."
            selectAction(result.action_id)
        } else {
            root.statusMessage = "기능 생성에 실패했습니다."
        }
    }

    function startEditAction() {
        if (!root.currentAction || !root.currentAction.action_id)
            return
        root.isNewMode = false
        root.isEditMode = true
        root.showAdvancedEdit = false
        root.syncEditFields()
    }

    function syncEditFields() {
        if (!root.currentAction || !root.currentAction.action_id)
            return

        editName.text = root.currentAction.name || ""
        editDescription.text = root.currentAction.description || ""

        var categoryIndex = root.categoryOptions.indexOf(root.currentAction.category || "문서 작업")
        editCategory.currentIndex = categoryIndex >= 0 ? categoryIndex : 0
        editInputMode.currentIndex = root.inputModeIndex(root.currentAction.input_mode || "auto")
        editUseRag.checked = !!root.currentAction.use_rag
        editResponseLength.currentIndex = root.responseLengthIndex(root.currentAction.response_length || "medium")
        editEnabled.checked = root.currentAction.enabled === undefined ? true : !!root.currentAction.enabled
        editActionPromptBinding.currentIndex = root.indexOfPromptDocId(root.currentAction.binding_prompt_doc_id || "")
        editRequiredVars.text = root.currentAction.required_variables_json || "[]"
    }

    function saveCurrentAction() {
        var c = getActionController()
        var action = root.currentAction
        if (!c || !action || !action.action_id) return

        var name = editName.text.trim()
        if (!name) {
            root.statusMessage = "기능 이름은 필수입니다."
            return
        }

        var description = editDescription.text.trim()
        var category = editCategory.currentText || "문서 작업"
        var inputMode = editInputMode.currentValue || "auto"
        var useRag = editUseRag.checked
        var responseLength = root.selectedResponseLength(editResponseLength)
        var enabled = editEnabled.checked
        var requiredVars = editRequiredVars.text.trim() || "[]"

        var result = c.update_action(action.action_id, name, description, category, inputMode, useRag, requiredVars, enabled, responseLength)
        if (result && result.action_id) {
            var promptDoc = root.selectedPromptFromCombo(editActionPromptBinding)
            if (promptDoc)
                c.set_binding(action.action_id, promptDoc.prompt_doc_id)
            root.isEditMode = false
            root.statusMessage = "변경 내용을 저장했습니다."
            selectAction(action.action_id)
        } else {
            root.statusMessage = "저장에 실패했습니다."
        }
    }

    function deleteCurrentAction() {
        var action = root.currentAction
        if (!action || !action.action_id) {
            root.statusMessage = "삭제할 기능이 없습니다."
            return
        }
        root.showDeleteConfirm = true
    }

    function confirmDelete() {
        var c = getActionController()
        var action = root.currentAction
        if (!c || !action || !action.action_id) return

        var ok = c.archive_action(action.action_id)
        if (ok) {
            root.showDeleteConfirm = false
            root.statusMessage = "AI 기능을 삭제했습니다."
            if (root.actionList && root.actionList.length > 0) {
                selectAction(root.actionList[0].action_id)
            }
        } else {
            root.statusMessage = "삭제에 실패했습니다."
        }
    }

    Component.onCompleted: {
        refreshFromController()
        if (root.actionList && root.actionList.length > 0) {
            selectAction(root.actionList[0].action_id)
        }
    }

    Connections {
        target: aiActionControllerObj
        function onActionsChanged() { root.refreshFromController() }
        function onCurrentActionChanged() {
            root.refreshFromController()
            if (root.isEditMode)
                root.syncEditFields()
        }
        function onInfoMessage(msg) { root.statusMessage = msg }
        function onErrorOccurred(msg) { root.statusMessage = msg }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.md
        spacing: Metrics.sm

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.md

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Metrics.xs

                Text {
                    text: "AI 기능 관리"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.h5
                    font.weight: Typography.weightSemibold
                    color: Colors.textPrimary
                }

                Text {
                    Layout.fillWidth: true
                    text: "일반 사무 업무에 맞는 AI 기능을 쉽게 등록하고, 프롬프트와 연결할 수 있습니다."
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textSecondary
                    wrapMode: Text.Wrap
                }
            }

            Button {
                text: "+ AI 기능 추가"
                Layout.preferredHeight: 34
                contentItem: Text {
                    text: parent.text
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    font.weight: Typography.weightMedium
                    color: Colors.primary700
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    color: parent.hovered ? Colors.primary50 : Colors.bgPrimary
                    radius: Metrics.radiusSm
                    border.color: Colors.primary200
                    border.width: 1
                }
                onClicked: root.startNewAction()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Colors.borderLight
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.md

            Rectangle {
                Layout.preferredWidth: 270
                Layout.fillHeight: true
                color: Colors.bgPrimary
                radius: Metrics.radiusMd
                border.color: Colors.borderLight
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Metrics.sm
                    spacing: Metrics.sm

                    Text {
                        text: "기능 목록"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.bodySmall
                        font.weight: Typography.weightMedium
                        color: Colors.textPrimary
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "실행 중으로 사용할 기능만 AI 패널에 표시됩니다."
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.caption
                        color: Colors.textSecondary
                        wrapMode: Text.Wrap
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: root.actionList
                        clip: true
                        spacing: Metrics.xs

                        delegate: Rectangle {
                            width: ListView.view.width
                            height: 72
                            radius: Metrics.radiusSm
                            color: root.currentAction && root.currentAction.action_id === modelData.action_id ? Colors.primary50 : (itemMouse.containsMouse ? Colors.bgSecondary : "transparent")
                            border.color: root.currentAction && root.currentAction.action_id === modelData.action_id ? Colors.primary200 : "transparent"
                            border.width: 1
                            opacity: modelData.enabled ? 1 : 0.65

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: Metrics.sm
                                spacing: Metrics.xs

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: Metrics.xs

                                    Text {
                                        Layout.fillWidth: true
                                        text: modelData.name || modelData.action_id || ""
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.bodySmall
                                        font.weight: Typography.weightMedium
                                        color: Colors.textPrimary
                                        elide: Text.ElideRight
                                    }

                                    Rectangle {
                                        radius: Metrics.radiusFull
                                        height: 20
                                        width: enabledBadgeText.implicitWidth + 14
                                        color: modelData.enabled ? Colors.success : Colors.bgTertiary

                                        Text {
                                            id: enabledBadgeText
                                            anchors.centerIn: parent
                                            text: modelData.enabled ? "사용 중" : "사용 안 함"
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 10
                                            color: modelData.enabled ? Colors.bgPrimary : Colors.textSecondary
                                        }
                                    }
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.description || "설명이 없습니다."
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.textSecondary
                                    wrapMode: Text.Wrap
                                    maximumLineCount: 2
                                    elide: Text.ElideRight
                                }
                            }

                            MouseArea {
                                id: itemMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: root.selectAction(modelData.action_id)
                            }
                        }

                        ScrollBar.vertical: ScrollBar {
                            policy: ScrollBar.AsNeeded
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Colors.bgPrimary
                radius: Metrics.radiusMd
                border.color: Colors.borderLight
                border.width: 1

                Item {
                    anchors.fill: parent

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Metrics.lg
                        spacing: Metrics.md
                        visible: root.currentAction && root.currentAction.action_id

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.sm

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.xs

                                Text {
                                    text: root.currentAction ? (root.currentAction.name || "") : ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.h6
                                    font.weight: Typography.weightSemibold
                                    color: Colors.textPrimary
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: root.currentAction ? (root.currentAction.description || "설명이 없습니다.") : ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textSecondary
                                    wrapMode: Text.Wrap
                                }
                            }

                            RowLayout {
                                spacing: Metrics.xs

                                Rectangle {
                                    width: 72
                                    height: 30
                                    radius: Metrics.radiusSm
                                    color: editBtnArea.containsMouse ? Colors.bgTertiary : "transparent"
                                    border.color: Colors.borderLight
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: "수정"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        color: Colors.textSecondary
                                    }

                                    MouseArea {
                                        id: editBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.startEditAction()
                                    }
                                }

                                Rectangle {
                                    width: 72
                                    height: 30
                                    radius: Metrics.radiusSm
                                    color: deleteBtnArea.containsMouse ? Colors.error50 : "transparent"
                                    border.color: Colors.error200
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: "삭제"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        color: Colors.error500
                                    }

                                    MouseArea {
                                        id: deleteBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.deleteCurrentAction()
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Colors.borderLight
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            radius: Metrics.radiusMd
                            color: Colors.bgSecondary
                            border.color: Colors.borderLight
                            border.width: 1

                            GridLayout {
                                anchors.fill: parent
                                anchors.margins: Metrics.md
                                columns: 2
                                columnSpacing: Metrics.md
                                rowSpacing: Metrics.sm

                                Text { text: "카테고리"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                                Text { text: root.currentAction ? (root.currentAction.category || "문서 작업") : ""; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textPrimary }

                                Text { text: "입력 방식"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                                Text { text: root.getInputModeLabel(root.currentAction ? root.currentAction.input_mode : "auto"); font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textPrimary }

                                Text { text: "문서 검색"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                                Text { text: root.currentAction && root.currentAction.use_rag ? "사용" : "사용 안 함"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textPrimary }

                                Text { text: "응답 길이"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                                Text { text: root.getResponseLengthLabel(root.currentAction ? root.currentAction.response_length : "medium"); font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textPrimary }

                                Text { text: "사용 여부"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                                Text { text: root.currentAction && root.currentAction.enabled ? "사용 중" : "사용 안 함"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textPrimary }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.sm

                            Text {
                                text: "연결 프롬프트"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textPrimary
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                implicitHeight: currentPromptLayout.implicitHeight + Metrics.md * 2
                                radius: Metrics.radiusMd
                                color: Colors.bgSecondary
                                border.color: Colors.borderLight
                                border.width: 1

                                ColumnLayout {
                                    id: currentPromptLayout
                                    anchors.fill: parent
                                    anchors.margins: Metrics.md
                                    spacing: Metrics.xs

                                    Text {
                                        Layout.fillWidth: true
                                        text: root.promptTitle(root.currentPromptInfo())
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.bodySmall
                                        font.weight: Typography.weightMedium
                                        color: Colors.textPrimary
                                        wrapMode: Text.Wrap
                                    }

                                    Rectangle {
                                        radius: Metrics.radiusFull
                                        height: 22
                                        width: promptTypeText.implicitWidth + 16
                                        color: Colors.primary100

                                        Text {
                                            id: promptTypeText
                                            anchors.centerIn: parent
                                            text: root.promptTypeLabel(root.currentPromptInfo())
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 10
                                            color: Colors.primary700
                                        }
                                    }

                                    Text {
                                        Layout.fillWidth: true
                                        text: root.promptTypeDescription(root.currentPromptInfo())
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        color: Colors.textSecondary
                                        wrapMode: Text.Wrap
                                    }
                                }
                            }
                        }

                        Item { Layout.fillHeight: true }
                    }

                    Column {
                        anchors.centerIn: parent
                        width: Math.min(parent.width * 0.8, 360)
                        spacing: Metrics.sm
                        visible: !root.currentAction || !root.currentAction.action_id

                        Text {
                            width: parent.width
                            text: "등록된 AI 기능이 없습니다."
                            horizontalAlignment: Text.AlignHCenter
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            color: Colors.textSecondary
                        }

                        Text {
                            width: parent.width
                            text: "업무용 AI 기능을 하나 추가하면 이 영역에서 상세 설정을 볼 수 있습니다."
                            horizontalAlignment: Text.AlignHCenter
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: Colors.textTertiary
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 34
            radius: Metrics.radiusSm
            color: Colors.bgSecondary
            border.color: Colors.borderLight
            visible: root.statusMessage !== ""

            Text {
                anchors.centerIn: parent
                text: root.statusMessage
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.caption
                color: Colors.textSecondary
            }

            Timer {
                interval: 5000
                running: root.statusMessage !== ""
                onTriggered: root.statusMessage = ""
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: Colors.bgPrimary
        visible: root.isNewMode
        z: 10

        ScrollView {
            anchors.fill: parent
            anchors.margins: Metrics.lg
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: Metrics.md

                Text {
                    text: "새 AI 기능 등록"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.h6
                    font.weight: Typography.weightSemibold
                    color: Colors.textPrimary
                }

                Text {
                    Layout.fillWidth: true
                    text: "일반 사용자가 이해하기 쉬운 항목만 먼저 입력하면 됩니다. 필요한 경우에만 고급 설정을 펼쳐서 확인하세요."
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textSecondary
                    wrapMode: Text.Wrap
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: Colors.borderLight }

                Text { text: "기능 이름"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                TextField {
                    id: newActionName
                    Layout.fillWidth: true
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    selectByMouse: true
                    placeholderText: "예: 회의록 요약, 문서 문장 다듬기"
                }

                Text { text: "설명"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                TextArea {
                    id: newActionDescription
                    Layout.fillWidth: true
                    Layout.preferredHeight: 88
                    wrapMode: TextEdit.Wrap
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    selectByMouse: true
                    placeholderText: "이 기능이 어떤 상황에서 어떤 답변을 해주면 좋은지 적어주세요."
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.md

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.xs

                        Text { text: "카테고리"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                        ComboBox {
                            id: newActionCategory
                            Layout.fillWidth: true
                            model: root.categoryOptions
                            currentIndex: 0
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.xs

                        Text { text: "입력 모드"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                        ComboBox {
                            id: newActionInputMode
                            Layout.fillWidth: true
                            model: root.inputModeOptions
                            textRole: "label"
                            valueRole: "value"
                            currentIndex: 0
                        }

                        Text {
                            Layout.fillWidth: true
                            text: root.getInputModeDescription(newActionInputMode.currentValue || "auto")
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: Colors.textTertiary
                            wrapMode: Text.Wrap
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.xs

                    Text { text: "응답 길이"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                    ComboBox {
                        id: newActionResponseLength
                        Layout.fillWidth: true
                        model: root.responseLengthOptions
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: 1
                    }

                    Text {
                        Layout.fillWidth: true
                        text: root.getResponseLengthDescription(root.selectedResponseLength(newActionResponseLength))
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.caption
                        color: Colors.textTertiary
                        wrapMode: Text.Wrap
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: newRagLayout.implicitHeight + Metrics.md * 2
                    radius: Metrics.radiusMd
                    color: Colors.bgSecondary
                    border.color: Colors.borderLight
                    border.width: 1

                    ColumnLayout {
                        id: newRagLayout
                        anchors.fill: parent
                        anchors.margins: Metrics.md
                        spacing: Metrics.xs

                        CheckBox {
                            id: newActionUseRag
                            text: "문서 검색 사용"
                            checked: false
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                        }

                        Text {
                            Layout.fillWidth: true
                            text: "현재 문서나 저장된 자료를 참고하여 더 정확한 답변을 생성합니다."
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: Colors.textSecondary
                            wrapMode: Text.Wrap
                        }
                    }
                }

                CheckBox {
                    id: newActionEnabled
                    text: "AI 패널에서 바로 사용할 수 있게 표시"
                    checked: true
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.xs

                    Text { text: "연결 프롬프트"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                    ComboBox {
                        id: newActionPromptBinding
                        Layout.fillWidth: true
                        model: root.promptDocumentList
                        textRole: "title"
                        currentIndex: -1
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: newPromptLayout.implicitHeight + Metrics.sm * 2
                        radius: Metrics.radiusMd
                        color: Colors.bgSecondary
                        border.color: Colors.borderLight
                        border.width: 1
                        visible: root.selectedPromptFromCombo(newActionPromptBinding) !== null

                        ColumnLayout {
                            id: newPromptLayout
                            anchors.fill: parent
                            anchors.margins: Metrics.sm
                            spacing: Metrics.xs

                            Text {
                                Layout.fillWidth: true
                                text: root.promptTitle(root.selectedPromptFromCombo(newActionPromptBinding))
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textPrimary
                            }

                            Text {
                                Layout.fillWidth: true
                                text: root.promptTypeLabel(root.selectedPromptFromCombo(newActionPromptBinding))
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.primary700
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: newAdvancedLayout.implicitHeight + Metrics.md * 2
                    radius: Metrics.radiusMd
                    color: Colors.bgSecondary
                    border.color: Colors.borderLight
                    border.width: 1

                    ColumnLayout {
                        id: newAdvancedLayout
                        anchors.fill: parent
                        anchors.margins: Metrics.md
                        spacing: Metrics.sm

                        RowLayout {
                            Layout.fillWidth: true

                            Text {
                                Layout.fillWidth: true
                                text: "고급 설정"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textPrimary
                            }

                            Button {
                                text: root.showAdvancedNew ? "접기" : "펼치기"
                                contentItem: Text {
                                    text: parent.text
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.textPrimary
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    color: Colors.bgPrimary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                }
                                onClicked: root.showAdvancedNew = !root.showAdvancedNew
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: "일반적으로는 건드릴 필요 없습니다. 변수는 프롬프트 내용을 기준으로 자동 감지됩니다."
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: Colors.textSecondary
                            wrapMode: Text.Wrap
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.xs
                            visible: root.showAdvancedNew

                            Text { text: "필수 변수(JSON)"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                            TextField {
                                id: newActionRequiredVars
                                Layout.fillWidth: true
                                text: "[]"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                selectByMouse: true
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.sm

                    Button {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 38
                        text: "등록"
                        contentItem: Text {
                            text: "등록"
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
                        }
                        onClicked: root.saveNewAction()
                    }

                    Button {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 38
                        text: "취소"
                        contentItem: Text {
                            text: "취소"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            color: Colors.textPrimary
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            color: Colors.bgSecondary
                            radius: Metrics.radiusSm
                            border.color: Colors.borderLight
                        }
                        onClicked: root.cancelEdit()
                    }
                }
            }
        }
    }

    // Edit Action Form
    Rectangle {
        anchors.fill: parent
        color: Colors.bgPrimary
        visible: root.isEditMode
        z: 10

        ScrollView {
            anchors.fill: parent
            anchors.margins: Metrics.lg
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: Metrics.md

                Text {
                    text: "AI 기능 수정"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.h6
                    font.weight: Typography.weightSemibold
                    color: Colors.textPrimary
                }

                Text {
                    Layout.fillWidth: true
                    text: "업무 흐름에 맞게 설명과 입력 방식, 프롬프트 연결을 다듬어 주세요."
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textSecondary
                    wrapMode: Text.Wrap
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: Colors.borderLight }

                Text { text: "기능명"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                TextField {
                    id: editName
                    Layout.fillWidth: true
                    readOnly: true
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    selectByMouse: true
                }

                Text { text: "설명"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                TextArea {
                    id: editDescription
                    Layout.fillWidth: true
                    Layout.preferredHeight: 88
                    wrapMode: TextEdit.Wrap
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    selectByMouse: true
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.md

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.xs

                        Text { text: "카테고리"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                        ComboBox {
                            id: editCategory
                            Layout.fillWidth: true
                            model: root.categoryOptions
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.xs

                        Text { text: "입력 방식"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                        ComboBox {
                            id: editInputMode
                            Layout.fillWidth: true
                            model: root.inputModeOptions
                            textRole: "label"
                            valueRole: "value"
                        }

                        Text {
                            Layout.fillWidth: true
                            text: root.getInputModeDescription(editInputMode.currentValue || "auto")
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: Colors.textTertiary
                            wrapMode: Text.Wrap
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.xs

                    Text { text: "응답 길이"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                    ComboBox {
                        id: editResponseLength
                        Layout.fillWidth: true
                        model: root.responseLengthOptions
                        textRole: "label"
                        valueRole: "value"
                    }

                    Text {
                        Layout.fillWidth: true
                        text: root.getResponseLengthDescription(root.selectedResponseLength(editResponseLength))
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.caption
                        color: Colors.textTertiary
                        wrapMode: Text.Wrap
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: editRagLayout.implicitHeight + Metrics.md * 2
                    radius: Metrics.radiusMd
                    color: Colors.bgSecondary
                    border.color: Colors.borderLight
                    border.width: 1

                    ColumnLayout {
                        id: editRagLayout
                        anchors.fill: parent
                        anchors.margins: Metrics.md
                        spacing: Metrics.xs

                        CheckBox {
                            id: editUseRag
                            text: "문서 검색 사용"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                        }

                        Text {
                            Layout.fillWidth: true
                            text: "현재 문서나 저장된 자료를 참고하여 더 정확한 답변을 생성합니다."
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: Colors.textSecondary
                            wrapMode: Text.Wrap
                        }
                    }
                }

                CheckBox {
                    id: editEnabled
                    text: "AI 패널에서 바로 사용할 수 있게 표시"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.xs

                    Text { text: "연결 프롬프트"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                    ComboBox {
                        id: editActionPromptBinding
                        Layout.fillWidth: true
                        model: root.promptDocumentList
                        textRole: "title"
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: editPromptLayout.implicitHeight + Metrics.sm * 2
                        radius: Metrics.radiusMd
                        color: Colors.bgSecondary
                        border.color: Colors.borderLight
                        border.width: 1
                        visible: root.selectedPromptFromCombo(editActionPromptBinding) !== null

                        ColumnLayout {
                            id: editPromptLayout
                            anchors.fill: parent
                            anchors.margins: Metrics.sm
                            spacing: Metrics.xs

                            Text {
                                Layout.fillWidth: true
                                text: root.promptTitle(root.selectedPromptFromCombo(editActionPromptBinding))
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textPrimary
                            }

                            Text {
                                Layout.fillWidth: true
                                text: root.promptTypeLabel(root.selectedPromptFromCombo(editActionPromptBinding))
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.primary700
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: editAdvancedLayout.implicitHeight + Metrics.md * 2
                    radius: Metrics.radiusMd
                    color: Colors.bgSecondary
                    border.color: Colors.borderLight
                    border.width: 1

                    ColumnLayout {
                        id: editAdvancedLayout
                        anchors.fill: parent
                        anchors.margins: Metrics.md
                        spacing: Metrics.sm

                        RowLayout {
                            Layout.fillWidth: true

                            Text {
                                Layout.fillWidth: true
                                text: "고급 설정"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textPrimary
                            }

                            Button {
                                text: root.showAdvancedEdit ? "접기" : "펼치기"
                                contentItem: Text {
                                    text: parent.text
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.textPrimary
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    color: Colors.bgPrimary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                }
                                onClicked: root.showAdvancedEdit = !root.showAdvancedEdit
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: "일반적으로는 수정하지 않아도 됩니다. 변수는 프롬프트 분석 결과와 함께 자동으로 활용됩니다."
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: Colors.textSecondary
                            wrapMode: Text.Wrap
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.xs
                            visible: root.showAdvancedEdit

                            Text { text: "필수 변수(JSON)"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                            TextField {
                                id: editRequiredVars
                                Layout.fillWidth: true
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                selectByMouse: true
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.sm

                    Button {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 38
                        text: "저장"
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
                        }
                        onClicked: root.saveCurrentAction()
                    }

                    Button {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 38
                        text: "취소"
                        contentItem: Text {
                            text: parent.text
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            color: Colors.textPrimary
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            color: Colors.bgSecondary
                            radius: Metrics.radiusSm
                            border.color: Colors.borderLight
                        }
                        onClicked: root.cancelEdit()
                    }
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#80000000"
        visible: root.showDeleteConfirm
        z: 100

        Rectangle {
            anchors.centerIn: parent
            width: 320
            height: 180
            radius: Metrics.radiusLg
            color: Colors.bgPrimary
            border.color: Colors.borderLight

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Metrics.lg
                spacing: Metrics.md

                Text {
                    Layout.fillWidth: true
                    text: "AI 기능 삭제"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.h6
                    font.weight: Typography.weightSemibold
                    color: Colors.textPrimary
                    horizontalAlignment: Text.AlignHCenter
                }

                Text {
                    Layout.fillWidth: true
                    text: "이 AI 기능을 삭제하면 AI 패널 목록에서 사라집니다.\n기존 프롬프트 문서는 삭제되지 않습니다."
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textSecondary
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.sm

                    Button {
                        Layout.fillWidth: true
                        text: "삭제"
                        contentItem: Text {
                            text: parent.text
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            color: Colors.white
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            color: Colors.error500
                            radius: Metrics.radiusSm
                        }
                        onClicked: root.confirmDelete()
                    }

                    Button {
                        Layout.fillWidth: true
                        text: "취소"
                        contentItem: Text {
                            text: parent.text
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            color: Colors.textPrimary
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            color: Colors.bgSecondary
                            radius: Metrics.radiusSm
                            border.color: Colors.borderLight
                        }
                        onClicked: root.showDeleteConfirm = false
                    }
                }
            }
        }
    }
}
