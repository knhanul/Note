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

    property var promptControllerObj: typeof promptController !== "undefined" && promptController !== null ? promptController : null
    property var actionList: promptControllerObj ? promptControllerObj.actionList : []
    property var promptDocumentList: promptControllerObj ? promptControllerObj.promptDocumentList : []
    property var currentAction: promptControllerObj ? promptControllerObj.currentAction : ({})

    function getController() {
        return promptControllerObj
    }

    function selectAction(actionId) {
        var pc = getController()
        if (!pc || !actionId)
            return

        pc.load_action(actionId)
    }

    function refreshFromController() {
        var pc = getController()
        if (!pc)
            return
        root.actionList = pc.actionList
        root.promptDocumentList = pc.promptDocumentList
        root.currentAction = pc.currentAction
    }

    function bindSelectedPrompt(actionId, promptDocId) {
        var pc = getController()
        if (!pc || !actionId || !promptDocId)
            return false
        return pc.set_binding(actionId, promptDocId)
    }

    function resetBindingToDefault(actionId) {
        var pc = getController()
        if (!pc || !actionId)
            return false
        return pc.reset_binding_to_default(actionId)
    }

    function validatePromptForAction(actionId, promptDocId) {
        var pc = getController()
        if (!pc || !actionId || !promptDocId)
            return {ok: true, missing_required_variables: [], unknown_variables: []}
        return pc.validate_prompt_for_action(actionId, promptDocId)
    }

    function createPromptFromActionDefault(actionId) {
        var pc = getController()
        if (!pc || !actionId)
            return ""
        return pc.create_prompt_from_default(actionId)
    }

    function copyPromptDocument(promptDocId) {
        var pc = getController()
        if (!pc || !promptDocId)
            return ""
        return pc.copy_prompt_document(promptDocId)
    }

    function requestOpenPromptDocument(promptDocId) {
        var pc = getController()
        if (!pc || !promptDocId)
            return
        pc.requestOpenPromptDocument(promptDocId)
    }

    function formatVariables(variables) {
        if (!variables || !variables.length)
            return "없음"
        return variables.map(function(v) { return "{{" + v + "}}" }).join(", ")
    }

    function promptDocDisplayTitle(doc) {
        if (!doc)
            return ""
        var title = doc.title || doc.prompt_doc_id || ""
        if (doc.readonly)
            title += " · 읽기 전용"
        return title
    }

    Component.onCompleted: {
        refreshFromController()
        if (root.actionList && root.actionList.length > 0) {
            selectAction(root.actionList[0].action_id)
        }
    }

    Connections {
        target: promptControllerObj
        function onActionsChanged() { root.refreshFromController() }
        function onPromptDocumentsChanged() { root.refreshFromController() }
        function onCurrentActionChanged() { root.refreshFromController() }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.md
        spacing: Metrics.sm

        Text {
            Layout.fillWidth: true
            text: "기능별 프롬프트 연결"
            font.family: Typography.fontPrimary
            font.pixelSize: Typography.h5
            font.weight: Typography.weightSemibold
            color: Colors.textPrimary
        }

        Text {
            Layout.fillWidth: true
            text: "AI 기능에 사용할 프롬프트 문서를 선택하고 연결합니다."
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

            // Left: Action list
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
                        text: "AI 기능 목록"
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
                            height: 40
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

            // Right: Prompt binding details
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

                        Text {
                            text: root.currentAction ? (root.currentAction.action_name || root.currentAction.action_id || "") : ""
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.h6
                            font.weight: Typography.weightSemibold
                            color: Colors.textPrimary
                        }

                        Text {
                            text: root.currentAction ? (root.currentAction.action_description || "") : ""
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            color: Colors.textSecondary
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Colors.borderLight
                        }

                        Text {
                            text: "필수 변수"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            font.weight: Typography.weightMedium
                            color: Colors.textPrimary
                        }

                        Text {
                            text: root.currentAction ? formatVariables(root.currentAction.required_variables || []) : ""
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            color: Colors.textSecondary
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Colors.borderLight
                        }

                        Text {
                            text: "현재 연결된 프롬프트"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            font.weight: Typography.weightMedium
                            color: Colors.textPrimary
                        }

                        ComboBox {
                            Layout.fillWidth: true
                            model: root.promptDocumentList.map(function(doc) { return promptDocDisplayTitle(doc) })
                            currentIndex: {
                                if (!root.currentAction || !root.currentAction.binding_prompt_doc_id)
                                    return -1
                                for (var i = 0; i < root.promptDocumentList.length; i++) {
                                    if (root.promptDocumentList[i].prompt_doc_id === root.currentAction.binding_prompt_doc_id)
                                        return i
                                }
                                return -1
                            }
                            onActivated: function(index) {
                                if (index >= 0 && index < root.promptDocumentList.length) {
                                    var promptDocId = root.promptDocumentList[index].prompt_doc_id
                                    var actionId = root.currentAction ? root.currentAction.action_id : ""
                                    if (actionId && promptDocId) {
                                        root.bindSelectedPrompt(actionId, promptDocId)
                                        root.selectAction(actionId)
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Colors.borderLight
                        }

                        // Prompt status
                        Rectangle {
                            Layout.fillWidth: true
                            height: 30
                            radius: Metrics.radiusSm
                            color: {
                                if (!root.currentAction || !root.currentAction.current_prompt)
                                    return Colors.bgTertiary
                                var doc = root.currentAction.current_prompt
                                if (doc.readonly)
                                    return Colors.warning100
                                return Colors.success100
                            }

                            Text {
                                anchors.centerIn: parent
                                text: {
                                    if (!root.currentAction || !root.currentAction.current_prompt)
                                        return "선택된 프롬프트 없음"
                                    var doc = root.currentAction.current_prompt
                                    if (doc.readonly)
                                        return "기본 프롬프트"
                                    return "사용자 프롬프트"
                                }
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: {
                                    if (!root.currentAction || !root.currentAction.current_prompt)
                                        return Colors.textTertiary
                                    var doc = root.currentAction.current_prompt
                                    if (doc.readonly)
                                        return Colors.warning700
                                    return Colors.success700
                                }
                            }
                        }

                        // Variable validation
                        Rectangle {
                            Layout.fillWidth: true
                            height: 30
                            radius: Metrics.radiusSm
                            color: Colors.bgTertiary
                            visible: root.currentAction && root.currentAction.current_prompt !== undefined

                            Text {
                                anchors.centerIn: parent
                                text: {
                                    if (!root.currentAction || !root.currentAction.current_prompt)
                                        return ""
                                    var validation = root.validatePromptForAction(
                                        root.currentAction.action_id,
                                        root.currentAction.current_prompt.prompt_doc_id
                                    )
                                    if (validation && validation.ok)
                                        return "✓ 변수 검사 통과"
                                    return "⚠ 변수 누락: " + (validation.missing_required_variables || []).join(", ")
                                }
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: {
                                    if (!root.currentAction || !root.currentAction.current_prompt)
                                        return Colors.textTertiary
                                    var validation = root.validatePromptForAction(
                                        root.currentAction.action_id,
                                        root.currentAction.current_prompt.prompt_doc_id
                                    )
                                    if (validation && validation.ok)
                                        return Colors.success700
                                    return Colors.warning700
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Colors.borderLight
                        }

                        // Buttons
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.sm

                            Rectangle {
                                Layout.fillWidth: true
                                height: 32
                                radius: Metrics.radiusMd
                                color: openBtnArea.containsMouse ? Colors.primary500 : Colors.primary400
                                visible: root.currentAction && root.currentAction.current_prompt !== undefined

                                Text {
                                    anchors.centerIn: parent
                                    text: "선택한 프롬프트 열기"
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightMedium
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textInverse
                                }

                                MouseArea {
                                    id: openBtnArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: {
                                        if (root.currentAction && root.currentAction.current_prompt) {
                                            root.requestOpenPromptDocument(root.currentAction.current_prompt.prompt_doc_id)
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 32
                                radius: Metrics.radiusMd
                                color: createBtnArea.containsMouse ? Colors.primary500 : Colors.primary400

                                Text {
                                    anchors.centerIn: parent
                                    text: "새 프롬프트 만들기"
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightMedium
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textInverse
                                }

                                MouseArea {
                                    id: createBtnArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: {
                                        var actionId = root.currentAction ? root.currentAction.action_id : ""
                                        if (actionId) {
                                            var newId = root.createPromptFromActionDefault(actionId)
                                            if (newId) {
                                                root.bindSelectedPrompt(actionId, newId)
                                                root.selectAction(actionId)
                                                root.requestOpenPromptDocument(newId)
                                            }
                                        }
                                    }
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
                                color: copyBtnArea.containsMouse ? Colors.primary500 : Colors.primary400
                                visible: root.currentAction && root.currentAction.current_prompt !== undefined && root.currentAction.current_prompt.readonly

                                Text {
                                    anchors.centerIn: parent
                                    text: "복사해서 수정"
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightMedium
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textInverse
                                }

                                MouseArea {
                                    id: copyBtnArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: {
                                        if (root.currentAction && root.currentAction.current_prompt) {
                                            var promptDocId = root.currentAction.current_prompt.prompt_doc_id
                                            var newId = root.copyPromptDocument(promptDocId)
                                            if (newId) {
                                                var actionId = root.currentAction.action_id
                                                root.bindSelectedPrompt(actionId, newId)
                                                root.selectAction(actionId)
                                                root.requestOpenPromptDocument(newId)
                                            }
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 32
                                radius: Metrics.radiusMd
                                color: {
                                    if (!Colors.warning500 || !Colors.warning400) return "#F59E0B"
                                    return resetBtnArea.containsMouse ? Colors.warning500 : Colors.warning400
                                }

                                Text {
                                    anchors.centerIn: parent
                                    text: "기본값으로 복원"
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightMedium
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textInverse
                                }

                                MouseArea {
                                    id: resetBtnArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: {
                                        var actionId = root.currentAction ? root.currentAction.action_id : ""
                                        if (actionId) {
                                            root.resetBindingToDefault(actionId)
                                            root.selectAction(actionId)
                                        }
                                    }
                                }
                            }
                        }

                        Item {
                            Layout.fillHeight: true
                        }
                    }
                }
            }
        }
    }
}
