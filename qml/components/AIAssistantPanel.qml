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
    property string selectedCategory: ""
    property var categoryOrder: []
    property var actionOrderMap: ({})
    property var favoriteActions: []
    property string favoriteCategoryName: "즐겨찾기"
    property var categoryList: buildCategoryList()
    property var filteredActionList: orderedActionsByCategory(selectedCategory)

    function getActionController() {
        return aiActionControllerObj
    }

    function getSettingsService() {
        return typeof settingsService !== "undefined" && settingsService !== null ? settingsService : null
    }

    function refreshActionList() {
        var aac = getActionController()
        if (aac && aac.refresh) {
            aac.refresh()
        }
    }

    function normalizeCategory(category) {
        return category && category !== "" ? category : "기타"
    }

    function buildCategoryList() {
        var categories = []
        for (var i = 0; i < root.enabledActionList.length; i++) {
            var category = normalizeCategory(root.enabledActionList[i].category)
            if (categories.indexOf(category) < 0) {
                categories.push(category)
            }
        }

        var ordered = []
        // Add favorite category first if there are favorites
        if (root.favoriteActions && root.favoriteActions.length > 0) {
            ordered.push(root.favoriteCategoryName)
        }
        // Add ordered categories from saved order
        for (var j = 0; j < root.categoryOrder.length; j++) {
            if (categories.indexOf(root.categoryOrder[j]) >= 0) {
                ordered.push(root.categoryOrder[j])
            }
        }
        // Add remaining categories
        for (var k = 0; k < categories.length; k++) {
            if (ordered.indexOf(categories[k]) < 0) {
                ordered.push(categories[k])
            }
        }
        return ordered
    }

    function filterActionsByCategory(category) {
        // Handle favorite category
        if (category === root.favoriteCategoryName) {
            var favorites = []
            for (var f = 0; f < root.favoriteActions.length; f++) {
                var favId = root.favoriteActions[f]
                for (var a = 0; a < root.enabledActionList.length; a++) {
                    if (root.enabledActionList[a].action_id === favId) {
                        favorites.push(root.enabledActionList[a])
                        break
                    }
                }
            }
            return favorites
        }
        // Handle normal category
        var filtered = []
        var selected = normalizeCategory(category)
        for (var i = 0; i < root.enabledActionList.length; i++) {
            var action = root.enabledActionList[i]
            if (normalizeCategory(action.category) === selected) {
                filtered.push(action)
            }
        }
        return filtered
    }

    function orderedActionsByCategory(category) {
        // Handle favorite category
        if (category === root.favoriteCategoryName) {
            var favorites = []
            for (var f = 0; f < root.favoriteActions.length; f++) {
                var favId = root.favoriteActions[f]
                for (var a = 0; a < root.enabledActionList.length; a++) {
                    if (root.enabledActionList[a].action_id === favId) {
                        favorites.push(root.enabledActionList[a])
                        break
                    }
                }
            }
            return favorites
        }
        // Handle normal category
        var actions = filterActionsByCategory(category)
        var order = root.actionOrderMap[category] || []
        var ordered = []
        for (var i = 0; i < order.length; i++) {
            for (var j = 0; j < actions.length; j++) {
                if (actions[j].action_id === order[i] && ordered.indexOf(actions[j]) < 0) {
                    ordered.push(actions[j])
                    break
                }
            }
        }
        for (var k = 0; k < actions.length; k++) {
            if (ordered.indexOf(actions[k]) < 0) {
                ordered.push(actions[k])
            }
        }
        return ordered
    }

    function selectFirstActionInCategory() {
        if (root.filteredActionList.length > 0) {
            root.selectedAction = root.filteredActionList[0]
        } else {
            root.selectedAction = ({})
        }
    }

    function ensureActionSelection() {
        if (root.categoryList.length === 0) {
            root.selectedCategory = ""
            root.selectedAction = ({})
            return
        }

        if (!root.selectedCategory || root.categoryList.indexOf(root.selectedCategory) < 0) {
            root.selectedCategory = root.categoryList[0]
        }

        if (!root.selectedAction || !root.selectedAction.action_id) {
            root.selectFirstActionInCategory()
        }
    }

    function moveCategory(fromIndex, toIndex) {
        if (fromIndex < 0 || toIndex < 0 || fromIndex === toIndex)
            return
        var list = root.categoryList.slice()
        if (fromIndex >= list.length || toIndex >= list.length)
            return
        var item = list.splice(fromIndex, 1)[0]
        list.splice(toIndex, 0, item)
        root.categoryOrder = list
        root.categoryList = root.buildCategoryList()
        root.saveActionSelectionOrder()
    }

    function moveActionInCategory(category, fromIndex, toIndex) {
        if (fromIndex < 0 || toIndex < 0 || fromIndex === toIndex)
            return
        var actions = root.orderedActionsByCategory(category)
        if (fromIndex >= actions.length || toIndex >= actions.length)
            return
        var item = actions.splice(fromIndex, 1)[0]
        actions.splice(toIndex, 0, item)

        var map = {}
        for (var key in root.actionOrderMap) {
            map[key] = root.actionOrderMap[key]
        }
        var order = []
        for (var i = 0; i < actions.length; i++) {
            order.push(actions[i].action_id)
        }
        map[category] = order
        root.actionOrderMap = map
        root.saveActionSelectionOrder()
    }

    function loadActionSelectionOrder() {
        var ss = root.getSettingsService()
        if (!ss || !ss.get_value)
            return
        var raw = ss.get_value("ai_panel_action_selection_order", "{}")
        try {
            var data = JSON.parse(raw || "{}")
            root.categoryOrder = data.categories || []
            root.actionOrderMap = data.actions || ({})
            root.categoryList = root.buildCategoryList()
        } catch (e) {
            root.categoryOrder = []
            root.actionOrderMap = ({})
        }
    }

    function saveActionSelectionOrder() {
        var ss = root.getSettingsService()
        if (!ss || !ss.set_value)
            return
        var data = {
            categories: root.categoryOrder,
            actions: root.actionOrderMap,
            favorites: root.favoriteActions
        }
        ss.set_value("ai_panel_action_selection_order", JSON.stringify(data))
    }

    function loadFavoriteActions() {
        var ss = root.getSettingsService()
        if (!ss || !ss.get_value)
            return
        var raw = ss.get_value("ai_panel_action_selection_order", "{}")
        try {
            var data = JSON.parse(raw || "{}")
            root.favoriteActions = data.favorites || []
        } catch (e) {
            root.favoriteActions = []
        }
    }

    function toggleFavorite(actionId) {
        var idx = root.favoriteActions.indexOf(actionId)
        if (idx >= 0) {
            root.favoriteActions.splice(idx, 1)
        } else {
            root.favoriteActions.push(actionId)
        }
        root.saveActionSelectionOrder()
    }

    function isFavorite(actionId) {
        return root.favoriteActions.indexOf(actionId) >= 0
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
        if (mode === "current_note_qa") return "현재 문서에 대해 질문하세요."
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

        if (action.action_id === "current_note_qa") {
            if (!window.currentNote || !window.currentNote.content) {
                console.log("[AIAssistantPanel] current_note_qa requires a note to be open")
                return
            }
            if (!userInput) {
                console.log("[AIAssistantPanel] current_note_qa requires a question input")
                return
            }
            ac.askQuestion(window.currentNote.content, userInput)
        } else if (isDefaultAction(action.action_id)) {
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

        root.loadActionSelectionOrder()
        root.loadFavoriteActions()
        root.refreshActionList()
        root.ensureActionSelection()
    }

    Connections {
        target: aiActionControllerObj
        function onActionsChanged() {
            root.categoryList = root.buildCategoryList()
            root.ensureActionSelection()
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

                        ListView {
                            id: categoryFolderView
                            width: parent.width
                            height: 180
                            clip: true
                            spacing: Metrics.xs
                            model: root.categoryList
                            boundsBehavior: Flickable.StopAtBounds

                            delegate: Item {
                                id: categoryDelegate
                                width: categoryFolderView.width
                                height: dragArea.drag.active ? 36 : categoryContent.implicitHeight
                                z: dragArea.drag.active ? 10 : 0

                                property string categoryName: modelData
                                property int visualIndex: index !== undefined ? index : 0
                                property bool wasDragged: false

                                Column {
                                    id: categoryContent
                                    width: parent.width
                                    spacing: 0

                                    Rectangle {
                                        width: parent.width
                                        height: 36
                                        color: dragArea.drag.active ? Colors.primary50 : "transparent"
                                        radius: Metrics.radiusSm

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.leftMargin: Metrics.xs
                                            anchors.rightMargin: Metrics.xs
                                            spacing: Metrics.xs

                                            Text {
                                                text: "☰"
                                                font.pixelSize: 12
                                                color: Colors.textTertiary
                                                verticalAlignment: Text.AlignVCenter
                                            }

                                            Text {
                                                text: root.selectedCategory === categoryDelegate.categoryName ? "📂" : "📁"
                                                font.pixelSize: 14
                                                verticalAlignment: Text.AlignVCenter
                                            }

                                            Text {
                                                Layout.fillWidth: true
                                                text: categoryDelegate.categoryName
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: Typography.bodySmall
                                                font.weight: root.selectedCategory === categoryDelegate.categoryName ? Font.Bold : Font.Normal
                                                color: root.selectedCategory === categoryDelegate.categoryName ? Colors.primary700 : Colors.textPrimary
                                                verticalAlignment: Text.AlignVCenter
                                            }

                                            Text {
                                                text: root.filterActionsByCategory(categoryDelegate.categoryName).length
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: Typography.caption
                                                color: root.selectedCategory === categoryDelegate.categoryName ? Colors.primary500 : Colors.textTertiary
                                                verticalAlignment: Text.AlignVCenter
                                            }
                                        }

                                        MouseArea {
                                            id: dragArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            drag.target: categoryDelegate
                                            drag.axis: Drag.YAxis
                                            drag.threshold: 6
                                            onPositionChanged: {
                                                if (drag.active) {
                                                    categoryDelegate.wasDragged = true
                                                }
                                            }
                                            onClicked: {
                                                if (categoryDelegate.wasDragged) {
                                                    categoryDelegate.wasDragged = false
                                                    return
                                                }
                                                if (root.selectedCategory === categoryDelegate.categoryName) {
                                                    root.selectedCategory = ""
                                                    root.selectedAction = ({})
                                                } else {
                                                    root.selectedCategory = categoryDelegate.categoryName
                                                    root.selectFirstActionInCategory()
                                                }
                                            }
                                            onReleased: {
                                                var targetIndex = categoryFolderView.indexAt(categoryDelegate.width / 2, categoryDelegate.y + categoryDelegate.height / 2)
                                                if (targetIndex < 0)
                                                    targetIndex = Math.max(0, Math.min(root.categoryList.length - 1, categoryDelegate.visualIndex))
                                                root.moveCategory(categoryDelegate.visualIndex, targetIndex)
                                                categoryDelegate.y = 0
                                                categoryDelegate.wasDragged = false
                                            }
                                        }
                                    }

                                    Column {
                                        width: parent.width
                                        visible: root.selectedCategory === categoryDelegate.categoryName && !dragArea.drag.active
                                        spacing: 0

                                        Repeater {
                                            model: root.orderedActionsByCategory(categoryDelegate.categoryName)

                                            Rectangle {
                                                width: parent.width
                                                height: 34
                                                color: root.selectedAction && root.selectedAction.action_id === modelData.action_id ? Colors.primary50 : "transparent"
                                                radius: Metrics.radiusSm

                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.leftMargin: 24
                                                    anchors.rightMargin: Metrics.sm
                                                    spacing: Metrics.xs

                                                    Text {
                                                        text: "⚡"
                                                        font.pixelSize: 11
                                                        verticalAlignment: Text.AlignVCenter
                                                    }

                                                    Text {
                                                        Layout.fillWidth: true
                                                        text: modelData.name || modelData.action_id
                                                        font.family: Typography.fontPrimary
                                                        font.pixelSize: Typography.bodySmall
                                                        color: root.selectedAction && root.selectedAction.action_id === modelData.action_id ? Colors.primary700 : Colors.textSecondary
                                                        verticalAlignment: Text.AlignVCenter
                                                        elide: Text.ElideRight
                                                    }

                                                    Text {
                                                        text: root.isFavorite(modelData.action_id) ? "★" : "☆"
                                                        font.pixelSize: 14
                                                        color: root.isFavorite(modelData.action_id) ? Colors.warning : Colors.textTertiary
                                                        verticalAlignment: Text.AlignVCenter
                                                        MouseArea {
                                                            width: 24
                                                            height: 24
                                                            anchors.centerIn: parent
                                                            onClicked: {
                                                                root.toggleFavorite(modelData.action_id)
                                                                root.categoryList = root.buildCategoryList()
                                                            }
                                                        }
                                                    }
                                                }

                                                MouseArea {
                                                    anchors.fill: parent
                                                    anchors.rightMargin: 24
                                                    hoverEnabled: true
                                                    onClicked: root.selectedAction = modelData
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            Text {
                                visible: root.categoryList.length === 0
                                width: categoryFolderView.width
                                text: "사용 가능한 AI 기능이 없습니다."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.textSecondary
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }

                        Rectangle {
                            width: parent.width
                            implicitHeight: selectedActionTitle.implicitHeight + (selectedActionDescription.visible ? selectedActionDescription.implicitHeight + Metrics.xs : 0) + Metrics.md * 2
                            radius: Metrics.radiusMd
                            color: Colors.bgSecondary
                            border.color: Colors.borderLight
                            border.width: 1
                            visible: !!(root.selectedAction && root.selectedAction.action_id)

                            Column {
                                width: parent.width - (Metrics.md * 2)
                                anchors.horizontalCenter: parent.horizontalCenter
                                anchors.topMargin: Metrics.sm
                                anchors.bottomMargin: Metrics.sm
                                spacing: Metrics.xs

                                Text {
                                    id: selectedActionTitle
                                    width: parent.width
                                    text: root.selectedAction ? (root.selectedAction.name || root.selectedAction.action_id) : ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodyMedium
                                    font.weight: Font.Bold
                                    color: Colors.textPrimary
                                }

                                Text {
                                    id: selectedActionDescription
                                    width: parent.width
                                    visible: root.selectedAction && root.selectedAction.description && root.selectedAction.description !== ""
                                    text: root.selectedAction ? root.selectedAction.description : ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.textSecondary
                                    wrapMode: Text.Wrap
                                }
                            }
                        }

                        TextField {
                            id: actionInput
                            width: parent.width
                            placeholderText: root.selectedAction ? (root.selectedAction.action_id === "current_note_qa" ? "현재 문서에 대해 질문하세요." : getInputModePlaceholder(root.selectedAction.input_mode)) : "AI 기능을 선택하세요"
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

                    }
                }

                Rectangle {
                    width: parent.width
                    radius: Metrics.radiusLg
                    color: Colors.surface
                    border.color: Colors.borderLight
                    implicitHeight: questionColumn.implicitHeight + (Metrics.md * 2)
                    visible: false

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

