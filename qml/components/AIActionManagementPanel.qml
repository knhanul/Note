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
    property var promptDocumentList: promptDocumentControllerObj ? promptDocumentControllerObj.promptDocumentList : []
    property var currentAction: aiActionControllerObj ? aiActionControllerObj.currentAction : ({})

    property bool isNewMode: false
    property bool isEditMode: false
    property bool showDeleteConfirm: false
    property bool showAdvancedNew: false
    property bool showAdvancedEdit: false
    property string statusMessage: ""
    property bool isFormMode: isNewMode || isEditMode
    property bool isActionEditorOpen: isFormMode
    property int actionEditorPanelWidth: Math.max(560, Math.min(width - Metrics.lg * 2, 980))
    property bool actionEditorWideLayout: actionEditorPanelWidth >= 600
    readonly property string actionEditorMode: isNewMode ? "create" : "edit"
    readonly property string actionEditorTitle: actionEditorMode === "create" ? "새 AI 기능 등록" : "AI 기능 수정"
    readonly property string actionEditorDescription: actionEditorMode === "create"
                                                     ? "새 AI 기능의 이름, 설명, 프롬프트 연결 방식을 설정합니다."
                                                     : "선택한 AI 기능의 이름, 설명, 프롬프트 연결 방식을 수정합니다."
    readonly property string confirmButtonText: actionEditorMode === "create" ? "등록" : "저장"
    property string selectedPromptPreview: ""

    property var defaultCategoryOptions: ["문서 작업", "문서 질문", "요약/정리", "번역", "코드/수식", "기타"]
    property var categoryOptions: loadCategories()

    function loadCategories() {
        var ss = typeof settingsService !== "undefined" && settingsService !== null ? settingsService : null
        if (!ss) return root.defaultCategoryOptions
        try {
            var raw = ss.get_value("ai_category_list", "")
            if (raw) {
                var parsed = JSON.parse(raw)
                if (Array.isArray(parsed) && parsed.length > 0) return parsed
            }
        } catch (e) {}
        return root.defaultCategoryOptions
    }

    function reloadCategories() {
        root.categoryOptions = loadCategories()
    }
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
        // Properties are kept in sync via QML expression bindings automatically.
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
        root.selectedPromptPreview = ""

        actionFormName.text = ""
        actionFormDescription.text = ""
        actionFormCategory.currentIndex = 0
        actionFormResponseLength.currentIndex = 1
        actionFormPromptBinding.currentIndex = -1
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

        var name = actionFormName.text.trim()
        if (!name) {
            root.statusMessage = "기능 이름은 필수입니다."
            return
        }

        var actionId = c.generate_action_id(name)

        var description = actionFormDescription.text.trim()
        var category = actionFormCategory.currentText || "문서 작업"
        var inputMode = "auto"
        var useRag = false
        var responseLength = root.selectedResponseLength(actionFormResponseLength)
        var enabled = true
        var requiredVars = "[]"

        var result = c.create_action(name, actionId, description, category, inputMode, useRag, requiredVars, enabled, responseLength)
        if (result && result.action_id) {
            var promptDoc = root.selectedPromptFromCombo(actionFormPromptBinding)
            if (promptDoc)
                c.set_binding(result.action_id, promptDoc.prompt_doc_id)
            selectAction(result.action_id)
            root.isNewMode = false
            root.statusMessage = "'" + name + "' 기능을 만들었습니다."
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

        actionFormName.text = root.currentAction.name || ""
        actionFormDescription.text = root.currentAction.description || ""

        var categoryIndex = root.categoryOptions.indexOf(root.currentAction.category || "문서 작업")
        actionFormCategory.currentIndex = categoryIndex >= 0 ? categoryIndex : 0
        actionFormResponseLength.currentIndex = root.responseLengthIndex(root.currentAction.response_length || "medium")
        actionFormPromptBinding.currentIndex = root.indexOfPromptDocId(root.currentAction.binding_prompt_doc_id || "")

        // Update prompt preview
        if (actionFormPromptBinding.currentIndex >= 0 && actionFormPromptBinding.currentIndex < root.promptDocumentList.length) {
            var selectedPrompt = root.promptDocumentList[actionFormPromptBinding.currentIndex]
            root.selectedPromptPreview = selectedPrompt.content_md || "(프롬프트 내용이 없습니다)"
        } else {
            root.selectedPromptPreview = ""
        }
    }

    function saveCurrentAction() {
        var c = getActionController()
        var action = root.currentAction
        if (!c || !action || !action.action_id) return

        var name = actionFormName.text.trim()
        if (!name) {
            root.statusMessage = "기능 이름은 필수입니다."
            return
        }

        var description = actionFormDescription.text.trim()
        var category = actionFormCategory.currentText || "문서 작업"
        var inputMode = "auto"
        var useRag = false
        var responseLength = root.selectedResponseLength(actionFormResponseLength)
        var enabled = true
        var requiredVars = root.currentAction.required_variables_json || "[]"

        var result = c.update_action(action.action_id, name, description, category, inputMode, useRag, requiredVars, enabled, responseLength)
        if (result && result.action_id) {
            var promptDoc = root.selectedPromptFromCombo(actionFormPromptBinding)
            if (promptDoc)
                c.set_binding(action.action_id, promptDoc.prompt_doc_id)
            selectAction(action.action_id)
            root.isEditMode = false
            root.statusMessage = "변경 내용을 저장했습니다."
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
                        visible: !!(root.currentAction && root.currentAction.action_id)

                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: titleSection.implicitHeight + Metrics.md * 2
                            radius: Metrics.radiusMd
                            color: Colors.bgSecondary
                            border.color: Colors.borderLight
                            border.width: 1

                            RowLayout {
                                id: titleSection
                                anchors.fill: parent
                                anchors.margins: Metrics.md
                                spacing: Metrics.sm

                                Text {
                                    Layout.fillWidth: true
                                    text: root.currentAction ? (root.currentAction.name || "") : ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.h6
                                    font.weight: Typography.weightSemibold
                                    color: Colors.textPrimary
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
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: detailInfoSection.implicitHeight + Metrics.md * 2
                            radius: Metrics.radiusMd
                            color: Colors.bgSecondary
                            border.color: Colors.borderLight
                            border.width: 1

                            ColumnLayout {
                                id: detailInfoSection
                                anchors.fill: parent
                                anchors.margins: Metrics.md
                                spacing: Metrics.sm

                                Text {
                                    Layout.fillWidth: true
                                    text: root.currentAction ? (root.currentAction.description || "설명이 없습니다.") : ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textSecondary
                                    wrapMode: Text.Wrap
                                }

                                Rectangle { Layout.fillWidth: true; height: 1; color: Colors.borderLight }

                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: 2
                                    columnSpacing: Metrics.md
                                    rowSpacing: Metrics.sm

                                    Text { text: "카테고리"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                                    Text { text: root.currentAction ? (root.currentAction.category || "문서 작업") : ""; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textPrimary }

                                    Text { text: "응답 길이"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                                    Text { text: root.getResponseLengthLabel(root.currentAction ? root.currentAction.response_length : "medium"); font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textPrimary }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            radius: Metrics.radiusMd
                            color: Colors.bgSecondary
                            border.color: Colors.borderLight
                            border.width: 1

                            ColumnLayout {
                                id: promptSection
                                anchors.fill: parent
                                anchors.margins: Metrics.md
                                spacing: Metrics.xs

                                Text {
                                    Layout.fillWidth: true
                                    text: "연결 프롬프트"
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    font.weight: Typography.weightMedium
                                    color: Colors.textSecondary
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: root.promptTitle(root.currentPromptInfo())
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    font.weight: Typography.weightMedium
                                    color: Colors.textPrimary
                                    wrapMode: Text.Wrap
                                }

                                Rectangle { Layout.fillWidth: true; height: 1; color: Colors.borderLight }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    radius: Metrics.radiusSm
                                    color: Colors.bgPrimary
                                    border.color: Colors.borderLight
                                    border.width: 1

                                    ScrollView {
                                        anchors.fill: parent
                                        anchors.margins: Metrics.sm
                                        clip: true
                                        ScrollBar.vertical.policy: ScrollBar.AsNeeded

                                        Text {
                                            width: parent.width
                                            text: root.currentPromptInfo() ? (root.currentPromptInfo().content_md || "내용이 없습니다.") : "연결된 프롬프트가 없습니다."
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: Typography.caption
                                            color: Colors.textPrimary
                                            wrapMode: Text.Wrap
                                            textFormat: Text.PlainText
                                            verticalAlignment: Text.AlignTop
                                        }
                                    }
                                }
                            }
                        }
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
        color: Qt.rgba(0, 0, 0, 0.08)
        visible: root.isFormMode
        z: 10

        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }

        Rectangle {
            id: actionEditorCard
            anchors.centerIn: parent
            width: root.actionEditorPanelWidth
            height: parent.height - Metrics.lg * 2
            radius: Metrics.radiusLg
            color: Colors.bgPrimary
            border.color: Colors.primary200
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Metrics.lg
                spacing: Metrics.md

                Rectangle {
                    Layout.fillWidth: true
                    radius: Metrics.radiusMd
                    color: Colors.bgSecondary
                    border.color: Colors.borderLight
                    border.width: 1
                    implicitHeight: editorTitleLayout.implicitHeight + Metrics.md * 2

                    ColumnLayout {
                        id: editorTitleLayout
                        anchors.fill: parent
                        anchors.margins: Metrics.md
                        spacing: Metrics.xs

                        Text {
                            Layout.fillWidth: true
                            text: root.actionEditorTitle
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.h6
                            font.weight: Typography.weightSemibold
                            color: Colors.textPrimary
                        }

                        Text {
                            Layout.fillWidth: true
                            text: root.actionEditorDescription
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            color: Colors.textSecondary
                            wrapMode: Text.Wrap
                        }
                    }
                }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    ScrollBar.vertical.policy: ScrollBar.AsNeeded

                    GridLayout {
                        width: actionEditorCard.width - Metrics.lg * 2
                        columns: root.actionEditorWideLayout ? 2 : 1
                        columnSpacing: Metrics.lg
                        rowSpacing: Metrics.md

                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignTop
                            spacing: Metrics.sm

                            Text { text: "기능 이름"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                            TextField {
                                id: actionFormName
                                Layout.fillWidth: true
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                selectByMouse: true
                                placeholderText: "예: 회의록 요약, 문서 문장 다듬기"
                            }

                            Text { text: "설명"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                            TextArea {
                                id: actionFormDescription
                                Layout.fillWidth: true
                                Layout.preferredHeight: 56
                                wrapMode: TextEdit.Wrap
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                selectByMouse: true
                                placeholderText: "이 기능이 어떤 상황에서 어떤 답변을 해주면 좋은지 적어주세요."
                                background: Rectangle {
                                    color: Colors.bgPrimary
                                    radius: Metrics.radiusMd
                                    border.color: Colors.borderLight
                                    border.width: 1
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.xs

                                Text { text: "연결 프롬프트"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                                ComboBox {
                                    id: actionFormPromptBinding
                                    Layout.fillWidth: true
                                    model: root.promptDocumentList
                                    textRole: "title"
                                    currentIndex: -1
                                    onCurrentIndexChanged: {
                                        if (currentIndex >= 0 && currentIndex < root.promptDocumentList.length) {
                                            var selectedPrompt = root.promptDocumentList[currentIndex]
                                            root.selectedPromptPreview = selectedPrompt.content_md || "(프롬프트 내용이 없습니다)"
                                        } else {
                                            root.selectedPromptPreview = ""
                                        }
                                    }
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.md

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: Metrics.xs

                                    Text { text: "카테고리"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                                    ComboBox {
                                        id: actionFormCategory
                                        Layout.fillWidth: true
                                        model: root.categoryOptions
                                        currentIndex: 0
                                    }
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.xs

                                Text { text: "응답 길이"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                                ComboBox {
                                    id: actionFormResponseLength
                                    Layout.fillWidth: true
                                    model: root.responseLengthOptions
                                    textRole: "label"
                                    valueRole: "value"
                                    currentIndex: 1
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: root.getResponseLengthDescription(root.selectedResponseLength(actionFormResponseLength))
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.textTertiary
                                    wrapMode: Text.Wrap
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.minimumWidth: 280
                            Layout.preferredWidth: 320
                            Layout.alignment: Qt.AlignTop
                            spacing: Metrics.xs

                            Text {
                                text: "프롬프트 미리보기"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.textSecondary
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: Metrics.radiusMd
                                color: Colors.bgSecondary
                                border.color: Colors.borderLight
                                border.width: 1

                                ScrollView {
                                    anchors.fill: parent
                                    anchors.margins: Metrics.sm
                                    clip: true
                                    ScrollBar.vertical.policy: ScrollBar.AsNeeded

                                    Text {
                                        width: parent.width
                                        text: root.selectedPromptPreview || "프롬프트를 선택하면 미리보기가 표시됩니다."
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        color: root.selectedPromptPreview ? Colors.textPrimary : Colors.textTertiary
                                        wrapMode: Text.Wrap
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 58
                    radius: Metrics.radiusMd
                    color: Colors.bgSecondary
                    border.color: Colors.borderLight
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: Metrics.sm
                        spacing: Metrics.sm

                        Item { Layout.fillWidth: true }

                        Button {
                            Layout.preferredWidth: 116
                            Layout.preferredHeight: 38
                            text: "취소"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            flat: true
                            onClicked: root.cancelEdit()
                        }

                        Button {
                            id: saveButton
                            Layout.preferredWidth: 132
                            Layout.preferredHeight: 38
                            text: root.confirmButtonText
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            font.weight: Typography.weightMedium
                            flat: true
                            palette.button: Colors.primary500
                            palette.buttonText: Colors.white
                            onClicked: {
                                console.log("[AIActionManagementPanel] Save button clicked, isNewMode:", root.isNewMode)
                                if (root.isNewMode) {
                                    root.saveNewAction()
                                } else {
                                    root.saveCurrentAction()
                                }
                            }
                        }
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
