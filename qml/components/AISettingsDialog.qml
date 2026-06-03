import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Dialogs
import theme

Rectangle {
    id: root
    visible: false
    anchors.centerIn: parent
    width: 900
    height: 650
    radius: Metrics.radiusXxl
    color: Colors.bgPrimary
    border.color: Colors.borderLight
    border.width: 1
    z: 9000

    property int settingsMenuIndex: 0

    // Category management state
    property var categoryList: []
    property string newCategoryName: ""
    property int editingCategoryIndex: -1
    property string editingCategoryName: ""

    function loadCategoryList() {
        var ss = typeof settingsService !== "undefined" && settingsService !== null ? settingsService : null
        var defaults = ["문서 작업", "문서 질문", "요약/정리", "번역", "코드/수식", "기타"]
        if (!ss) { root.categoryList = defaults; return }
        try {
            var raw = ss.get_value("ai_category_list", "")
            if (raw) {
                var parsed = JSON.parse(raw)
                if (Array.isArray(parsed) && parsed.length > 0) { root.categoryList = parsed; return }
            }
        } catch (e) {}
        root.categoryList = defaults
    }

    function saveCategoryList() {
        var ss = typeof settingsService !== "undefined" && settingsService !== null ? settingsService : null
        if (!ss) return
        ss.set_value("ai_category_list", JSON.stringify(root.categoryList))
    }

    function addCategory(name) {
        if (!name || name.trim() === "") return false
        var trimmed = name.trim()
        for (var i = 0; i < root.categoryList.length; i++) {
            if (root.categoryList[i] === trimmed) return false
        }
        var arr = root.categoryList.slice()
        arr.push(trimmed)
        root.categoryList = arr
        saveCategoryList()
        return true
    }

    function removeCategory(index) {
        if (index < 0 || index >= root.categoryList.length) return
        var arr = root.categoryList.slice()
        arr.splice(index, 1)
        root.categoryList = arr
        saveCategoryList()
    }

    function renameCategory(index, newName) {
        if (index < 0 || index >= root.categoryList.length) return false
        if (!newName || newName.trim() === "") return false
        var trimmed = newName.trim()
        for (var i = 0; i < root.categoryList.length; i++) {
            if (i !== index && root.categoryList[i] === trimmed) return false
        }
        var oldName = root.categoryList[index]
        var arr = root.categoryList.slice()
        arr[index] = trimmed
        root.categoryList = arr
        saveCategoryList()
        // Update actions that had the old category name
        var c = typeof aiActionController !== "undefined" && aiActionController !== null ? aiActionController : null
        if (c && oldName !== trimmed) {
            var actions = c.actionList || []
            for (var j = 0; j < actions.length; j++) {
                if (actions[j].category === oldName) {
                    c.update_action(actions[j].action_id, actions[j].name, actions[j].description || "",
                                    trimmed, actions[j].input_mode || "auto", !!actions[j].use_rag,
                                    actions[j].required_variables_json || "[]", !!actions[j].enabled,
                                    actions[j].response_length || "medium")
                }
            }
        }
        return true
    }

    function moveCategoryUp(index) {
        if (index <= 0 || index >= root.categoryList.length) return
        var arr = root.categoryList.slice()
        var tmp = arr[index - 1]
        arr[index - 1] = arr[index]
        arr[index] = tmp
        root.categoryList = arr
        saveCategoryList()
    }

    function moveCategoryDown(index) {
        if (index < 0 || index >= root.categoryList.length - 1) return
        var arr = root.categoryList.slice()
        var tmp = arr[index + 1]
        arr[index + 1] = arr[index]
        arr[index] = tmp
        root.categoryList = arr
        saveCategoryList()
    }

    function getCategoryActionCount(categoryName) {
        var c = typeof aiActionController !== "undefined" && aiActionController !== null ? aiActionController : null
        if (!c) return 0
        var count = 0
        var actions = c.actionList || []
        for (var i = 0; i < actions.length; i++) {
            if ((actions[i].category || "기타") === categoryName) count++
        }
        return count
    }

    property bool aiConnected: typeof aiAssistantController !== "undefined" && aiAssistantController !== null ? aiAssistantController.isConnected : false
    property string aiChatModel: typeof aiAssistantController !== "undefined" && aiAssistantController !== null ? aiAssistantController.chatModel : ""
    property string aiEmbeddingModel: typeof aiAssistantController !== "undefined" && aiAssistantController !== null ? aiAssistantController.embeddingModel : ""
    property string aiPerformanceMode: typeof aiAssistantController !== "undefined" && aiAssistantController !== null ? aiAssistantController.performanceMode : "low"
    property var aiModelList: typeof aiAssistantController !== "undefined" && aiAssistantController !== null ? aiAssistantController.modelList : []

    signal closed()

    Component.onCompleted: {
        if (!root.hasPromptController() && root.settingsMenuIndex === 1)
            root.settingsMenuIndex = 0
    }

    function getController() {
        return typeof aiAssistantController !== "undefined" && aiAssistantController !== null ? aiAssistantController : null
    }

    function getAssistantController() {
        return typeof assistantController !== "undefined" && assistantController !== null ? assistantController : null
    }

    function getPromptController() {
        return typeof promptController !== "undefined" && promptController !== null ? promptController : null
    }

    function hasPromptController() {
        return getPromptController() !== null
    }

    function canUseAI() {
        return root.aiConnected && root.aiChatModel !== ""
    }

    function safeGet(prop, defaultVal) {
        var c = getController()
        return c && c[prop] !== undefined ? c[prop] : defaultVal
    }

    function syncAssistantSettings() {
        var ac = getAssistantController()
        if (ac && ac.reloadSettings) {
            ac.reloadSettings()
        }
    }

    function syncChatModelCombo() {
        if (!chatModelCombo)
            return
        var idx = root.aiModelList.indexOf(root.aiChatModel)
        chatModelCombo.currentIndex = idx >= 0 ? idx : -1
    }

    function syncEmbeddingModelCombo() {
        if (!embeddingModelCombo)
            return
        var idx = root.aiModelList.indexOf(root.aiEmbeddingModel)
        embeddingModelCombo.currentIndex = idx >= 0 ? idx : -1
    }

    MouseArea {
        anchors.fill: parent
        onClicked: {}
    }

    Rectangle {
        anchors.fill: parent
        color: "transparent"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Metrics.md
            spacing: Metrics.sm

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.sm

                Text {
                    Layout.fillWidth: true
                    text: "AI 설정"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.h4
                    font.weight: Typography.weightSemibold
                    color: Colors.textPrimary
                }

                Rectangle {
                    width: 86
                    height: 34
                    radius: Metrics.radiusMd
                    color: closeMA.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                    border.width: 1
                    border.color: Colors.borderLight

                    Text {
                        anchors.centerIn: parent
                        text: "닫기"
                        font.family: Typography.fontPrimary
                        font.pixelSize: 12
                        color: Colors.textSecondary
                    }

                    MouseArea {
                        id: closeMA
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: root.closed()
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Metrics.md

                Rectangle {
                    Layout.preferredWidth: 160
                    Layout.fillHeight: true
                    radius: Metrics.radiusLg
                    color: Colors.bgSecondary
                    border.width: 1
                    border.color: Colors.borderLight

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Metrics.sm
                        spacing: Metrics.sm

                        Rectangle {
                            Layout.fillWidth: true
                            height: 40
                            radius: Metrics.radiusMd
                            color: root.settingsMenuIndex === 0 ? Colors.primary50 : (modelSettingsMenuMA.containsMouse ? Colors.bgPrimary : "transparent")
                            border.width: 1
                            border.color: root.settingsMenuIndex === 0 ? Colors.primary200 : Colors.borderLight

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: Metrics.md
                                text: "모델 설정"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: root.settingsMenuIndex === 0 ? Typography.weightSemibold : Typography.weightRegular
                                color: root.settingsMenuIndex === 0 ? Colors.primary700 : Colors.textSecondary
                            }

                            MouseArea {
                                id: modelSettingsMenuMA
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: root.settingsMenuIndex = 0
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 40
                            radius: Metrics.radiusMd
                            color: root.settingsMenuIndex === 1 ? Colors.primary50 : (actionSettingsMenuMA.containsMouse ? Colors.bgPrimary : "transparent")
                            border.width: 1
                            border.color: root.settingsMenuIndex === 1 ? Colors.primary200 : Colors.borderLight
                            visible: typeof aiActionController !== "undefined" && aiActionController !== null

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: Metrics.md
                                text: "AI 기능 관리"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: root.settingsMenuIndex === 1 ? Typography.weightSemibold : Typography.weightRegular
                                color: root.settingsMenuIndex === 1 ? Colors.primary700 : Colors.textSecondary
                            }

                            MouseArea {
                                id: actionSettingsMenuMA
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: root.settingsMenuIndex = 1
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 40
                            radius: Metrics.radiusMd
                            color: root.settingsMenuIndex === 2 ? Colors.primary50 : (categoryMenuMA.containsMouse ? Colors.bgPrimary : "transparent")
                            border.width: 1
                            border.color: root.settingsMenuIndex === 2 ? Colors.primary200 : Colors.borderLight

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: Metrics.md
                                text: "카테고리 관리"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: root.settingsMenuIndex === 2 ? Typography.weightSemibold : Typography.weightRegular
                                color: root.settingsMenuIndex === 2 ? Colors.primary700 : Colors.textSecondary
                            }

                            MouseArea {
                                id: categoryMenuMA
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    root.settingsMenuIndex = 2
                                    root.loadCategoryList()
                                }
                            }
                        }

                        Item { Layout.fillHeight: true }
                    }
                }

                StackLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: root.settingsMenuIndex

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: Metrics.radiusLg
                        color: Colors.bgSecondary
                        border.width: 1
                        border.color: Colors.borderLight

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: Metrics.sm
                            spacing: Metrics.sm

                            Text {
                                text: "모델 설정"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.h5
                                font.weight: Typography.weightSemibold
                                color: Colors.textPrimary
                            }

                            Text {
                                Layout.fillWidth: true
                                text: "Ollama 모델을 설정하고 연결하세요. 모델을 선택하면 자동으로 연결됩니다."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textSecondary
                                wrapMode: Text.Wrap
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: Colors.borderLight
                            }

                            ScrollView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                ScrollBar.vertical.policy: ScrollBar.AsNeeded

                                ColumnLayout {
                                    width: parent.width
                                    spacing: Metrics.sm

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: Metrics.xs

                                        Text {
                                            text: "연결 상태"
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: Typography.caption
                                            font.weight: Typography.weightMedium
                                            color: Colors.textSecondary
                                        }

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: Metrics.sm

                                            Rectangle {
                                                Layout.preferredWidth: 120
                                                height: 32
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

                                            Button {
                                                text: "연결 확인"
                                                Layout.preferredHeight: 32
                                                contentItem: Text {
                                                    text: parent.text
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.caption
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
                                                onClicked: {
                                                    var c = getController()
                                                    if (c) c.check_connection()
                                                }
                                            }
                                        }
                                    }

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Layout.maximumWidth: 560
                                        Layout.alignment: Qt.AlignLeft
                                        spacing: Metrics.sm

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: Metrics.sm

                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                Layout.preferredWidth: 260
                                                Layout.maximumWidth: 260
                                                spacing: Metrics.xs

                                                Text {
                                                    text: "LLM 모델 (생성)"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.caption
                                                    font.weight: Typography.weightMedium
                                                    color: Colors.textSecondary
                                                }

                                                Text {
                                                    Layout.fillWidth: true
                                                    Layout.maximumWidth: 260
                                                    text: "답변을 작성하는 모델입니다. 요약, 문장 다듬기, 보고서 초안 작성에 사용됩니다."
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.caption
                                                    color: Colors.textTertiary
                                                    wrapMode: Text.Wrap
                                                    maximumLineCount: 3
                                                }
                                            }

                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                Layout.preferredWidth: 260
                                                Layout.maximumWidth: 260
                                                spacing: Metrics.xs

                                                Text {
                                                    text: "검색 모델 (임베딩)"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.caption
                                                    font.weight: Typography.weightMedium
                                                    color: Colors.textSecondary
                                                }

                                                Text {
                                                    Layout.fillWidth: true
                                                    Layout.maximumWidth: 260
                                                    text: "문서에서 관련 내용을 찾아주는 모델입니다. 현재 폴더 질문, 외부 문서 검색, 관련 노트 추천에 사용됩니다."
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.caption
                                                    color: Colors.textTertiary
                                                    wrapMode: Text.Wrap
                                                    maximumLineCount: 3
                                                }
                                            }
                                        }

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: Metrics.sm

                                            ComboBox {
                                                id: chatModelCombo
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 32
                                                Layout.preferredWidth: 260
                                                Layout.maximumWidth: 260
                                                model: root.aiModelList
                                                currentIndex: -1
                                                Component.onCompleted: syncChatModelCombo()
                                                onModelChanged: syncChatModelCombo()
                                                onActivated: {
                                                    var list = root.aiModelList
                                                    if (chatModelCombo.currentIndex >= 0 && chatModelCombo.currentIndex < list.length) {
                                                        var c = getController()
                                                        if (c) {
                                                            c.setChatModel(list[chatModelCombo.currentIndex])
                                                            c.check_connection()
                                                            syncAssistantSettings()
                                                            syncChatModelCombo()
                                                        }
                                                    }
                                                }
                                            }

                                            ComboBox {
                                                id: embeddingModelCombo
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 32
                                                Layout.preferredWidth: 260
                                                Layout.maximumWidth: 260
                                                model: root.aiModelList
                                                currentIndex: -1
                                                Component.onCompleted: syncEmbeddingModelCombo()
                                                onModelChanged: syncEmbeddingModelCombo()
                                                onActivated: {
                                                    var list = root.aiModelList
                                                    if (embeddingModelCombo.currentIndex >= 0 && embeddingModelCombo.currentIndex < list.length) {
                                                        var c = getController()
                                                        if (c) {
                                                            c.setEmbeddingModel(list[embeddingModelCombo.currentIndex])
                                                            syncAssistantSettings()
                                                            syncEmbeddingModelCombo()
                                                        }
                                                    }
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
                                            Layout.fillWidth: false
                                            Layout.preferredWidth: 260
                                            Layout.maximumWidth: 260
                                            Layout.alignment: Qt.AlignLeft
                                            spacing: Metrics.xs
                                            height: 24

                                            Rectangle {
                                                Layout.fillHeight: true
                                                Layout.fillWidth: true
                                                radius: Metrics.radiusSm
                                                color: root.aiPerformanceMode === "low" ? Colors.success : Colors.bgTertiary
                                                border.color: Colors.borderLight
                                                border.width: root.aiPerformanceMode === "low" ? 0 : 1
                                                Text {
                                                    anchors.centerIn: parent
                                                    text: "저사양"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.caption
                                                    color: root.aiPerformanceMode === "low" ? Colors.bgPrimary : Colors.textSecondary
                                                }
                                                MouseArea {
                                                    anchors.fill: parent
                                                    onClicked: {
                                                        var c = getController()
                                                        if (c) {
                                                            c.setPerformanceMode("low")
                                                            syncAssistantSettings()
                                                        }
                                                    }
                                                }
                                            }

                                            Rectangle {
                                                Layout.fillHeight: true
                                                Layout.fillWidth: true
                                                radius: 0
                                                color: root.aiPerformanceMode === "normal" ? Colors.success : Colors.bgTertiary
                                                border.color: Colors.borderLight
                                                border.width: root.aiPerformanceMode === "normal" ? 0 : 1
                                                Text {
                                                    anchors.centerIn: parent
                                                    text: "일반"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.caption
                                                    color: root.aiPerformanceMode === "normal" ? Colors.bgPrimary : Colors.textSecondary
                                                }
                                                MouseArea {
                                                    anchors.fill: parent
                                                    onClicked: {
                                                        var c = getController()
                                                        if (c) {
                                                            c.setPerformanceMode("normal")
                                                            syncAssistantSettings()
                                                        }
                                                    }
                                                }
                                            }

                                            Rectangle {
                                                Layout.fillHeight: true
                                                Layout.fillWidth: true
                                                radius: Metrics.radiusSm
                                                color: root.aiPerformanceMode === "high" ? Colors.success : Colors.bgTertiary
                                                border.color: Colors.borderLight
                                                border.width: root.aiPerformanceMode === "high" ? 0 : 1
                                                Text {
                                                    anchors.centerIn: parent
                                                    text: "고성능"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.caption
                                                    color: root.aiPerformanceMode === "high" ? Colors.bgPrimary : Colors.textSecondary
                                                }
                                                MouseArea {
                                                    anchors.fill: parent
                                                    onClicked: {
                                                        var c = getController()
                                                        if (c) {
                                                            c.setPerformanceMode("high")
                                                            syncAssistantSettings()
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        AIActionManagementPanel {
                            anchors.fill: parent
                            visible: typeof aiActionController !== "undefined" && aiActionController !== null
                        }

                        ColumnLayout {
                            anchors.fill: parent
                            spacing: Metrics.sm
                            visible: typeof aiActionController === "undefined" || aiActionController === null

                            Text {
                                Layout.fillWidth: true
                                text: "AI 기능 관리를 사용할 수 없습니다."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textSecondary
                                horizontalAlignment: Text.AlignHCenter
                            }

                            Text {
                                Layout.fillWidth: true
                                text: "이 탭은 work_ai_editor에서만 활성화됩니다."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.textTertiary
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                    }

                    // 카테고리 관리 tab (index 2)
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: Metrics.md
                            spacing: Metrics.md

                            Text {
                                text: "카테고리 관리"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.h5
                                font.weight: Typography.weightSemibold
                                color: Colors.textPrimary
                            }

                            Text {
                                Layout.fillWidth: true
                                text: "AI 기능을 분류하는 카테고리를 추가, 수정, 삭제, 정렬할 수 있습니다."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textSecondary
                                wrapMode: Text.Wrap
                            }

                            Rectangle { Layout.fillWidth: true; height: 1; color: Colors.borderLight }

                            // Add new category
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.sm

                                TextField {
                                    id: newCategoryInput
                                    Layout.fillWidth: true
                                    placeholderText: "새 카테고리 이름"
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textPrimary
                                    background: Rectangle {
                                        color: Colors.bgPrimary
                                        radius: Metrics.radiusSm
                                        border.color: Colors.borderLight
                                        border.width: 1
                                    }
                                    onAccepted: {
                                        if (root.addCategory(text)) {
                                            text = ""
                                        }
                                    }
                                }

                                Rectangle {
                                    width: 70
                                    height: 32
                                    radius: Metrics.radiusSm
                                    color: addCatBtnMA.containsMouse ? Colors.primary600 : Colors.primary500

                                    Text {
                                        anchors.centerIn: parent
                                        text: "추가"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.bodySmall
                                        font.weight: Typography.weightMedium
                                        color: Colors.textInverse
                                    }

                                    MouseArea {
                                        id: addCatBtnMA
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            if (root.addCategory(newCategoryInput.text)) {
                                                newCategoryInput.text = ""
                                            }
                                        }
                                    }
                                }
                            }

                            Rectangle { Layout.fillWidth: true; height: 1; color: Colors.borderLight }

                            // Category list
                            ScrollView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                ScrollBar.vertical.policy: ScrollBar.AsNeeded

                                ColumnLayout {
                                    width: parent.width
                                    spacing: Metrics.xs

                                    Repeater {
                                        model: root.categoryList

                                        Rectangle {
                                            Layout.fillWidth: true
                                            implicitHeight: 44
                                            radius: Metrics.radiusSm
                                            color: catItemMA.containsMouse ? Colors.bgSecondary : Colors.surface
                                            border.color: Colors.borderLight
                                            border.width: 1

                                            property int catIndex: index
                                            property string catName: modelData

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.leftMargin: Metrics.md
                                                anchors.rightMargin: Metrics.sm
                                                spacing: Metrics.sm

                                                // Inline rename field (visible only when editing this row)
                                                TextField {
                                                    id: renameCatInput
                                                    Layout.fillWidth: true
                                                    visible: root.editingCategoryIndex === catIndex
                                                    text: root.editingCategoryName
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.bodySmall
                                                    color: Colors.textPrimary
                                                    background: Rectangle {
                                                        color: Colors.bgPrimary
                                                        radius: Metrics.radiusSm
                                                        border.color: Colors.primary300
                                                        border.width: 1
                                                    }
                                                    onAccepted: {
                                                        if (root.renameCategory(catIndex, text)) {
                                                            root.editingCategoryIndex = -1
                                                        }
                                                    }
                                                    Keys.onEscapePressed: root.editingCategoryIndex = -1
                                                }

                                                // Normal display
                                                Text {
                                                    Layout.fillWidth: true
                                                    visible: root.editingCategoryIndex !== catIndex
                                                    text: catName
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.bodySmall
                                                    font.weight: Typography.weightMedium
                                                    color: Colors.textPrimary
                                                    elide: Text.ElideRight
                                                }

                                                // Action count badge
                                                Rectangle {
                                                    visible: root.editingCategoryIndex !== catIndex
                                                    implicitWidth: countText.implicitWidth + 10
                                                    implicitHeight: 20
                                                    radius: 10
                                                    color: Colors.bgTertiary
                                                    Layout.alignment: Qt.AlignVCenter

                                                    Text {
                                                        id: countText
                                                        anchors.centerIn: parent
                                                        text: root.getCategoryActionCount(catName)
                                                        font.family: Typography.fontPrimary
                                                        font.pixelSize: 10
                                                        color: Colors.textSecondary
                                                    }
                                                }

                                                // Move up
                                                Rectangle {
                                                    width: 24; height: 24; radius: 12
                                                    color: moveUpMA.containsMouse ? Colors.bgTertiary : "transparent"
                                                    visible: root.editingCategoryIndex !== catIndex
                                                    Layout.alignment: Qt.AlignVCenter
                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: "\u25B2"
                                                        font.pixelSize: 10
                                                        color: catIndex > 0 ? Colors.textSecondary : Colors.textTertiary
                                                    }
                                                    MouseArea {
                                                        id: moveUpMA
                                                        anchors.fill: parent
                                                        hoverEnabled: true
                                                        cursorShape: Qt.PointingHandCursor
                                                        onClicked: root.moveCategoryUp(catIndex)
                                                    }
                                                }

                                                // Move down
                                                Rectangle {
                                                    width: 24; height: 24; radius: 12
                                                    color: moveDownMA.containsMouse ? Colors.bgTertiary : "transparent"
                                                    visible: root.editingCategoryIndex !== catIndex
                                                    Layout.alignment: Qt.AlignVCenter
                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: "\u25BC"
                                                        font.pixelSize: 10
                                                        color: catIndex < root.categoryList.length - 1 ? Colors.textSecondary : Colors.textTertiary
                                                    }
                                                    MouseArea {
                                                        id: moveDownMA
                                                        anchors.fill: parent
                                                        hoverEnabled: true
                                                        cursorShape: Qt.PointingHandCursor
                                                        onClicked: root.moveCategoryDown(catIndex)
                                                    }
                                                }

                                                // Rename button
                                                Rectangle {
                                                    width: 24; height: 24; radius: 12
                                                    color: renameMA.containsMouse ? Colors.bgTertiary : "transparent"
                                                    visible: root.editingCategoryIndex !== catIndex
                                                    Layout.alignment: Qt.AlignVCenter
                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: "\u270E"
                                                        font.pixelSize: 12
                                                        color: Colors.textSecondary
                                                    }
                                                    MouseArea {
                                                        id: renameMA
                                                        anchors.fill: parent
                                                        hoverEnabled: true
                                                        cursorShape: Qt.PointingHandCursor
                                                        onClicked: {
                                                            root.editingCategoryIndex = catIndex
                                                            root.editingCategoryName = catName
                                                        }
                                                    }
                                                }

                                                // Confirm rename
                                                Rectangle {
                                                    width: 24; height: 24; radius: 12
                                                    color: confirmRenameMA.containsMouse ? Colors.success : Colors.bgTertiary
                                                    visible: root.editingCategoryIndex === catIndex
                                                    Layout.alignment: Qt.AlignVCenter
                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: "\u2713"
                                                        font.pixelSize: 12
                                                        font.weight: Typography.weightBold
                                                        color: confirmRenameMA.containsMouse ? Colors.textInverse : Colors.textSecondary
                                                    }
                                                    MouseArea {
                                                        id: confirmRenameMA
                                                        anchors.fill: parent
                                                        hoverEnabled: true
                                                        cursorShape: Qt.PointingHandCursor
                                                        onClicked: {
                                                            if (root.renameCategory(catIndex, renameCatInput.text))
                                                                root.editingCategoryIndex = -1
                                                        }
                                                    }
                                                }

                                                // Cancel rename
                                                Rectangle {
                                                    width: 24; height: 24; radius: 12
                                                    color: cancelRenameMA.containsMouse ? Colors.bgTertiary : "transparent"
                                                    visible: root.editingCategoryIndex === catIndex
                                                    Layout.alignment: Qt.AlignVCenter
                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: "\u2715"
                                                        font.pixelSize: 10
                                                        color: Colors.textSecondary
                                                    }
                                                    MouseArea {
                                                        id: cancelRenameMA
                                                        anchors.fill: parent
                                                        hoverEnabled: true
                                                        cursorShape: Qt.PointingHandCursor
                                                        onClicked: root.editingCategoryIndex = -1
                                                    }
                                                }

                                                // Delete button
                                                Rectangle {
                                                    width: 24; height: 24; radius: 12
                                                    color: delCatMA.containsMouse ? Colors.error50 : "transparent"
                                                    visible: root.editingCategoryIndex !== catIndex
                                                    Layout.alignment: Qt.AlignVCenter
                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: "\u2715"
                                                        font.pixelSize: 10
                                                        color: delCatMA.containsMouse ? Colors.error : Colors.textTertiary
                                                    }
                                                    MouseArea {
                                                        id: delCatMA
                                                        anchors.fill: parent
                                                        hoverEnabled: true
                                                        cursorShape: Qt.PointingHandCursor
                                                        onClicked: {
                                                            // Reassign actions in this category to "기타"
                                                            var c = typeof aiActionController !== "undefined" && aiActionController !== null ? aiActionController : null
                                                            if (c) {
                                                                var actions = c.actionList || []
                                                                for (var i = 0; i < actions.length; i++) {
                                                                    if ((actions[i].category || "기타") === catName) {
                                                                        c.update_action(actions[i].action_id, actions[i].name, actions[i].description || "",
                                                                                        "기타", actions[i].input_mode || "auto", !!actions[i].use_rag,
                                                                                        actions[i].required_variables_json || "[]", !!actions[i].enabled,
                                                                                        actions[i].response_length || "medium")
                                                                    }
                                                                }
                                                            }
                                                            root.removeCategory(catIndex)
                                                        }
                                                    }
                                                }
                                            }

                                            MouseArea {
                                                id: catItemMA
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                z: -1
                                            }
                                        }
                                    }

                                    Item {
                                        Layout.fillHeight: true
                                        Layout.minimumHeight: Metrics.md
                                    }
                                }
                            }

                            Text {
                                Layout.fillWidth: true
                                text: "카테고리를 삭제하면 해당 카테고리의 기능은 '기타'로 이동합니다."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.textTertiary
                                wrapMode: Text.Wrap
                            }
                        }
                    }
                }
            }
        }
    }

}
