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
    property var currentPromptDocument: promptControllerObj ? promptControllerObj.currentPromptDocument : ({})
    property var validation: promptControllerObj ? promptControllerObj.validation : ({"ok": true, "missing_required_variables": [], "unknown_variables": []})
    property string selectedActionId: promptControllerObj ? promptControllerObj.currentActionId : ""
    property string selectedPromptDocId: promptControllerObj ? promptControllerObj.currentPromptDocumentId : ""
    property string statusMessage: ""
    property bool statusError: false

    function getController() {
        return promptControllerObj
    }

    function currentActionItem() {
        if (!root.actionList || !root.selectedActionId)
            return null
        for (var i = 0; i < root.actionList.length; i++) {
            var item = root.actionList[i]
            if (item && String(item.action_id || "") === root.selectedActionId)
                return item
        }
        return null
    }

    function promptDocItem(promptDocId) {
        if (!root.promptDocumentList || !promptDocId)
            return null
        for (var i = 0; i < root.promptDocumentList.length; i++) {
            var item = root.promptDocumentList[i]
            if (item && String(item.prompt_doc_id || "") === promptDocId)
                return item
        }
        return null
    }

    function selectAction(actionId) {
        var pc = getController()
        if (!pc || !actionId)
            return

        pc.load_action(actionId)
        root.selectedActionId = actionId

        var binding = pc.get_binding(actionId)
        root.selectedPromptDocId = binding && binding.binding_prompt_doc_id ? binding.binding_prompt_doc_id : actionId
        root.statusMessage = ""
        root.statusError = false
    }

    function selectPromptDocument(promptDocId) {
        root.selectedPromptDocId = promptDocId || ""
    }

    function refreshFromController() {
        var pc = getController()
        if (!pc)
            return
        root.actionList = pc.actionList
        root.promptDocumentList = pc.promptDocumentList
        root.currentAction = pc.currentAction
        root.currentPromptDocument = pc.currentPromptDocument
        root.validation = pc.validation
        root.selectedActionId = pc.currentActionId
        root.selectedPromptDocId = pc.currentPromptDocumentId
    }

    function promptDocDisplayTitle(doc) {
        if (!doc)
            return ""
        var title = doc.title || doc.prompt_doc_id || ""
        if (doc.readonly)
            title += " · 읽기 전용"
        return title
    }

    function formatVariables(variables) {
        if (!variables || !variables.length)
            return "없음"
        return variables.map(function(v) { return "{{" + v + "}}" }).join(", ")
    }

    function bindSelectedPrompt() {
        var pc = getController()
        if (!pc || !root.selectedActionId || !root.selectedPromptDocId)
            return
        var ok = pc.set_binding(root.selectedActionId, root.selectedPromptDocId)
        statusError = !ok
        statusMessage = ok ? "연결이 저장되었습니다." : "연결 저장에 실패했습니다."
        if (ok) {
            refreshFromController()
        }
    }

    function resetBinding() {
        var pc = getController()
        if (!pc || !root.selectedActionId)
            return
        var ok = pc.reset_binding_to_default(root.selectedActionId)
        statusError = !ok
        statusMessage = ok ? "기본 연결로 복원했습니다." : "기본 연결 복원에 실패했습니다."
        if (ok) {
            refreshFromController()
        }
    }

    function validateSelected() {
        var pc = getController()
        if (!pc || !root.selectedActionId || !root.selectedPromptDocId)
            return
        var result = pc.validate_prompt_for_action(root.selectedActionId, root.selectedPromptDocId)
        root.validation = result
        statusError = !(result && result.ok)
        statusMessage = (result && result.ok) ? "검사가 통과되었습니다." : "변수 검사를 확인하세요."
    }

    function openSelectedPromptDocument() {
        var pc = getController()
        if (!pc || !root.selectedPromptDocId)
            return
        if (typeof window !== "undefined" && window && window.openAIPromptDocument) {
            window.openAIPromptDocument(root.selectedPromptDocId)
        } else {
            pc.open_prompt_document(root.selectedPromptDocId)
        }
    }

    function createPromptCopyFromDefault() {
        var pc = getController()
        if (!pc || !root.selectedActionId)
            return
        var newId = pc.create_prompt_from_default(root.selectedActionId)
        if (newId) {
            statusError = false
            statusMessage = "새 프롬프트 문서를 생성했습니다."
            selectPromptDocument(newId)
            refreshFromController()
            if (typeof window !== "undefined" && window && window.openAIPromptDocument) {
                window.openAIPromptDocument(newId)
            }
        }
    }

    function currentPromptDocumentInfo() {
        return promptDocItem(root.selectedPromptDocId)
    }

    Component.onCompleted: {
        refreshFromController()
        if (!root.selectedActionId && root.actionList && root.actionList.length > 0) {
            selectAction(root.actionList[0].action_id)
        } else if (root.selectedActionId) {
            selectAction(root.selectedActionId)
        }
    }

    Connections {
        target: promptControllerObj
        function onActionsChanged() { root.refreshFromController() }
        function onPromptDocumentsChanged() { root.refreshFromController() }
        function onCurrentActionChanged() { root.refreshFromController() }
        function onCurrentPromptDocumentChanged() { root.refreshFromController() }
        function onValidationChanged() { root.refreshFromController() }
        function onCurrentPromptDocumentIdChanged() { root.refreshFromController() }
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
                text: "AI 프롬프트 관리"
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.h5
                font.weight: Typography.weightSemibold
                color: Colors.textPrimary
            }

            Text {
                text: "기능 ↔ 프롬프트 문서 연결"
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.caption
                color: Colors.textSecondary
            }
        }

        Text {
            Layout.fillWidth: true
            text: "프롬프트 본문은 메인 마크다운 에디터의 AI 프롬프트 서재에서 수정합니다. 이 탭에서는 기능별 연결만 저장합니다."
            wrapMode: Text.WordWrap
            font.family: Typography.fontPrimary
            font.pixelSize: Typography.caption
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
                Layout.preferredWidth: 260
                Layout.fillHeight: true
                radius: Metrics.radiusMd
                color: Colors.bgPrimary
                border.color: Colors.borderLight

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Metrics.sm
                    spacing: Metrics.xs

                    Text {
                        text: "AI 기능"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.bodySmall
                        font.weight: Typography.weightSemibold
                        color: Colors.textPrimary
                    }

                    ListView {
                        id: actionListView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: root.actionList
                        clip: true
                        spacing: Metrics.xs

                        delegate: Rectangle {
                            width: ListView.view.width
                            height: 64
                            radius: Metrics.radiusSm
                            color: String(action_id || "") === root.selectedActionId ? Colors.primary50 : Colors.bgSecondary
                            border.color: String(action_id || "") === root.selectedActionId ? Colors.primary200 : Colors.borderLight

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: Metrics.xs
                                spacing: 2

                                Text {
                                    Layout.fillWidth: true
                                    text: name || action_id
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    font.weight: Typography.weightMedium
                                    color: Colors.textPrimary
                                    elide: Text.ElideRight
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: category || "기본"
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.textSecondary
                                    elide: Text.ElideRight
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: description || ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.textTertiary
                                    elide: Text.ElideRight
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: root.selectAction(String(action_id || ""))
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: Metrics.radiusMd
                color: Colors.bgPrimary
                border.color: Colors.borderLight

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Metrics.md
                    spacing: Metrics.sm

                    RowLayout {
                        Layout.fillWidth: true

                        Text {
                            Layout.fillWidth: true
                            text: root.currentAction && root.currentAction.action ? root.currentAction.action.name : "기능을 선택하세요"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.h5
                            font.weight: Typography.weightSemibold
                            color: Colors.textPrimary
                        }

                        Rectangle {
                            visible: root.currentPromptDocument && root.currentPromptDocument.readonly
                            radius: Metrics.radiusFull
                            color: Colors.bgTertiary
                            border.color: Colors.borderLight

                            Text {
                                anchors.margins: Metrics.xs
                                anchors.centerIn: parent
                                text: "읽기 전용"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.textSecondary
                            }
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: root.currentAction && root.currentAction.action ? (root.currentAction.action.description || "") : "왼쪽에서 AI 기능을 선택하세요."
                        wrapMode: Text.WordWrap
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.bodySmall
                        color: Colors.textSecondary
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.sm

                        Text {
                            text: "필수 변수"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            font.weight: Typography.weightMedium
                            color: Colors.textSecondary
                        }

                        Text {
                            Layout.fillWidth: true
                            text: formatVariables(root.currentAction && root.currentAction.required_variables ? root.currentAction.required_variables : [])
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: Colors.textTertiary
                            elide: Text.ElideRight
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.sm

                        Text {
                            text: "현재 연결"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            font.weight: Typography.weightMedium
                            color: Colors.textSecondary
                        }

                        Text {
                            Layout.fillWidth: true
                            text: root.currentPromptDocument ? promptDocDisplayTitle(root.currentPromptDocument) : "연결된 문서가 없습니다"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: Colors.textPrimary
                            elide: Text.ElideRight
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.sm

                        ComboBox {
                            id: promptCombo
                            Layout.fillWidth: true
                            model: root.promptDocumentList
                            textRole: "title"
                            valueRole: "prompt_doc_id"
                            currentIndex: {
                                var idx = -1
                                for (var i = 0; i < root.promptDocumentList.length; i++) {
                                    var doc = root.promptDocumentList[i]
                                    if (doc && String(doc.prompt_doc_id || "") === root.selectedPromptDocId) {
                                        idx = i
                                        break
                                    }
                                }
                                return idx
                            }
                            onActivated: function(index) {
                                if (index >= 0 && index < root.promptDocumentList.length) {
                                    var doc = root.promptDocumentList[index]
                                    root.selectPromptDocument(doc ? String(doc.prompt_doc_id || "") : "")
                                }
                            }
                        }

                        Button {
                            text: "선택한 프롬프트 열기"
                            enabled: root.selectedPromptDocId !== ""
                            onClicked: root.openSelectedPromptDocument()
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Metrics.sm

                        Button {
                            text: "복사해서 수정"
                            enabled: root.selectedActionId !== ""
                            onClicked: root.createPromptCopyFromDefault()
                        }

                        Button {
                            text: "기본값으로 복원"
                            enabled: root.selectedActionId !== ""
                            onClicked: root.resetBinding()
                        }

                        Button {
                            text: "변수 검사"
                            enabled: root.selectedActionId !== "" && root.selectedPromptDocId !== ""
                            onClicked: root.validateSelected()
                        }

                        Button {
                            text: "저장"
                            enabled: root.selectedActionId !== "" && root.selectedPromptDocId !== ""
                            onClicked: root.bindSelectedPrompt()
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: Metrics.radiusMd
                        color: Colors.bgSecondary
                        border.color: Colors.borderLight

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: Metrics.sm
                            spacing: Metrics.xs

                            Text {
                                text: "선택한 프롬프트 문서"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightSemibold
                                color: Colors.textPrimary
                            }

                            Text {
                                Layout.fillWidth: true
                                text: root.currentPromptDocument ? (root.currentPromptDocument.description || "") : "프롬프트 문서를 선택하세요."
                                wrapMode: Text.WordWrap
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.textSecondary
                            }

                            Text {
                                Layout.fillWidth: true
                                text: root.currentPromptDocument ? ("source_type: " + (root.currentPromptDocument.source_type || "") + " / readonly: " + (root.currentPromptDocument.readonly ? "1" : "0")) : ""
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.textTertiary
                            }

                            Text {
                                Layout.fillWidth: true
                                visible: root.currentPromptDocument && root.currentPromptDocument.variables && root.currentPromptDocument.variables.length > 0
                                text: "문서 변수: " + formatVariables(root.currentPromptDocument ? root.currentPromptDocument.variables : [])
                                wrapMode: Text.WordWrap
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.textTertiary
                            }
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: root.validation && ((!root.validation.ok) || (root.validation.unknown_variables && root.validation.unknown_variables.length) || (root.validation.missing_required_variables && root.validation.missing_required_variables.length))
                        text: {
                            var parts = []
                            if (root.validation.missing_required_variables && root.validation.missing_required_variables.length)
                                parts.push("필수 변수 누락: " + root.validation.missing_required_variables.join(", "))
                            if (root.validation.unknown_variables && root.validation.unknown_variables.length)
                                parts.push("알 수 없는 변수: " + root.validation.unknown_variables.join(", "))
                            return parts.join(" | ")
                        }
                        wrapMode: Text.WordWrap
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.caption
                        color: Colors.warning
                    }

                    Text {
                        Layout.fillWidth: true
                        visible: root.statusMessage !== ""
                        text: root.statusMessage
                        wrapMode: Text.WordWrap
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.caption
                        color: root.statusError ? Colors.error : Colors.success
                    }
                }
            }
        }
    }
}
