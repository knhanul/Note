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

    property var actionList: aiActionControllerObj ? aiActionControllerObj.actionList : []
    property var promptDocumentList: promptControllerObj ? promptControllerObj.promptDocumentList : []
    property var filteredPromptList: {
        if (!promptDocumentList || promptDocumentList.length === 0) return []
        // 모든 프롬프트 표시
        return promptDocumentList
    }
    property var currentAction: aiActionControllerObj ? aiActionControllerObj.currentAction : ({})

    property bool isNewMode: false
    property bool isEditMode: false
    property string statusMessage: ""
    property bool showDeleteConfirm: false

    function getActionController() {
        return aiActionControllerObj
    }

    function getPromptController() {
        return promptControllerObj
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
        // Properties will auto-update via Python signals
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
        root.statusMessage = "새 기능을 입력하세요"
    }

    function cancelEdit() {
        root.isNewMode = false
        root.isEditMode = false
        root.statusMessage = ""
    }

    function saveNewAction() {
        var c = getActionController()
        if (!c) return

        var name = newActionName.text.trim()
        if (!name) {
            root.statusMessage = "기능 이름은 필수입니다"
            return
        }

        var actionId = c.generate_action_id(name)

        var description = newActionDescription.text.trim()
        var category = newActionCategory.currentText || "user"
        var inputMode = newActionInputMode.currentText || "auto"
        var useRag = newActionUseRag.checked
        var requiredVars = newActionRequiredVars.text.trim() || "[]"

        var result = c.create_action(name, actionId, description, category, inputMode, useRag, requiredVars, true)
        if (result && result.action_id) {
            // 프롬프트 연결 처리
            var promptIdx = newActionPromptBinding.currentIndex
            if (promptIdx >= 0 && promptIdx < root.filteredPromptList.length) {
                var promptDocId = root.filteredPromptList[promptIdx].prompt_doc_id
                c.set_binding(actionId, promptDocId)
            }
            newActionPromptBinding.currentIndex = -1
            root.isNewMode = false
            root.statusMessage = "'" + name + "' 기능이 생성되었습니다"
            selectAction(result.action_id)
        } else {
            root.statusMessage = "기능 생성에 실패했습니다"
        }
    }

    function saveCurrentAction() {
        var c = getActionController()
        var action = root.currentAction
        if (!c || !action || !action.action_id) return

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
            // 프롬프트 연결 처리
            var promptIdx = editActionPromptBinding.currentIndex
            if (promptIdx >= 0 && promptIdx < root.filteredPromptList.length) {
                var promptDocId = root.filteredPromptList[promptIdx].prompt_doc_id
                c.set_binding(action.action_id, promptDocId)
            }
            root.isEditMode = false
            root.statusMessage = "저장되었습니다"
            selectAction(action.action_id)
        } else {
            root.statusMessage = "저장에 실패했습니다"
        }
    }

    function deleteCurrentAction() {
        var action = root.currentAction
        if (!action || !action.action_id) {
            root.statusMessage = "삭제할 기능이 없습니다"
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
            root.statusMessage = "삭제되었습니다"
            root.showDeleteConfirm = false
            if (root.actionList && root.actionList.length > 0) {
                selectAction(root.actionList[0].action_id)
            }
        } else {
            root.statusMessage = "삭제에 실패했습니다"
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
        function onCurrentActionChanged() { root.refreshFromController() }
        function onInfoMessage(msg) { root.statusMessage = msg }
        function onErrorOccurred(msg) { root.statusMessage = msg }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.md
        spacing: Metrics.sm

        // Header
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
                    text: "AI 기능을 등록, 수정, 삭제하고 프롬프트 문서와 연결합니다."
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textSecondary
                }
            }

            Button {
                text: "+ AI 기능 추가"
                Layout.preferredHeight: 32
                contentItem: Text {
                    text: parent.text
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    font.weight: Typography.weightMedium
                    color: Colors.primary600
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

        // Main Content
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.md

            // Left: Action List
            Rectangle {
                Layout.preferredWidth: 260
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

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: root.actionList
                        clip: true
                        spacing: 1

                        delegate: Rectangle {
                            width: ListView.view.width
                            height: 36
                            radius: Metrics.radiusSm
                            color: actionMouse.containsMouse ? Colors.primary50 : (root.currentAction && root.currentAction.action_id === modelData.action_id ? Colors.primary100 : "transparent")

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: Metrics.sm
                                anchors.rightMargin: Metrics.sm
                                spacing: Metrics.sm

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.name || modelData.action_id || ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textPrimary
                                    elide: Text.ElideRight
                                }
                            }

                            MouseArea {
                                id: actionMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    root.selectAction(modelData.action_id)
                                }
                            }
                        }

                        ScrollBar.vertical: ScrollBar {
                            policy: ScrollBar.AlwaysOn
                        }
                    }
                }
            }

            // Right: Action Details
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 400
                color: Colors.bgPrimary
                radius: Metrics.radiusMd
                border.color: Colors.borderLight
                border.width: 1
                visible: root.currentAction && root.currentAction.action_id

                ScrollView {
                    anchors.fill: parent
                    anchors.margins: Metrics.md
                    clip: true

                    ColumnLayout {
                        width: parent.width
                        spacing: Metrics.sm

                        // Action Header
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.sm

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.xs

                                Text {
                                    text: root.currentAction ? (root.currentAction.name || root.currentAction.action_id || "") : ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.h6
                                    font.weight: Typography.weightSemibold
                                    color: Colors.textPrimary
                                }

                                Text {
                                    text: root.currentAction ? (root.currentAction.description || "") : ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textSecondary
                                    wrapMode: Text.WordWrap
                                }
                            }

                            RowLayout {
                                spacing: Metrics.xs

                                Rectangle {
                                    width: 60
                                    height: 28
                                    radius: Metrics.radiusSm
                                    color: editBtnArea.containsMouse ? Colors.bgTertiary : "transparent"
                                    border.color: Colors.borderLight
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: "수정"
                                        font.pixelSize: 12
                                        color: Colors.textSecondary
                                    }

                                    MouseArea {
                                        id: editBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: root.isEditMode = true
                                    }
                                }

                                Rectangle {
                                    width: 60
                                    height: 28
                                    radius: Metrics.radiusSm
                                    color: delBtnArea.containsMouse ? Colors.error50 : "transparent"
                                    border.color: Colors.error200
                                    border.width: 1

                                    Text {
                                        anchors.centerIn: parent
                                        text: "삭제"
                                        font.pixelSize: 12
                                        color: Colors.error500
                                    }

                                    MouseArea {
                                        id: delBtnArea
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

                        // Connected Prompt
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.xs

                            Text {
                                text: "연결된 프롬프트"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textPrimary
                            }

                            ComboBox {
                                Layout.fillWidth: true
                                model: root.filteredPromptList.map(function(doc) { return doc.title || doc.prompt_doc_id || "" })
                                currentIndex: {
                                    if (!root.currentAction || !root.currentAction.binding_prompt_doc_id)
                                        return -1
                                    for (var i = 0; i < root.filteredPromptList.length; i++) {
                                        if (root.filteredPromptList[i].prompt_doc_id === root.currentAction.binding_prompt_doc_id)
                                            return i
                                    }
                                    return -1
                                }
                                onActivated: function(index) {
                                    if (index >= 0 && index < root.filteredPromptList.length) {
                                        var promptDocId = root.filteredPromptList[index].prompt_doc_id
                                        var actionId = root.currentAction ? root.currentAction.action_id : ""
                                        if (actionId && promptDocId) {
                                            root.bindSelectedPrompt(actionId, promptDocId)
                                            root.selectAction(actionId)
                                        }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Colors.borderLight
                        }

                        // Action Info
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.xs

                            Text {
                                text: "기능 정보"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textPrimary
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: Metrics.md
                                rowSpacing: Metrics.xs

                                Text { text: "카테고리:"; color: Colors.textSecondary; font.pixelSize: Typography.caption }
                                Text { text: root.currentAction ? (root.currentAction.category || "user") : ""; color: Colors.textPrimary; font.pixelSize: Typography.caption }

                                Text { text: "입력 모드:"; color: Colors.textSecondary; font.pixelSize: Typography.caption }
                                Text { text: root.currentAction ? (root.currentAction.input_mode || "auto") : ""; color: Colors.textPrimary; font.pixelSize: Typography.caption }

                                Text { text: "RAG 사용:"; color: Colors.textSecondary; font.pixelSize: Typography.caption }
                                Text { text: root.currentAction ? (root.currentAction.use_rag ? "예" : "아니오") : ""; color: Colors.textPrimary; font.pixelSize: Typography.caption }

                                Text { text: "필수 변수:"; color: Colors.textSecondary; font.pixelSize: Typography.caption }
                                Text { 
                                    text: root.currentAction ? (root.currentAction.required_variables && root.currentAction.required_variables.length > 0 ? root.currentAction.required_variables.join(", ") : "없음") : ""
                                    color: Colors.textPrimary
                                    font.pixelSize: Typography.caption
                                }
                            }
                        }
                    }
                }
            }
        }

        // Status Message
        Rectangle {
            Layout.fillWidth: true
            height: 32
            radius: Metrics.radiusSm
            color: Colors.bgSecondary
            border.color: Colors.borderLight
            visible: root.statusMessage !== ""

            Text {
                anchors.centerIn: parent
                text: root.statusMessage
                font.family: Typography.fontPrimary
                font.pixelSize: 11
                color: Colors.textSecondary
            }

            Timer {
                interval: 5000
                running: root.statusMessage !== ""
                onTriggered: root.statusMessage = ""
            }
        }
    }

    // New Action Form
    Rectangle {
        anchors.fill: parent
        color: Colors.bgPrimary
        visible: root.isNewMode
        z: 10

        ScrollView {
            anchors.fill: parent
            anchors.margins: Metrics.md
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: Metrics.sm

                Text {
                    text: "새 AI 기능 등록"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.h6
                    font.weight: Typography.weightSemibold
                    color: Colors.textPrimary
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: Colors.borderLight }

                Text { text: "기능 이름"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                TextField {
                    id: newActionName
                    Layout.fillWidth: true
                    height: 32
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textPrimary
                    selectByMouse: true
                    placeholderText: "예: 문서 요약하기"
                }

                Text { text: "설명"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                TextField {
                    id: newActionDescription
                    Layout.fillWidth: true
                    height: 32
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textPrimary
                    selectByMouse: true
                    placeholderText: "이 기능에 대한 설명을 입력하세요"
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.md

                    ColumnLayout {
                        Layout.fillWidth: true
                        Text { text: "카테고리"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                        ComboBox {
                            id: newActionCategory
                            Layout.fillWidth: true
                            height: 32
                            model: ["user", "문서 처리", "문서 질문", "기타"]
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Text { text: "입력 모드"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                        ComboBox {
                            id: newActionInputMode
                            Layout.fillWidth: true
                            height: 32
                            model: ["auto", "note_required", "chat_only", "note_and_chat", "selection_required"]
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    CheckBox { 
                        id: newActionUseRag
                        text: "RAG(문서 검색) 사용"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.bodySmall
                    }
                }

                Text { text: "연결할 프롬프트"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                ComboBox {
                    id: newActionPromptBinding
                    Layout.fillWidth: true
                    height: 32
                    model: root.filteredPromptList.map(function(doc) { return doc.title || doc.prompt_doc_id || "" })
                    currentIndex: -1
                }

                Text { text: "필수 변수 (JSON)"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                TextField {
                    id: newActionRequiredVars
                    Layout.fillWidth: true
                    height: 32
                    text: "[]"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textPrimary
                    selectByMouse: true
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.sm

                    Rectangle {
                        Layout.fillWidth: true
                        height: 36
                        radius: Metrics.radiusMd
                        color: saveNewBtn.containsMouse ? Colors.primary500 : Colors.primary400

                        Text {
                            anchors.centerIn: parent
                            text: "등록"
                            color: Colors.textInverse
                            font.weight: Typography.weightMedium
                        }

                        MouseArea {
                            id: saveNewBtn
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: root.saveNewAction()
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 36
                        radius: Metrics.radiusMd
                        color: cancelNewBtn.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                        border.color: Colors.borderLight

                        Text {
                            anchors.centerIn: parent
                            text: "취소"
                            color: Colors.textSecondary
                        }

                        MouseArea {
                            id: cancelNewBtn
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: root.cancelEdit()
                        }
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
            anchors.margins: Metrics.md
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: Metrics.sm

                Text {
                    text: "AI 기능 수정"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.h6
                    font.weight: Typography.weightSemibold
                    color: Colors.textPrimary
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: Colors.borderLight }

                Text { text: "기능명"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                TextField {
                    id: editName
                    Layout.fillWidth: true
                    height: 32
                    text: root.currentAction ? (root.currentAction.name || "") : ""
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textPrimary
                    selectByMouse: true
                    readOnly: true
                }

                Text { text: "설명"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                TextField {
                    id: editDescription
                    Layout.fillWidth: true
                    height: 32
                    text: root.currentAction ? (root.currentAction.description || "") : ""
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textPrimary
                    selectByMouse: true
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.md

                    ColumnLayout {
                        Layout.fillWidth: true
                        Text { text: "카테고리"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
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
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Text { text: "입력 모드"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
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
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    CheckBox { 
                        id: editUseRag
                        text: "RAG(문서 검색) 사용"
                        checked: root.currentAction ? root.currentAction.use_rag : false
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.bodySmall
                    }
                }

                Text { text: "연결할 프롬프트"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                ComboBox {
                    id: editActionPromptBinding
                    Layout.fillWidth: true
                    height: 32
                    model: root.filteredPromptList.map(function(doc) { return doc.title || doc.prompt_doc_id || "" })
                    currentIndex: {
                        if (!root.currentAction || !root.currentAction.binding_prompt_doc_id)
                            return -1
                        for (var i = 0; i < root.filteredPromptList.length; i++) {
                            if (root.filteredPromptList[i].prompt_doc_id === root.currentAction.binding_prompt_doc_id)
                                return i
                        }
                        return -1
                    }
                }

                Text { text: "필수 변수 (JSON)"; font.family: Typography.fontPrimary; font.pixelSize: Typography.caption; color: Colors.textSecondary }
                TextField {
                    id: editRequiredVars
                    Layout.fillWidth: true
                    height: 32
                    text: root.currentAction ? root.currentAction.required_variables_json || "[]" : "[]"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textPrimary
                    selectByMouse: true
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Metrics.sm

                    Rectangle {
                        Layout.fillWidth: true
                        height: 36
                        radius: Metrics.radiusMd
                        color: saveEditBtn.containsMouse ? Colors.primary500 : Colors.primary400

                        Text {
                            anchors.centerIn: parent
                            text: "저장"
                            color: Colors.textInverse
                            font.weight: Typography.weightMedium
                        }

                        MouseArea {
                            id: saveEditBtn
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: root.saveCurrentAction()
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 36
                        radius: Metrics.radiusMd
                        color: cancelEditBtn.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                        border.color: Colors.borderLight

                        Text {
                            anchors.centerIn: parent
                            text: "취소"
                            color: Colors.textSecondary
                        }

                        MouseArea {
                            id: cancelEditBtn
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: root.cancelEdit()
                        }
                    }
                }
            }
        }
    }

    // Delete Confirmation Dialog
    Rectangle {
        anchors.fill: parent
        color: "#80000000"
        visible: root.showDeleteConfirm
        z: 100

        Rectangle {
            anchors.centerIn: parent
            width: 300
            height: 160
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
                    text: "이 AI 기능을 정말 삭제하시겠습니까?\n삭제된 기능은 목록에서 사라집니다."
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
                        color: confirmDelBtn.containsMouse ? Colors.error500 : Colors.error400

                        Text {
                            anchors.centerIn: parent
                            text: "삭제"
                            color: Colors.textInverse
                        }

                        MouseArea {
                            id: confirmDelBtn
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: root.confirmDelete()
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 32
                        radius: Metrics.radiusMd
                        color: cancelDelBtn.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                        border.color: Colors.borderLight

                        Text {
                            anchors.centerIn: parent
                            text: "취소"
                            color: Colors.textSecondary
                        }

                        MouseArea {
                            id: cancelDelBtn
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