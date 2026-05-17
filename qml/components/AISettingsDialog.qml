import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import theme

Rectangle {
    id: root
    visible: false
    anchors.centerIn: parent
    width: 800
    height: 500
    radius: Metrics.radiusXxl
    color: Colors.bgPrimary
    border.color: Colors.borderLight
    border.width: 1
    z: 9000

    property int settingsMenuIndex: 0

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
                            color: root.settingsMenuIndex === 1 ? Colors.primary50 : (promptSettingsMenuMA.containsMouse ? Colors.bgPrimary : "transparent")
                            border.width: 1
                            border.color: root.settingsMenuIndex === 1 ? Colors.primary200 : Colors.borderLight
                            visible: root.hasPromptController()

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: Metrics.md
                                text: "프롬프트 연결"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: root.settingsMenuIndex === 1 ? Typography.weightSemibold : Typography.weightRegular
                                color: root.settingsMenuIndex === 1 ? Colors.primary700 : Colors.textSecondary
                            }

                            MouseArea {
                                id: promptSettingsMenuMA
                                anchors.fill: parent
                                hoverEnabled: true
                                enabled: root.hasPromptController()
                                onClicked: root.settingsMenuIndex = 1
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 40
                            radius: Metrics.radiusMd
                            color: root.settingsMenuIndex === 2 ? Colors.primary50 : (actionSettingsMenuMA.containsMouse ? Colors.bgPrimary : "transparent")
                            border.width: 1
                            border.color: root.settingsMenuIndex === 2 ? Colors.primary200 : Colors.borderLight
                            visible: typeof aiActionController !== "undefined" && aiActionController !== null

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: Metrics.md
                                text: "AI 기능 관리"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: root.settingsMenuIndex === 2 ? Typography.weightSemibold : Typography.weightRegular
                                color: root.settingsMenuIndex === 2 ? Colors.primary700 : Colors.textSecondary
                            }

                            MouseArea {
                                id: actionSettingsMenuMA
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: root.settingsMenuIndex = 2
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

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: Metrics.radiusLg
                        color: Colors.bgSecondary
                        border.width: 1
                        border.color: Colors.borderLight

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: Metrics.md
                            spacing: Metrics.md

                            Text {
                                text: "프롬프트 관리"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.h5
                                font.weight: Typography.weightSemibold
                                color: Colors.textPrimary
                            }

                            Text {
                                Layout.fillWidth: true
                                text: "AI 기능에 사용되는 프롬프트 템플릿을 관리합니다."
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

                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                PromptBindingPanel {
                                    anchors.fill: parent
                                    visible: root.hasPromptController()
                                }

                                ColumnLayout {
                                    anchors.centerIn: parent
                                    width: parent.width
                                    spacing: Metrics.sm
                                    visible: !root.hasPromptController()

                                    Text {
                                        Layout.fillWidth: true
                                        text: "프롬프트 연결 기능을 사용할 수 없습니다."
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
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            radius: Metrics.radiusLg
                            color: Colors.bgSecondary
                            border.width: 1
                            border.color: Colors.borderLight

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: Metrics.md
                                spacing: Metrics.md

                                AIActionManagementPanel {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    visible: typeof aiActionController !== "undefined" && aiActionController !== null
                                }

                                ColumnLayout {
                                    Layout.alignment: Qt.AlignCenter
                                    Layout.fillWidth: true
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
                        }
                    }
                }
            }
        }
    }
}
