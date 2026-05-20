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

    // Use direct binding to Python properties; notify signals will trigger updates
    property var actionList: aiActionControllerObj ? aiActionControllerObj.actionList : []
    property var currentAction: aiActionControllerObj ? aiActionControllerObj.currentAction : ({})

    property var promptDocumentList: typeof promptDocumentController !== "undefined" && promptDocumentController !== null ? promptDocumentController.promptDocumentList : []

    property bool isNewMode: false
    property string statusMessage: ""
    property bool showDeleteConfirm: false

    function getController() {
        return aiActionControllerObj
    }

    function selectAction(actionId) {
        var c = getController()
        if (!c || !actionId)
            return
        c.load_action(actionId)
    }

    function formatVariables(variablesJson) {
        if (!variablesJson)
            return "없음"
        try {
            var arr = JSON.parse(variablesJson)
            if (!arr || !arr.length)
                return "없음"
            return arr.map(function(v) { return "{{" + v + "}}" }).join(", ")
        } catch (e) {
            return "없음"
        }
    }

    function promptDocDisplayTitle(doc) {
        if (!doc)
            return ""
        var prefix = doc.readonly ? "[기본] " : "[사용자] "
        return prefix + (doc.title || doc.prompt_doc_id || "")
    }

    function getPromptDocIdFromIndex(index) {
        if (index < 0 || index >= root.promptDocumentList.length)
            return ""
        return root.promptDocumentList[index].prompt_doc_id
    }

    function getPromptDocIndexFromId(promptDocId) {
        if (!promptDocId)
            return -1
        for (var i = 0; i < root.promptDocumentList.length; i++) {
            if (root.promptDocumentList[i].prompt_doc_id === promptDocId)
                return i
        }
        return -1
    }

    function isDefaultAction(action) {
        return action && (action.readonly === true || action.source_type === "default")
    }

    function startNewAction() {
        root.isNewMode = true
        root.statusMessage = "새 기능을 입력하세요"
    }

    function cancelNewAction() {
        root.isNewMode = false
        root.statusMessage = ""
        if (root.actionList && root.actionList.length > 0) {
            selectAction(root.actionList[0].action_id)
        }
    }

    function saveNewAction() {
        var c = getController()
        if (!c)
            return

        var name = newActionName.text.trim()
        if (!name) {
            root.statusMessage = "기능 이름은 필수입니다"
            return
        }

        var actionId = newActionId.text.trim() || c.generate_action_id(name)
        var description = newActionDescription.text.trim()
        var category = newActionCategory.currentText || "user"
        var inputMode = newActionInputMode.currentText || "auto"
        var useRag = newActionUseRag.checked
        var requiredVars = newActionRequiredVars.text.trim() || "[]"

        var result = c.create_action(name, actionId, description, category, inputMode, useRag, requiredVars)
        if (result && result.action_id) {
            root.isNewMode = false
            root.statusMessage = "'" + name + "' 기능이 생성되었습니다"
            selectAction(result.action_id)
        } else {
            root.statusMessage = "기능 생성에 실패했습니다"
        }
    }

    function saveCurrentAction() {
        var c = getController()
        var action = root.currentAction
        if (!c || !action || !action.action_id)
            return

        if (isDefaultAction(action)) {
            root.statusMessage = "기본 기능은 수정할 수 없습니다"
            return
        }

        var name = editName.text.trim()
        if (!name) {
            root.statusMessage = "기능 이름은 필수입니다"
            return
        }

        var description = editDescription.text.trim()
        var category = editCategory.currentText || "user"
        var inputMode = editInputMode.currentText || "auto"
        var useRag = editUseRag.checked
        var requiredVars = editRequiredVars.text.trim() || "[]"

        var result = c.update_action(action.action_id, name, description, category, inputMode, useRag, requiredVars)
        if (result && result.action_id) {
            root.statusMessage = "저장되었습니다"
            selectAction(result.action_id)
        } else {
            root.statusMessage = "저장에 실패했습니다"
        }
    }

    function duplicateCurrentAction() {
        var c = getController()
        var action = root.currentAction
        if (!c || !action || !action.action_id)
            return

        var result = c.duplicate_action(action.action_id)
        if (result && result.action_id) {
            root.statusMessage = "기능이 복사되었습니다"
            selectAction(result.action_id)
        } else {
            root.statusMessage = "복제에 실패했습니다"
        }
    }

    function deleteCurrentAction() {
        var c = getController()
        var action = root.currentAction
        if (!c || !action || !action.action_id)
            return

        if (isDefaultAction(action)) {
            root.statusMessage = "기본 기능은 삭제할 수 없습니다"
            return
        }

        root.showDeleteConfirm = true
    }

    function confirmDelete() {
        var c = getController()
        var action = root.currentAction
        if (!c || !action || !action.action_id)
            return

        var ok = c.archive_action(action.action_id)
        if (ok) {
            root.statusMessage = "삭제되었습니다"
            root.showDeleteConfirm = false
            refreshFromController()
            if (root.actionList && root.actionList.length > 0) {
                selectAction(root.actionList[0].action_id)
            }
        } else {
            root.statusMessage = "삭제에 실패했습니다"
        }
    }

    function moveCurrentActionUp() {
        var c = getController()
        var action = root.currentAction
        if (!c || !action || !action.action_id)
            return

        var ok = c.move_action_up(action.action_id)
        if (ok) {
            root.statusMessage = ""
            refreshFromController()
        }
    }

    function moveCurrentActionDown() {
        var c = getController()
        var action = root.currentAction
        if (!c || !action || !action.action_id)
            return

        var ok = c.move_action_down(action.action_id)
        if (ok) {
            root.statusMessage = ""
            refreshFromController()
        }
    }

    function toggleEnabled() {
        var c = getController()
        var action = root.currentAction
        if (!c || !action || !action.action_id)
            return

        var newEnabled = !action.enabled
        c.set_action_enabled(action.action_id, newEnabled)
        root.statusMessage = newEnabled ? "활성화되었습니다" : "비활성화되었습니다"
        refreshFromController()
    }

    function openBoundPrompt() {
        var action = root.currentAction
        if (!action || !action.binding_prompt_doc_id)
            return

        var pc = typeof promptController !== "undefined" && promptController !== null ? promptController : null
        if (pc && pc.requestOpenPromptDocument) {
            pc.requestOpenPromptDocument(action.binding_prompt_doc_id)
        }
    }

    function saveBinding() {
        var c = getController()
        var action = root.currentAction
        if (!c || !action || !action.action_id)
            return

        var promptIdx = editPromptCombo.currentIndex
        var promptDocId = getPromptDocIdFromIndex(promptIdx)
        if (!promptDocId) {
            root.statusMessage = "프롬프트를 선택하세요"
            return
        }

        var ok = c.set_binding(action.action_id, promptDocId)
        if (ok) {
            root.statusMessage = "프롬프트 연결이 변경되었습니다"
            refreshFromController()
        } else {
            root.statusMessage = "프롬프트 연결에 실패했습니다"
        }
    }

    function createNewPromptAndBind() {
        var pdc = typeof promptDocumentController !== "undefined" && promptDocumentController !== null ? promptDocumentController : null
        var c = getController()
        var action = root.currentAction

        if (!pdc) {
            root.statusMessage = "프롬프트 컨트롤러가 없습니다"
            return
        }

        var newDoc = pdc.createPromptDocument("새 AI 프롬프트", "", "")
        if (newDoc && newDoc.prompt_doc_id && c && action && action.action_id) {
            c.set_binding(action.action_id, newDoc.prompt_doc_id)
            root.statusMessage = "새 프롬프트를 만들고 연결했습니다"
            refreshFromController()
        } else {
            root.statusMessage = "새 프롬프트 생성에 실패했습니다"
        }
    }

    function duplicatePromptAndBind() {
        var pdc = typeof promptDocumentController !== "undefined" && promptDocumentController !== null ? promptDocumentController : null
        var c = getController()
        var action = root.currentAction

        if (!pdc) {
            root.statusMessage = "프롬프트 컨트롤러가 없습니다"
            return
        }

        if (!action || !action.binding_prompt_doc_id) {
            root.statusMessage = "연결된 프롬프트가 없습니다"
            return
        }

        var newDocId = pdc.duplicatePromptDocument(action.binding_prompt_doc_id)
        if (newDocId && c && action && action.action_id) {
            c.set_binding(action.action_id, newDocId)
            root.statusMessage = "프롬프트를 복사해서 연결했습니다"
            refreshFromController()
        } else {
            root.statusMessage = "프롬프트 복제에 실패했습니다"
        }
    }

    function validateCurrentBinding() {
        var c = getController()
        var action = root.currentAction
        if (!c || !action || !action.action_id)
            return {ok: true, missing_required_variables: [], unknown_variables: []}

        var promptDocId = action.binding_prompt_doc_id || action.action_id
        return c.validate_prompt_for_action(action.action_id, promptDocId)
    }

    Component.onCompleted: {
        if (root.actionList && root.actionList.length > 0 && (!root.currentAction || !root.currentAction.action_id)) {
            selectAction(root.actionList[0].action_id)
        }
    }

    Connections {
        target: typeof aiActionController !== "undefined" && aiActionController !== null ? aiActionController : null
        function onActionsChanged() {
            // Python notify signal will refresh the property binding automatically
            if (root.actionList && root.actionList.length > 0 && (!root.currentAction || !root.currentAction.action_id)) {
                root.selectAction(root.actionList[0].action_id)
            }
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
            spacing: Metrics.sm

            Text {
                Layout.fillWidth: true
                text: "AI 기능 관리"
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.h5
                font.weight: Typography.weightSemibold
                color: Colors.textPrimary
            }

            Rectangle {
                height: 32
                radius: Metrics.radiusMd
                color: newBtnArea.containsMouse ? Colors.primary500 : Colors.primary400

                Text {
                    anchors.centerIn: parent
                    text: "+ 새 기능"
                    font.family: Typography.fontPrimary
                    font.weight: Typography.weightMedium
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textInverse
                }

                MouseArea {
                    id: newBtnArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: root.startNewAction()
                }
            }
        }

        Text {
            Layout.fillWidth: true
            text: "AI 기능을 등록, 수정, 삭제하고 프롬프트에 연결합니다."
            font.family: Typography.fontPrimary
            font.pixelSize: Typography.bodySmall
            color: Colors.textSecondary
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
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Colors.bgPrimary
                radius: Metrics.radiusMd
                border.color: Colors.borderLight
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Metrics.sm
                    spacing: Metrics.xs

                    Text {
                        text: "기능 목록"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.bodySmall
                        font.weight: Typography.weightMedium
                        color: Colors.textPrimary
                    }

                    // Empty state for action list
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: !root.actionList || root.actionList.length === 0

                        Text {
                            Layout.fillWidth: true
                            text: "AI 기능이 없습니다"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            color: Colors.textTertiary
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }

                        Button {
                            Layout.alignment: Qt.AlignHCenter
                            text: "새 기능 만들기"
                            onClicked: root.startNewAction()
                        }
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: root.actionList
                        clip: true
                        spacing: 2
                        visible: root.actionList && root.actionList.length > 0

                        delegate: Rectangle {
                            width: ListView.view.width
                            height: 48
                            radius: Metrics.radiusSm
                            color: {
                                if (!modelData.enabled)
                                    return Colors.bgTertiary
                                if (actionMouse.containsMouse)
                                    return Colors.primary50
                                if (root.currentAction && root.currentAction.action_id === modelData.action_id)
                                    return Colors.primary100
                                return "transparent"
                            }
                            opacity: modelData.enabled ? 1.0 : 0.5

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.leftMargin: Metrics.sm
                                anchors.rightMargin: Metrics.sm
                                anchors.verticalCenter: parent.verticalCenter
                                spacing: 2

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

                                    Text {
                                        text: modelData.readonly || modelData.source_type === "default" ? "기본" : ""
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: 10
                                        color: Colors.textTertiary
                                    }
                                }

                                Text {
                                    text: modelData.action_id || ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: 10
                                    color: Colors.textTertiary
                                    elide: Text.ElideRight
                                }
                            }

                            MouseArea {
                                id: actionMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    root.isNewMode = false
                                    root.selectAction(modelData.action_id)
                                }
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

                ScrollView {
                    anchors.fill: parent
                    anchors.margins: Metrics.md
                    clip: true

                    ColumnLayout {
                        width: parent.width
                        spacing: Metrics.md

                        // New Action Form
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.sm
                            visible: root.isNewMode

                            Text {
                                text: "새 기능 만들기"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.h6
                                font.weight: Typography.weightSemibold
                                color: Colors.textPrimary
                            }

                            Text {
                                text: "기능 이름"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            TextField {
                                id: newActionName
                                Layout.fillWidth: true
                                height: 32
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textPrimary
                                background: Rectangle {
                                    color: Colors.bgSecondary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                }
                                onTextChanged: {
                                    var c = getController()
                                    if (c && text.trim()) {
                                        newActionId.text = c.generate_action_id(text.trim())
                                    }
                                }
                            }

                            Text {
                                text: "action_id"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            TextField {
                                id: newActionId
                                Layout.fillWidth: true
                                height: 32
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textPrimary
                                background: Rectangle {
                                    color: Colors.bgSecondary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                }
                            }

                            Text {
                                text: "설명"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            TextField {
                                id: newActionDescription
                                Layout.fillWidth: true
                                height: 32
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textPrimary
                                background: Rectangle {
                                    color: Colors.bgSecondary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                }
                            }

                            Text {
                                text: "카테고리"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            ComboBox {
                                id: newActionCategory
                                Layout.fillWidth: true
                                height: 32
                                model: ["user", "문서 처리", "문서 질문", "기타"]
                                currentIndex: 0
                            }

                            Text {
                                text: "입력 모드"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            ComboBox {
                                id: newActionInputMode
                                Layout.fillWidth: true
                                height: 32
                                model: ["auto", "note_required", "chat_only", "note_and_chat", "selection_required"]
                                currentIndex: 0
                            }

                            RowLayout {
                                Layout.fillWidth: true

                                Text {
                                    text: "RAG 사용"
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textSecondary
                                }

                                CheckBox {
                                    id: newActionUseRag
                                    checked: false
                                }
                            }

                            Text {
                                text: "필수 변수 (JSON 배열)"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            TextField {
                                id: newActionRequiredVars
                                Layout.fillWidth: true
                                height: 32
                                text: "[]"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textPrimary
                                background: Rectangle {
                                    color: Colors.bgSecondary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.sm

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: saveNewBtnArea.containsMouse ? Colors.primary500 : Colors.primary400

                                    Text {
                                        anchors.centerIn: parent
                                        text: "저장"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textInverse
                                    }

                                    MouseArea {
                                        id: saveNewBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.saveNewAction()
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: cancelNewBtnArea.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                                    border.color: Colors.borderLight

                                    Text {
                                        anchors.centerIn: parent
                                        text: "취소"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textSecondary
                                    }

                                    MouseArea {
                                        id: cancelNewBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.cancelNewAction()
                                    }
                                }
                            }
                        }

                        // Edit Action Form
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.sm
                            visible: !root.isNewMode && root.currentAction && root.currentAction.action_id

                            Text {
                                text: root.currentAction ? (root.currentAction.name || root.currentAction.action_id || "") : ""
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.h6
                                font.weight: Typography.weightSemibold
                                color: Colors.textPrimary
                            }

                            Text {
                                text: "action_id: " + (root.currentAction ? root.currentAction.action_id : "")
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.textTertiary
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: Colors.borderLight
                            }

                            Text {
                                text: "기능명"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            TextField {
                                id: editName
                                Layout.fillWidth: true
                                height: 32
                                text: root.currentAction ? root.currentAction.name : ""
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textPrimary
                                readOnly: isDefaultAction(root.currentAction)
                                background: Rectangle {
                                    color: Colors.bgSecondary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                }
                            }

                            Text {
                                text: "설명"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            TextField {
                                id: editDescription
                                Layout.fillWidth: true
                                height: 32
                                text: root.currentAction ? root.currentAction.description : ""
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textPrimary
                                background: Rectangle {
                                    color: Colors.bgSecondary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                }
                            }

                            Text {
                                text: "카테고리"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            ComboBox {
                                id: editCategory
                                Layout.fillWidth: true
                                height: 32
                                model: ["user", "문서 처리", "문서 질문", "기타"]
                                currentIndex: {
                                    var cat = root.currentAction ? root.currentAction.category : "user"
                                    var idx = model.indexOf(cat)
                                    return idx >= 0 ? idx : 0
                                }
                            }

                            Text {
                                text: "입력 모드"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            ComboBox {
                                id: editInputMode
                                Layout.fillWidth: true
                                height: 32
                                model: ["auto", "note_required", "chat_only", "note_and_chat", "selection_required"]
                                currentIndex: {
                                    var mode = root.currentAction ? root.currentAction.input_mode : "auto"
                                    var idx = model.indexOf(mode)
                                    return idx >= 0 ? idx : 0
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true

                                Text {
                                    text: "활성"
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textSecondary
                                }

                                CheckBox {
                                    id: editEnabled
                                    checked: root.currentAction ? root.currentAction.enabled : true
                                    onCheckedChanged: {
                                        var c = getController()
                                        if (c && root.currentAction && root.currentAction.action_id && checked !== root.currentAction.enabled) {
                                            c.set_action_enabled(root.currentAction.action_id, checked)
                                            root.refreshFromController()
                                        }
                                    }
                                }

                                Text {
                                    text: "RAG 사용"
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textSecondary
                                }

                                CheckBox {
                                    id: editUseRag
                                    checked: root.currentAction ? root.currentAction.use_rag : false
                                }
                            }

                            Text {
                                text: "필수 변수"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            TextField {
                                id: editRequiredVars
                                Layout.fillWidth: true
                                height: 32
                                text: root.currentAction ? root.currentAction.required_variables_json || "[]" : "[]"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textPrimary
                                background: Rectangle {
                                    color: Colors.bgSecondary
                                    radius: Metrics.radiusSm
                                    border.color: Colors.borderLight
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: Colors.borderLight
                            }

                            Text {
                                text: "연결 프롬프트"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textPrimary
                            }

                            ComboBox {
                                id: editPromptCombo
                                Layout.fillWidth: true
                                height: 32
                                model: root.promptDocumentList.map(function(doc) { return promptDocDisplayTitle(doc) })
                                currentIndex: {
                                    var bindingId = root.currentAction ? root.currentAction.binding_prompt_doc_id : ""
                                    return getPromptDocIndexFromId(bindingId)
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.sm

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: saveBindingBtnArea.containsMouse ? Colors.primary500 : Colors.primary400

                                    Text {
                                        anchors.centerIn: parent
                                        text: "연결 저장"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textInverse
                                    }

                                    MouseArea {
                                        id: saveBindingBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.saveBinding()
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: openPromptBtnArea.containsMouse ? Colors.primary500 : Colors.primary400

                                    Text {
                                        anchors.centerIn: parent
                                        text: "프롬프트 열기"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textInverse
                                    }

                                    MouseArea {
                                        id: openPromptBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.openBoundPrompt()
                                    }
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.sm

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: newPromptBtnArea.containsMouse ? Colors.primary500 : Colors.primary400

                                    Text {
                                        anchors.centerIn: parent
                                        text: "+ 새 프롬프트"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textInverse
                                    }

                                    MouseArea {
                                        id: newPromptBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.createNewPromptAndBind()
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: duplicatePromptBtnArea.containsMouse ? Colors.primary500 : Colors.primary400
                                    visible: root.currentAction && root.currentAction.binding_prompt_doc_id

                                    Text {
                                        anchors.centerIn: parent
                                        text: "복사해서 수정"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textInverse
                                    }

                                    MouseArea {
                                        id: duplicatePromptBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.duplicatePromptAndBind()
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: Colors.borderLight
                            }

                            // Validation result
                            Rectangle {
                                Layout.fillWidth: true
                                height: 30
                                radius: Metrics.radiusSm
                                color: Colors.bgTertiary

                                Text {
                                    anchors.centerIn: parent
                                    text: {
                                        var validation = validateCurrentBinding()
                                        if (validation.ok)
                                            return "✓ 변수 검사 통과"
                                        return "⚠ 누락: " + (validation.missing_required_variables || []).join(", ")
                                    }
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    color: validation.ok ? Colors.success700 : Colors.warning700
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: Colors.borderLight
                            }

                            // Action buttons
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.sm

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: saveBtnArea.containsMouse ? Colors.primary500 : Colors.primary400

                                    Text {
                                        anchors.centerIn: parent
                                        text: "저장"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textInverse
                                    }

                                    MouseArea {
                                        id: saveBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.saveCurrentAction()
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: duplicateBtnArea.containsMouse ? Colors.primary500 : Colors.primary400

                                    Text {
                                        anchors.centerIn: parent
                                        text: "복사"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textInverse
                                    }

                                    MouseArea {
                                        id: duplicateBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.duplicateCurrentAction()
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: deleteBtnArea.containsMouse ? Colors.error500 : Colors.error400
                                    visible: !isDefaultAction(root.currentAction)

                                    Text {
                                        anchors.centerIn: parent
                                        text: "삭제"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textInverse
                                    }

                                    MouseArea {
                                        id: deleteBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.deleteCurrentAction()
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: Colors.bgTertiary
                                    border.color: Colors.borderLight
                                    visible: isDefaultAction(root.currentAction)

                                    Text {
                                        anchors.centerIn: parent
                                        text: "기본 기능"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textTertiary
                                    }
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.sm

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: moveUpBtnArea.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                                    border.color: Colors.borderLight

                                    Text {
                                        anchors.centerIn: parent
                                        text: "↑ 위로"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textSecondary
                                    }

                                    MouseArea {
                                        id: moveUpBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.moveCurrentActionUp()
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: moveDownBtnArea.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                                    border.color: Colors.borderLight

                                    Text {
                                        anchors.centerIn: parent
                                        text: "↓ 아래로"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textSecondary
                                    }

                                    MouseArea {
                                        id: moveDownBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.moveCurrentActionDown()
                                    }
                                }
                            }
                        }

                        // Empty state
                        ColumnLayout {
                            Layout.fillWidth: true
                            visible: !root.isNewMode && (!root.currentAction || !root.currentAction.action_id)

                            Text {
                                Layout.fillWidth: true
                                text: "기능을 선택하거나 새 기능을 만드세요"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textSecondary
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }

                        Item {
                            Layout.fillHeight: true
                        }
                    }
                }
            }
        }

        // Status message
        Rectangle {
            Layout.fillWidth: true
            height: 32
            radius: Metrics.radiusSm
            color: Colors.bgPrimary
            border.color: Colors.borderLight

            Text {
                anchors.centerIn: parent
                text: root.statusMessage
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.bodySmall
                color: Colors.textSecondary
            }
        }

        // Delete confirmation dialog
        Rectangle {
            anchors.fill: parent
            radius: Metrics.radiusXxl
            color: "#80000000"
            visible: root.showDeleteConfirm

            Rectangle {
                anchors.centerIn: parent
                width: 300
                height: 120
                radius: Metrics.radiusLg
                color: Colors.bgPrimary
                border.color: Colors.borderLight

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Metrics.md
                    spacing: Metrics.md

                    Text {
                        Layout.fillWidth: true
                        text: "삭제 확인"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.h6
                        font.weight: Typography.weightSemibold
                        color: Colors.textPrimary
                        horizontalAlignment: Text.AlignHCenter
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "이 AI 기능을 삭제하시겠습니까?"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.bodySmall
                        color: Colors.textSecondary
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.Wrap
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.sm

                        Rectangle {
                            Layout.fillWidth: true
                            height: 32
                            radius: Metrics.radiusMd
                            color: confirmDelBtnArea.containsMouse ? Colors.error500 : Colors.error400

                            Text {
                                anchors.centerIn: parent
                                text: "삭제"
                                font.family: Typography.fontPrimary
                                font.weight: Typography.weightMedium
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textInverse
                            }

                            MouseArea {
                                id: confirmDelBtnArea
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: root.confirmDelete()
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 32
                            radius: Metrics.radiusMd
                            color: cancelDelBtnArea.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                            border.color: Colors.borderLight

                            Text {
                                anchors.centerIn: parent
                                text: "취소"
                                font.family: Typography.fontPrimary
                                font.weight: Typography.weightMedium
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textSecondary
                            }

                            MouseArea {
                                id: cancelDelBtnArea
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: root.showDeleteConfirm = false
                            }
                        }
                    }
                }
            }
        }
    }
}
