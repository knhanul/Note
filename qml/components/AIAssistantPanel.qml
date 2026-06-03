import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
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
    clip: false

    signal openSettingsDialog()
    signal openReferenceDocsSettings()
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
    property int favoriteVersion: 0
    property var categoryList: buildCategoryList()
    property var filteredActionList: orderedActionsByCategory(selectedCategory)

    // RAG citation and warning properties
    property var ragCitations: []
    property var ragWarnings: []
    property bool hasRagCitations: ragCitations && ragCitations.length > 0
    property bool hasRagWarnings: ragWarnings && ragWarnings.length > 0
    property bool ragRequestRunning: false
    property bool ragIndexingRunning: false
    property int ragIndexingProgressCurrent: 0
    property int ragIndexingProgressTotal: 0
    property var ragIndexingProgressItems: []
    property int ragIndexingProgressMaxEntries: 50
    property int aiModeIndex: 0  // 0 = 현재 문서 AI, 1 = 참고문서 AI
    property string lastAskedQuestion: ""
    property string currentStreamingNoteId: ""
    property string currentStreamingContent: ""
    property string currentStreamingTitle: ""
    property var noteEditorRef: null
    property bool currentStreamingIsRag: false
    property string currentRagAnswerText: ""

    // 현재문서 AI 실행 결과 상태
    property var currentAiRunStatus: ({
        lastActionName: "",
        lastQuestion: "",
        lastSuccess: false,
        lastElapsedMs: 0,
        lastResourceText: "",
        lastResultNoteId: "",
        lastResultNoteTitle: "",
        lastErrorMessage: "",
        lastExecutedAt: ""
    })

    // 참고문서 AI(RAG) 실행 결과 상태
    property var ragRunStatus: ({
        lastQuestion: "",
        lastSuccess: false,
        lastElapsedMs: 0,
        lastResourceText: "",
        lastResultNoteId: "",
        lastResultNoteTitle: "",
        lastErrorMessage: "",
        lastExecutedAt: ""
    })

    // RAG 대상 문서 목록 (QML에서 관리)
    property var ragTargetDocuments: []
    property int ragTargetDocumentsTotalCount: 0
    property int ragTargetDocumentsDisplayLimit: 100
    property string ragTargetDocumentsError: ""

    // 실행 시작 시간 추적
    property var aiRunStartTime: 0
    property var ragRunStartTime: 0

    onAiModeIndexChanged: {
        console.log("[AIAssistantPanel][DIAG] aiModeIndex changed:", aiModeIndex)
        if (aiModeIndex === 1) {
            refreshRagTargetDocumentsFromIndex()
        }
    }

    function setAiMode(index, source) {
        console.log("[AIAssistantPanel][DIAG] setAiMode request:", index, "source:", source || "unknown")
        if (root.aiModeIndex === index)
            return
        root.aiModeIndex = index
        if (tabScroll && tabScroll.contentItem) {
            tabScroll.contentItem.contentY = 0
        }
    }

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
        // Collect categories actually used by enabled actions
        var usedCategories = []
        for (var i = 0; i < root.enabledActionList.length; i++) {
            var category = normalizeCategory(root.enabledActionList[i].category)
            if (usedCategories.indexOf(category) < 0) {
                usedCategories.push(category)
            }
        }

        // Load managed category order from settings
        var managedOrder = []
        var ss = getSettingsService()
        if (ss) {
            try {
                var raw = ss.get_value("ai_category_list", "")
                if (raw) {
                    var parsed = JSON.parse(raw)
                    if (Array.isArray(parsed)) managedOrder = parsed
                }
            } catch (e) {}
        }

        var ordered = []
        // Add favorite category first if there are favorites
        if (root.favoriteActions && root.favoriteActions.length > 0) {
            ordered.push(root.favoriteCategoryName)
        }
        // Add categories in managed order (only those that have actions)
        for (var m = 0; m < managedOrder.length; m++) {
            if (usedCategories.indexOf(managedOrder[m]) >= 0 && ordered.indexOf(managedOrder[m]) < 0) {
                ordered.push(managedOrder[m])
            }
        }
        // Add ordered categories from saved selection order
        for (var j = 0; j < root.categoryOrder.length; j++) {
            if (usedCategories.indexOf(root.categoryOrder[j]) >= 0 && ordered.indexOf(root.categoryOrder[j]) < 0) {
                ordered.push(root.categoryOrder[j])
            }
        }
        // Add remaining categories not yet included
        for (var k = 0; k < usedCategories.length; k++) {
            if (ordered.indexOf(usedCategories[k]) < 0) {
                ordered.push(usedCategories[k])
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
            root.favoriteActions = data.favorites || []  // 이 줄 추가
            root.categoryList = root.buildCategoryList()
        } catch (e) {
            root.categoryOrder = []
            root.actionOrderMap = ({})
            root.favoriteActions = []  // 이 줄 추가
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


    function toggleFavorite(actionId) {
        var arr = root.favoriteActions.slice()
        var idx = arr.indexOf(actionId)
        if (idx >= 0) {
            arr.splice(idx, 1)
        } else {
            arr.push(actionId)
        }
        root.favoriteActions = arr
        root.favoriteVersion++
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

    // 상태 업데이트 헬퍼: 현재문서 AI
    function updateCurrentAiStatus(success, resultNoteId, resultNoteTitle, errorMsg) {
        var endTime = new Date().getTime()
        var elapsed = root.aiRunStartTime > 0 ? endTime - root.aiRunStartTime : 0
        var modelName = safeGet("chatModel", "") || "리소스 정보 없음"

        root.currentAiRunStatus = {
            lastActionName: root.currentAiRunStatus.lastActionName,
            lastQuestion: root.currentAiRunStatus.lastQuestion,
            lastSuccess: success,
            lastElapsedMs: elapsed,
            lastResourceText: modelName,
            lastResultNoteId: resultNoteId || "",
            lastResultNoteTitle: resultNoteTitle || "",
            lastErrorMessage: errorMsg || "",
            lastExecutedAt: new Date().toLocaleTimeString()
        }
        root.aiRunStartTime = 0
    }

    // 상태 업데이트 헬퍼: 참고문서 AI (RAG)
    function updateRagRunStatus(success, resultNoteId, resultNoteTitle, errorMsg) {
        var endTime = new Date().getTime()
        var elapsed = root.ragRunStartTime > 0 ? endTime - root.ragRunStartTime : 0
        var modelName = safeGet("chatModel", "") || "리소스 정보 없음"

        root.ragRunStatus = {
            lastQuestion: root.ragRunStatus.lastQuestion,
            lastSuccess: success,
            lastElapsedMs: elapsed,
            lastResourceText: modelName,
            lastResultNoteId: resultNoteId || "",
            lastResultNoteTitle: resultNoteTitle || "",
            lastErrorMessage: errorMsg || "",
            lastExecutedAt: new Date().toLocaleTimeString()
        }
        root.ragRunStartTime = 0
    }

    // RAG 대상 목록 초기화
    function clearRagTargetDocuments() {
        root.ragTargetDocuments = []
        root.ragTargetDocumentsTotalCount = 0
        root.ragTargetDocumentsError = ""
    }

    function refreshRagTargetDocumentsFromIndex(limit) {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) {
            console.log("[AIAssistantPanel] refreshRagTargetDocumentsFromIndex: no RAG controller")
            return
        }

        var displayLimit = limit || root.ragTargetDocumentsDisplayLimit
        try {
            var jsonStr = ragCtrl.listIndexedDocumentsJson(displayLimit)
            if (!jsonStr || jsonStr === "") {
                root.ragTargetDocuments = []
                root.ragTargetDocumentsTotalCount = 0
                root.ragTargetDocumentsError = ""
                return
            }

            var payload = JSON.parse(jsonStr)
            if (payload.error) {
                console.warn("[AIAssistantPanel] Failed to load RAG documents: " + payload.error)
                root.ragTargetDocuments = []
                root.ragTargetDocumentsTotalCount = 0
                root.ragTargetDocumentsError = payload.error
                return
            }

            var docs = Array.isArray(payload.items) ? payload.items : []
            root.ragTargetDocuments = docs
            root.ragTargetDocumentsTotalCount = payload.total_count || docs.length
            root.ragTargetDocumentsError = ""
        } catch (e) {
            console.warn("[AIAssistantPanel] refreshRagTargetDocumentsFromIndex parse error: " + e)
            root.ragTargetDocuments = []
            root.ragTargetDocumentsTotalCount = 0
            root.ragTargetDocumentsError = "목록을 불러오지 못했습니다."
        }
    }

    function formatRagDocumentSubtitle(doc) {
        if (!doc)
            return ""
        var parts = []
        if (doc.note_id) {
            parts.push("노트:" + doc.note_id)
        } else if (doc.source_path) {
            parts.push(doc.source_path)
        } else if (doc.document_id) {
            parts.push(doc.document_id)
        }
        if (doc.source_type) {
            parts.push(doc.source_type)
        }
        var chunkCount = doc.chunk_count
        if (chunkCount === undefined || chunkCount === null || chunkCount === "") {
            chunkCount = 0
        }
        parts.push("청크 " + chunkCount + "개")
        return parts.join(" · ")
    }

    function runSelectedAction() {
        var action = root.selectedAction
        if (!action || !action.action_id) return

        var ac = getAssistantController()
        if (!ac) return

        if (!canUseAI() || root.aiRunning) return

        var userInput = actionInput.text || ""
        root.lastAskedQuestion = userInput || ""
        
        // Step 1: Capture source note info FIRST before any note creation
        var sourceNoteId = ""
        var sourceTitle = ""
        var sourceContent = ""
        
        // Get the currently selected note ID
        var selectedNoteIdBefore = ""
        if (typeof selectedNoteId !== "undefined") {
            selectedNoteIdBefore = selectedNoteId
        }
        
        // Get content from noteEditor (WYSIWYG) first, then fallback to currentNote
        if (typeof noteEditor !== "undefined" && noteEditor) {
            sourceContent = noteEditor.content || ""
            sourceTitle = noteEditor.title || ""
        }
        if (!sourceContent && window.currentNote) {
            sourceContent = window.currentNote.content || ""
            sourceTitle = window.currentNote.title || ""
        }
        if (!sourceTitle && window.currentNote) {
            sourceTitle = window.currentNote.title || ""
        }
        
        // Get source note ID
        if (window.currentNote && window.currentNote.id) {
            sourceNoteId = window.currentNote.id
        } else if (selectedNoteIdBefore) {
            sourceNoteId = selectedNoteIdBefore
        }
        
        var sourceContentLen = sourceContent ? sourceContent.trim().length : 0
        
        console.log(
            "[AIAssistantPanel] runSelectedAction: action_id=" + action.action_id + 
            ", source_note_id=" + sourceNoteId + 
            ", source_title=" + (sourceTitle ? sourceTitle.substring(0, 30) : "(empty)") +
            ", source_content_len=" + sourceContentLen +
            ", selected_note_id_before=" + selectedNoteIdBefore
        )
        
        // Content length validation (minimum 100 chars for summarize)
        var minContentLength = 100
        if (action.action_id === "summarize_note" && sourceContentLen < minContentLength) {
            var errMsg = "현재 문서 본문을 충분히 가져오지 못했습니다. 원본 문서 선택 상태와 에디터 동기화를 확인해 주세요.\n현재 내용 길이: " + sourceContentLen + "자 (최소 필요: " + minContentLength + "자)"
            root.currentAiRunStatus = {
                lastActionName: action.name || action.action_id,
                lastQuestion: userInput,
                lastSuccess: false,
                lastElapsedMs: 0,
                lastResourceText: "",
                lastResultNoteId: "",
                lastResultNoteTitle: "",
                lastErrorMessage: errMsg,
                lastExecutedAt: new Date().toLocaleTimeString()
            }
            console.log(
                "[AIAssistantPanel] runSelectedAction: content too short, source_content_len=" + sourceContentLen +
                ", min required=" + minContentLength
            )
            return
        }
        
        // Step 2: Reset streaming state (but don't create note yet)
        root.currentStreamingNoteId = ""
        root.currentStreamingContent = ""
        root.currentStreamingTitle = ""
        root.currentStreamingIsRag = false
        root.currentRagAnswerText = ""

        // 실행 시작 시간 기록 및 상태 초기화
        root.aiRunStartTime = new Date().getTime()
        root.currentAiRunStatus = {
            lastActionName: action.name || action.action_id,
            lastQuestion: userInput,
            lastSuccess: false,
            lastElapsedMs: 0,
            lastResourceText: "",
            lastResultNoteId: "",
            lastResultNoteTitle: "",
            lastErrorMessage: "",
            lastExecutedAt: ""
        }

        // Step 3: Create AI result note AFTER capturing source
        var outputNoteId = ensureStreamingNote()
        
        var selectedNoteIdAfter = ""
        if (typeof selectedNoteId !== "undefined") {
            selectedNoteIdAfter = selectedNoteId
        }
        
        console.log(
            "[AIAssistantPanel] runSelectedAction: output_note_id=" + outputNoteId + 
            ", selected_note_id_after=" + selectedNoteIdAfter
        )
        
        var currentNoteJson = JSON.stringify({
            note_id: sourceNoteId || "",
            title: sourceTitle || "",
            content: sourceContent || "",
            tags: (window.currentNote && window.currentNote.tags) ? window.currentNote.tags : ""
        })
        
        if (action.action_id === "current_note_qa") {
            if (!sourceContent) {
                root.currentAiRunStatus = {
                    lastActionName: action.name || action.action_id,
                    lastQuestion: userInput,
                    lastSuccess: false,
                    lastElapsedMs: 0,
                    lastResourceText: "",
                    lastResultNoteId: "",
                    lastResultNoteTitle: "",
                    lastErrorMessage: "현재 노트를 선택한 뒤 실행해주세요.",
                    lastExecutedAt: new Date().toLocaleTimeString()
                }
                console.log("[AIAssistantPanel] current_note_qa: no note selected")
                return
            }
            if (!userInput) {
                root.currentAiRunStatus = {
                    lastActionName: action.name || action.action_id,
                    lastQuestion: userInput,
                    lastSuccess: false,
                    lastElapsedMs: 0,
                    lastResourceText: "",
                    lastResultNoteId: "",
                    lastResultNoteTitle: "",
                    lastErrorMessage: "질문 내용을 입력해주세요.",
                    lastExecutedAt: new Date().toLocaleTimeString()
                }
                console.log("[AIAssistantPanel] current_note_qa: no question input")
                return
            }

            console.log(
                "[AIAssistantPanel] current_note_qa: executing via runCustomAction, " +
                "userInput_len=" + userInput.length + ", content_len=" + sourceContentLen
            )

            try {
                ac.runCustomAction(action.action_id, userInput, currentNoteJson, selection, "[]")
            } catch (e) {
                console.log("[AIAssistantPanel] current_note_qa runCustomAction failed: " + e)
                console.log("[AIAssistantPanel] current_note_qa fallback to askQuestion")
                ac.askQuestion(sourceContent, userInput)
            }
        } else if (isDefaultAction(action.action_id)) {
            console.log(
                "[AIAssistantPanel] runTask: action_id=" + action.action_id + 
                ", content_len=" + sourceContentLen
            )
            ac.runTask(action.action_id, sourceContent)
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

    function getAiRagController() {
        return typeof aiRagController !== "undefined" && aiRagController !== null ? aiRagController : null
    }

    function parseJsonArraySafe(jsonText, fallback) {
        if (!jsonText || jsonText === "") return fallback
        try {
            var parsed = JSON.parse(jsonText)
            if (Array.isArray(parsed)) return parsed
            return fallback
        } catch (e) {
            console.warn("[AIAssistantPanel] JSON parse failed: " + e)
            return fallback
        }
    }

    function updateRagCitationsFromController() {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) return
        var json = ragCtrl.getLastCitationsJson()
        root.ragCitations = parseJsonArraySafe(json, [])
        refreshRagStreamingNoteContent()
    }

    function updateRagWarningsFromController() {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) return
        var json = ragCtrl.getLastWarningsJson()
        var warnings = parseJsonArraySafe(json, [])

        var indexResultJson = ragCtrl.getLastIndexResultJson()
        try {
            var indexResult = JSON.parse(indexResultJson)
            if (indexResult && indexResult.warnings && indexResult.warnings.length > 0) {
                for (var i = 0; i < indexResult.warnings.length; i++) {
                    var w = indexResult.warnings[i]
                    if (!w.startsWith("[등록]")) {
                        warnings.push("[등록] " + w)
                    } else {
                        warnings.push(w)
                    }
                }
            }
        } catch (e) {
        }

        root.ragWarnings = warnings
        refreshRagStreamingNoteContent()
    }

    function clearRagState() {
        root.ragCitations = []
        root.ragWarnings = []
        root.currentRagAnswerText = ""
        root.currentStreamingIsRag = false
    }

    function prepareRagIndexingProgress(items, totalCount) {
        var list = []
        if (items && items.length) {
            for (var i = 0; i < items.length && list.length < root.ragIndexingProgressMaxEntries; i++) {
                list.push(items[i])
            }
        }
        root.ragIndexingProgressItems = list
        if (typeof totalCount === "number" && totalCount >= 0) {
            root.ragIndexingProgressTotal = totalCount
        } else {
            root.ragIndexingProgressTotal = list.length
        }
        root.ragIndexingProgressCurrent = 0
    }

    function appendRagIndexingProgressItem(label) {
        if (!label)
            return
        var updated = root.ragIndexingProgressItems.slice()
        updated.push(label)
        if (updated.length > root.ragIndexingProgressMaxEntries) {
            updated = updated.slice(updated.length - root.ragIndexingProgressMaxEntries)
        }
        root.ragIndexingProgressItems = updated
    }

    function clearRagIndexingProgress() {
        root.ragIndexingProgressItems = []
        root.ragIndexingProgressCurrent = 0
        root.ragIndexingProgressTotal = 0
    }

    function applyRagIndexingProgressPayload(payload) {
        if (!payload)
            return
        var data = null
        try {
            data = JSON.parse(payload)
        } catch (e) {
            console.log("[AIAssistantPanel] Failed to parse indexing progress payload", payload)
            return
        }
        if (!data)
            return
        if (typeof data.total === "number" && data.total >= 0) {
            root.ragIndexingProgressTotal = data.total
        }
        if (typeof data.current === "number" && data.current >= 0) {
            root.ragIndexingProgressCurrent = data.current
        }
        if (data.label) {
            appendRagIndexingProgressItem(data.label)
        }
    }

    function buildLabelsFromNotes(notes) {
        var labels = []
        if (!notes || !notes.length)
            return labels
        for (var i = 0; i < notes.length; i++) {
            var note = notes[i] || {}
            var label = note.title || note.note_id || note.id || "제목 없음"
            labels.push(label)
            if (labels.length >= root.ragIndexingProgressMaxEntries)
                break
        }
        return labels
    }

    function buildLabelsFromPaths(paths) {
        var labels = []
        if (!paths || !paths.length)
            return labels
        for (var i = 0; i < paths.length; i++) {
            var path = paths[i]
            if (Array.isArray(path))
                path = path[0]
            if (typeof path !== "string")
                path = String(path)
            if (path.lastIndexOf("/") >= 0)
                path = path.substring(path.lastIndexOf("/") + 1)
            if (path.lastIndexOf("\\") >= 0)
                path = path.substring(path.lastIndexOf("\\") + 1)
            labels.push(path)
            if (labels.length >= root.ragIndexingProgressMaxEntries)
                break
        }
        return labels
    }

    // RAG 인덱스 초기화 후 등록 (replace 모드)
    function clearRagIndexAndRegister(registerFn) {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) {
            root.ragRunStatus = {
                lastQuestion: "",
                lastSuccess: false,
                lastElapsedMs: 0,
                lastResourceText: "",
                lastResultNoteId: "",
                lastResultNoteTitle: "",
                lastErrorMessage: "RAG 컨트롤러를 사용할 수 없습니다",
                lastExecutedAt: new Date().toLocaleTimeString()
            }
            return false
        }

        // 기존 인덱스 초기화 (실제 노트/문서는 삭제되지 않음)
        console.log("[AIAssistantPanel] Clearing RAG index for replace mode")
        ragCtrl.clearIndex()
        clearRagTargetDocuments()

        // 등록 함수 실행
        registerFn()
        return true
    }

    function indexCurrentNoteForRag() {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) {
            root.ragRunStatus = {
                lastQuestion: "",
                lastSuccess: false,
                lastElapsedMs: 0,
                lastResourceText: "",
                lastResultNoteId: "",
                lastResultNoteTitle: "",
                lastErrorMessage: "RAG 컨트롤러를 사용할 수 없습니다",
                lastExecutedAt: new Date().toLocaleTimeString()
            }
            return
        }

        if (!window.currentNote || !window.currentNote.id) {
            root.ragRunStatus = {
                lastQuestion: "",
                lastSuccess: false,
                lastElapsedMs: 0,
                lastResourceText: "",
                lastResultNoteId: "",
                lastResultNoteTitle: "",
                lastErrorMessage: "현재 노트가 없습니다",
                lastExecutedAt: new Date().toLocaleTimeString()
            }
            return
        }

        if (root.ragIndexingRunning || root.ragRequestRunning) {
            root.ragRunStatus = {
                lastQuestion: "",
                lastSuccess: false,
                lastElapsedMs: 0,
                lastResourceText: "",
                lastResultNoteId: "",
                lastResultNoteTitle: "",
                lastErrorMessage: "현재 작업이 진행 중입니다",
                lastExecutedAt: new Date().toLocaleTimeString()
            }
            return
        }

        var note = window.currentNote
        var tagsJson = "[]"
        if (note.tags && Array.isArray(note.tags)) {
            tagsJson = JSON.stringify(note.tags)
        }

        clearRagState()
        prepareRagIndexingProgress([note.title || note.id || "제목 없음"], 1)
        root.ragIndexingRunning = true

        console.log("[AIAssistantPanel] Indexing current note (replace mode): id=" + note.id)
        ragCtrl.indexCurrentNote(note.id, note.title || "", note.content || "", tagsJson)
    }

    function askIndexedDocuments(questionText) {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) {
            root.ragRunStatus = {
                lastQuestion: questionText || "",
                lastSuccess: false,
                lastElapsedMs: 0,
                lastResourceText: "",
                lastResultNoteId: "",
                lastResultNoteTitle: "",
                lastErrorMessage: "RAG 컨트롤러를 사용할 수 없습니다",
                lastExecutedAt: new Date().toLocaleTimeString()
            }
            return
        }

        var question = questionText || actionInput.text || ""
        if (!question) {
            root.ragRunStatus = {
                lastQuestion: "",
                lastSuccess: false,
                lastElapsedMs: 0,
                lastResourceText: "",
                lastResultNoteId: "",
                lastResultNoteTitle: "",
                lastErrorMessage: "질문 내용을 입력해주세요.",
                lastExecutedAt: new Date().toLocaleTimeString()
            }
            return
        }

        root.lastAskedQuestion = question

        // RAG 실행 시작 시간 기록 및 상태 초기화
        root.ragRunStartTime = new Date().getTime()
        root.ragRunStatus = {
            lastQuestion: question,
            lastSuccess: false,
            lastElapsedMs: 0,
            lastResourceText: "",
            lastResultNoteId: "",
            lastResultNoteTitle: "",
            lastErrorMessage: "",
            lastExecutedAt: ""
        }

        clearRagState()
        root.currentStreamingIsRag = true
        root.currentRagAnswerText = ""

        // Reset and prepare streaming note immediately
        root.currentStreamingNoteId = ""
        root.currentStreamingContent = ""
        root.currentStreamingTitle = "RAG 답변: " + question
        ensureStreamingNote()
        root.ragRequestRunning = true
        console.log("[AIAssistantPanel] [TIMING] RAG request START, ragRequestRunning=true")

        console.log("[AIAssistantPanel] Asking indexed documents: question=" + question)
        ragCtrl.askIndexedDocuments(question)
    }

    function getNoteController() {
        return typeof noteController !== "undefined" && noteController !== null ? noteController : null
    }

    function getFolderController() {
        return typeof folderController !== "undefined" && folderController !== null ? folderController : null
    }

    function indexCurrentFolderForRag() {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) {
            console.log("[AIAssistantPanel] RAG 컨트롤러 오류")
            return
        }

        var folderCtrl = getFolderController()
        if (!folderCtrl) {
            console.log("[AIAssistantPanel] 폴더 컨트롤러 오류")
            return
        }

        var currentFolderId = folderCtrl.currentFolderId
        if (!currentFolderId) {
            console.log("[AIAssistantPanel] 현재 폴더 미선택")
            return
        }

        if (root.ragIndexingRunning || root.ragRequestRunning) {
            console.log("[AIAssistantPanel] 현재 작업 진행 중")
            return
        }

        // 기존 인덱스 초기화 (replace 모드)
        console.log("[AIAssistantPanel] Clearing RAG index for replace mode (folder)")
        ragCtrl.clearIndex()
        clearRagTargetDocuments()

        clearRagState()
        prepareRagIndexingProgress([], 0)
        root.ragIndexingRunning = true
        console.log("[AIAssistantPanel] 참고문서 등록 중...")

        try {
            var descendantIds = folderCtrl.getDescendantIds(currentFolderId)
            var folderIds = [currentFolderId].concat(descendantIds || [])
            var notesJson = noteController.getNotesForRagByFolderIdsJson(JSON.stringify(folderIds))
            var notes = JSON.parse(notesJson)
            prepareRagIndexingProgress(buildLabelsFromNotes(notes), notes.length)
            console.log("[AIAssistantPanel] Indexing folder (replace mode): " + currentFolderId + ", notes count: " + notes.length)
            ragCtrl.indexCurrentFolderNotes(notesJson, currentFolderId)
        } catch (e) {
            root.ragIndexingRunning = false
            clearRagIndexingProgress()
            console.log("[AIAssistantPanel] 참고문서 등록 실패: " + e)
        }
    }

    function indexAllNotesForRag() {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) {
            console.log("[AIAssistantPanel] RAG 컨트롤러 오류")
            return
        }

        var noteCtrl = getNoteController()
        if (!noteCtrl) {
            console.log("[AIAssistantPanel] 노트 컨트롤러 오류")
            return
        }

        if (root.ragIndexingRunning || root.ragRequestRunning) {
            console.log("[AIAssistantPanel] 현재 작업 진행 중")
            return
        }

        // 기존 인덱스 초기화 (replace 모드)
        console.log("[AIAssistantPanel] Clearing RAG index for replace mode (all notes)")
        ragCtrl.clearIndex()
        clearRagTargetDocuments()

        clearRagState()
        prepareRagIndexingProgress([], 0)
        root.ragIndexingRunning = true
        console.log("[AIAssistantPanel] 참고문서 등록 중...")

        try {
            var notesJson = noteCtrl.getAllNotesForRagJson()
            var notes = JSON.parse(notesJson)
            prepareRagIndexingProgress(buildLabelsFromNotes(notes), notes.length)
            console.log("[AIAssistantPanel] Indexing all notes (replace mode), count: " + notes.length)
            ragCtrl.indexAllNotesJson(notesJson)
        } catch (e) {
            root.ragIndexingRunning = false
            clearRagIndexingProgress()
            console.log("[AIAssistantPanel] 참고문서 등록 실패: " + e)
        }
    }

    function updateLastIndexResultFromController() {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) return null
        try {
            return JSON.parse(ragCtrl.getLastIndexResultJson())
        } catch (e) {
            return null
        }
    }

    function formatIndexResultMessage(result, label) {
        if (!result) return label + " 등록 결과"
        var msg = label + " 등록 완료: " + result.indexed_count + "개 성공"
        if (result.failed_count > 0) {
            msg += ", " + result.failed_count + "개 실패"
        }
        return msg
    }

    function copyTextToClipboard(text) {
        if (!text) return false
        try {
            if (typeof Qt !== "undefined" && Qt.application && Qt.application.clipboard) {
                Qt.application.clipboard.setText(text)
                return true
            }
        } catch (e) {
            console.warn("[AIAssistantPanel] Clipboard copy failed: " + e)
        }
        return false
    }

    function formatSourcePath(path) {
        if (!path) return ""
        if (path.length <= 50) return path
        var parts = path.split(/[/\\]/)
        if (parts.length <= 3) return path
        return parts[0] + "/.../" + parts.slice(-2).join("/")
    }

    function formatRagWarningMessage(warningText) {
        if (!warningText) return ""
        if (warningText.startsWith("[등록]")) return warningText

        if (warningText.startsWith("[OLLAMA_CONNECTION_FAILED]")) {
            return "Ollama 연결 실패: Ollama 실행 상태와 모델 설치 여부를 확인해 주세요. (" + warningText + ")"
        }
        if (warningText.startsWith("[OLLAMA_TIMEOUT]")) {
            return "Ollama 응답 시간 초과: 더 작은 모델을 사용하거나 다시 시도해 주세요. (" + warningText + ")"
        }
        if (warningText.startsWith("[OLLAMA_EMPTY_RESPONSE]")) {
            return "Ollama가 빈 응답을 반환했습니다. 모델 상태를 확인해 주세요. (" + warningText + ")"
        }
        if (warningText.startsWith("[OLLAMA_INVALID_JSON]")) {
            return "Ollama 응답을 해석하지 못했습니다. (" + warningText + ")"
        }
        if (warningText.startsWith("[OLLAMA_GENERATE_FAILED]")) {
            return "Ollama 답변 생성 중 오류가 발생했습니다. (" + warningText + ")"
        }
        if (warningText.startsWith("[OLLAMA_HTTP_ERROR]")) {
            return "Ollama HTTP 오류가 발생했습니다. (" + warningText + ")"
        }
        if (warningText.startsWith("[HWPX_FILE_NOT_FOUND]")) {
            return "HWPX 파일을 찾을 수 없습니다. (" + warningText + ")"
        }
        if (warningText.startsWith("[HWPX_BROKEN_ZIP]")) {
            return "HWPX 파일이 손상되었습니다. (" + warningText + ")"
        }
        if (warningText.startsWith("[HWPX_CONVERSION_EMPTY]")) {
            return "HWPX 변환 결과가 비어 있습니다. (" + warningText + ")"
        }
        return warningText
    }

    function formatRagCitationLine(citation) {
        if (!citation)
            return ""

        var headingSuffix = ""
        if (citation.heading_path && citation.heading_path.length > 0) {
            headingSuffix = " > " + citation.heading_path.join(" > ")
        }

        var detailParts = []
        if (citation.source_type)
            detailParts.push(citation.source_type)
        if (citation.note_id) {
            detailParts.push("note_id: " + citation.note_id)
        } else if (citation.source_path) {
            detailParts.push("path: " + formatSourcePath(citation.source_path))
        }
        if (citation.cited_in_answer)
            detailParts.push("답변에 인용")

        var detailText = detailParts.length > 0 ? " (" + detailParts.join(" · ") + ")" : ""
        var linkText = ""
        if (citation.note_id) {
            linkText = " [노트 열기](https://note.local/open/" + citation.note_id + ")"
        }
        return "- " + (citation.title || "제목 없음") + headingSuffix + detailText + linkText
    }

    function buildRagCitationsSection() {
        if (!root.ragCitations || root.ragCitations.length === 0)
            return ""

        var lines = ["## 근거 문서"]
        for (var i = 0; i < root.ragCitations.length; i++) {
            lines.push(formatRagCitationLine(root.ragCitations[i]))
        }
        return lines.join("\n")
    }

    function buildRagWarningsSection() {
        if (!root.ragWarnings || root.ragWarnings.length === 0)
            return ""

        var lines = ["## 경고"]
        for (var i = 0; i < root.ragWarnings.length; i++) {
            lines.push("- " + formatRagWarningMessage(root.ragWarnings[i]))
        }
        return lines.join("\n")
    }

    function buildRagAnswerBody() {
        var sections = []
        if (root.currentRagAnswerText && root.currentRagAnswerText !== "")
            sections.push(root.currentRagAnswerText)

        var citationsSection = buildRagCitationsSection()
        if (citationsSection !== "")
            sections.push(citationsSection)

        var warningsSection = buildRagWarningsSection()
        if (warningsSection !== "")
            sections.push(warningsSection)

        return sections.join("\n\n---\n\n")
    }

    function refreshRagStreamingNoteContent() {
        if (!root.currentStreamingIsRag)
            return
        if (!root.currentStreamingNoteId || root.currentStreamingNoteId === "")
            return
        if (!root.currentRagAnswerText || root.currentRagAnswerText === "")
            return

        var body = buildRagAnswerBody()
        if (!body || body.trim() === "")
            return

        updateStreamingNote(body, false)
    }

    function ensureStreamingNote() {
        if (root.currentStreamingNoteId !== "") {
            console.log("[AIAssistantPanel] ensureStreamingNote: returning existing noteId=" + root.currentStreamingNoteId)
            return root.currentStreamingNoteId
        }

        var ac = getAssistantController()
        if (!ac) {
            console.log("[AIAssistantPanel] ensureStreamingNote: no assistantController")
            return ""
        }

        var now = new Date()
        var dateStr = now.getFullYear() + "." +
                      String(now.getMonth() + 1).padStart(2, "0") + "." +
                      String(now.getDate()).padStart(2, "0") + " " +
                      String(now.getHours()).padStart(2, "0") + ":" +
                      String(now.getMinutes()).padStart(2, "0")

        var aiMode = root.aiModeIndex === 1 ? "참고문서AI" : "현재문서AI"
        var question = root.lastAskedQuestion || ""
        var title = "AI결과 (" + dateStr + ")"
        
        root.currentStreamingTitle = title
        root.currentStreamingContent = title + "\n" + aiMode + "\n" + question + "\n"
        
        console.log("[AIAssistantPanel] ensureStreamingNote: creating new note, title=" + title)
        var folderId = ac.getOrCreateAIResultFolder()
        console.log("[AIAssistantPanel] ensureStreamingNote: folderId=" + folderId)
        var noteId = ac.createNewNote(title, root.currentStreamingContent, folderId)
        console.log("[AIAssistantPanel] ensureStreamingNote: created noteId=" + noteId)
        
        if (noteId) {
            root.currentStreamingNoteId = noteId
            if (!root.currentStreamingIsRag) {
                console.log("[AIAssistantPanel] AI 결과를 노트에 저장 중: " + title)
            }
            
            // Open the note in the editor
            console.log("[AIAssistantPanel] ensureStreamingNote: opening note in editor, selectedNoteId=" + noteId)
            if (typeof selectedNoteId !== "undefined") {
                selectedNoteId = noteId
            }
        }
        
        return noteId
    }

    function updateStreamingNote(newText, isAppend) {
        var noteId = ensureStreamingNote()
        console.log("[AIAssistantPanel] updateStreamingNote: noteId=" + noteId + ", isAppend=" + isAppend + ", textLen=" + newText.length)
        if (!noteId) {
            console.log("[AIAssistantPanel] updateStreamingNote: no noteId, skipping save")
            return
        }

        if (isAppend) {
            root.currentStreamingContent += newText
        } else {
            // If it's a full replacement (like RAG answer), keep the header
            var aiMode = root.aiModeIndex === 1 ? "참고문서AI" : "현재문서AI"
            var question = root.lastAskedQuestion || ""
            root.currentStreamingContent = root.currentStreamingTitle + "\n" + aiMode + "\n" + question + "\n" + newText
        }

        var nc = getNoteController()
        if (nc) {
            console.log("[AIAssistantPanel] updateStreamingNote: calling nc.updateNote, contentLen=" + root.currentStreamingContent.length)
            nc.updateNote(noteId, root.currentStreamingTitle, root.currentStreamingContent)
            
            // Also update current note cache by reassignment so bindings are notified.
            if (typeof window !== "undefined" && window.currentNote && window.selectedNoteId === noteId) {
                console.log("[AIAssistantPanel] updateStreamingNote: refreshing window.currentNote binding")
                window.currentNote = {
                    id: window.currentNote.id || noteId,
                    title: root.currentStreamingTitle,
                    content: root.currentStreamingContent,
                    content_json: window.currentNote.content_json || "",
                    tags: window.currentNote.tags || ""
                }
            }
            
            // Force WebNoteEditor to refresh immediately for live streaming visibility.
            if (root.noteEditorRef && typeof window !== "undefined" && window.selectedNoteId === noteId) {
                if (typeof root.noteEditorRef.applyLiveMarkdown === "function") {
                    console.log("[AIAssistantPanel] updateStreamingNote: forcing noteEditorRef.applyLiveMarkdown")
                    root.noteEditorRef.applyLiveMarkdown(root.currentStreamingContent)
                } else if (typeof root.noteEditorRef.setEditorContent === "function") {
                    console.log("[AIAssistantPanel] updateStreamingNote: fallback noteEditorRef.setEditorContent")
                    root.noteEditorRef.setEditorContent(root.currentStreamingContent, "")
                }
            }
        } else {
            console.log("[AIAssistantPanel] updateStreamingNote: no noteController")
        }
    }

    function fileUrlToLocalPath(fileUrl) {
        if (!fileUrl) return ""
        var path = fileUrl
        if (Array.isArray(fileUrl)) {
            path = fileUrl[0] || ""
        }
        if (typeof path !== "string") {
            path = String(path)
        }
        if (path.startsWith("file:///")) {
            path = path.substring(8)
        } else if (path.startsWith("file://")) {
            path = path.substring(7)
        } else if (path.startsWith("file:/")) {
            path = path.substring(5)
        }
        try {
            path = decodeURIComponent(path)
        } catch (e) {
        }
        return path
    }

    function indexExternalFilesForRag(paths) {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) {
            console.log("[AIAssistantPanel] RAG 컨트롤러 오류")
            return
        }

        if (!paths || paths.length === 0) {
            console.log("[AIAssistantPanel] 선택된 파일 없음")
            return
        }

        if (root.ragIndexingRunning || root.ragRequestRunning) {
            console.log("[AIAssistantPanel] 현재 작업 진행 중")
            return
        }

        // 기존 인덱스 초기화 (replace 모드)
        console.log("[AIAssistantPanel] Clearing RAG index for replace mode (external files)")
        ragCtrl.clearIndex()
        clearRagTargetDocuments()

        clearRagState()
        prepareRagIndexingProgress(buildLabelsFromPaths(paths), paths.length)
        root.ragIndexingRunning = true
        console.log("[AIAssistantPanel] 참고문서 등록 중...")

        try {
            var pathsJson = JSON.stringify(paths)
            console.log("[AIAssistantPanel] Indexing external files (replace mode): " + paths.length + " files")
            ragCtrl.indexExternalFilesJson(pathsJson)
        } catch (e) {
            root.ragIndexingRunning = false
            clearRagIndexingProgress()
            console.log("[AIAssistantPanel] 참고문서 등록 실패: " + e)
        }
    }

    function indexExternalFolderForRag(folderPath) {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) {
            console.log("[AIAssistantPanel] RAG 컨트롤러 오류")
            return
        }

        if (!folderPath) {
            console.log("[AIAssistantPanel] 선택된 폴더 없음")
            return
        }

        if (root.ragIndexingRunning || root.ragRequestRunning) {
            console.log("[AIAssistantPanel] 현재 작업 진행 중")
            return
        }

        // 기존 인덱스 초기화 (replace 모드)
        console.log("[AIAssistantPanel] Clearing RAG index for replace mode (external folder)")
        ragCtrl.clearIndex()
        clearRagTargetDocuments()

        clearRagState()
        prepareRagIndexingProgress([folderPath], 0)
        root.ragIndexingRunning = true
        console.log("[AIAssistantPanel] 참고문서 등록 중...")

        try {
            console.log("[AIAssistantPanel] Indexing external folder (replace mode): " + folderPath)
            ragCtrl.indexExternalFolder(folderPath)
        } catch (e) {
            root.ragIndexingRunning = false
            clearRagIndexingProgress()
            console.log("[AIAssistantPanel] 참고문서 등록 실패: " + e)
        }
    }

    Component.onCompleted: {
        console.log("[AIAssistantPanel][DIAG] loaded qml/components/AIAssistantPanel.qml")
        console.log("[AIAssistantPanel][DIAG] aiModeIndex =", root.aiModeIndex)
        var ac = getAssistantController()
        if (!ac)
            return

        root.aiRunning = ac.isRunning

        ac.tokenReceived.connect(function(token) {
            console.log("[AIAssistantPanel] Token received: length=" + token.length + ", currentStreamingContent.length=" + root.currentStreamingContent.length)
            updateStreamingNote(token, true)
        })

        ac.resultReady.connect(function(result) {
            console.log("[AIAssistantPanel] Result ready: length=" + result.length)
            if (result && result !== "") {
                updateStreamingNote(result, false)
            }
        })

        ac.runningChanged.connect(function(running) {
            root.aiRunning = running
            if (!running) {
                console.log("[AIAssistantPanel] Task finished, currentStreamingContent.length=" + root.currentStreamingContent.length)

                // Check if response is empty
                var isTrulyEmpty = (root.currentStreamingContent.indexOf(root.currentStreamingTitle) === 0 &&
                                   root.currentStreamingContent.length <= root.currentStreamingTitle.length + 20)

                if (root.currentStreamingNoteId !== "") {
                    if (isTrulyEmpty) {
                        console.log("[AIAssistantPanel] AI 답변 생성 실패")
                        updateStreamingNote("\n\n[오류] AI 응답이 비어 있습니다. 모델이 질문을 이해하지 못했거나 토큰 제한에 걸렸을 수 있습니다.", true)
                        // 상태 업데이트: 실패
                        updateCurrentAiStatus(false, root.currentStreamingNoteId, root.currentStreamingTitle, "AI 응답이 비어 있습니다")
                    } else {
                        console.log("[AIAssistantPanel] 모든 결과가 노트에 저장되었습니다.")
                        // 상태 업데이트: 성공
                        updateCurrentAiStatus(true, root.currentStreamingNoteId, root.currentStreamingTitle, "")
                    }
                }
            }
        })

        ac.errorOccurred.connect(function(error) {
            if (root.currentStreamingNoteId !== "") {
                updateStreamingNote("\n[오류] " + error, true)
                // 상태 업데이트: 실패
                updateCurrentAiStatus(false, root.currentStreamingNoteId, root.currentStreamingTitle, error)
            } else {
                console.log("[AIAssistantPanel] AI 오류: " + error)
                // 상태 업데이트: 실패 (노트 미생성)
                updateCurrentAiStatus(false, "", "", error)
            }
        })

        root.loadActionSelectionOrder()
        root.refreshActionList()
        root.ensureActionSelection()

        // Connect aiRagController signals
        var ragCtrl = getAiRagController()
        console.log("[AIAssistantPanel] RAG controller check:", ragCtrl ? "exists" : "null")
        if (ragCtrl) {
            console.log("[AIAssistantPanel] Connecting RAG signals...")
            ragCtrl.ragAnswerReady.connect(function(answerText) {
                console.log("[AIAssistantPanel] RAG answer received: len=" + answerText.length)
                root.ragRequestRunning = false
                if (root.currentStreamingIsRag) {
                    root.currentRagAnswerText = answerText || ""
                    refreshRagStreamingNoteContent()
                } else {
                    updateStreamingNote(answerText, false)
                }
                updateRagCitationsFromController()
                updateRagWarningsFromController()
                // 상태 업데이트: 성공
                updateRagRunStatus(true, root.currentStreamingNoteId, root.currentStreamingTitle, "")
            })

            ragCtrl.ragCitationsChanged.connect(function() {
                updateRagCitationsFromController()
                var ragCtrl2 = getAiRagController()
                if (ragCtrl2) {
                    var citationsJson = ragCtrl2.getLastCitationsJson()
                    console.log("[AIAssistantPanel] RAG citations: " + citationsJson)
                }
            })

            ragCtrl.ragWarningsChanged.connect(function() {
                updateRagWarningsFromController()
                var ragCtrl2 = getAiRagController()
                if (ragCtrl2) {
                    var warningsJson = ragCtrl2.getLastWarningsJson()
                    console.log("[AIAssistantPanel] RAG warnings: " + warningsJson)
                }
            })

            ragCtrl.indexingProgressChanged.connect(function(payload) {
                applyRagIndexingProgressPayload(payload)
            })

            ragCtrl.indexStatusChanged.connect(function(status) {
                console.log("[AIAssistantPanel] RAG index status: " + status)
                root.ragIndexingRunning = false
                clearRagIndexingProgress()
                if (status === "indexed_current_note") {
                    console.log("[AIAssistantPanel] 현재 문서 등록 완료")
                } else if (status === "indexed_folder") {
                    var result = updateLastIndexResultFromController()
                    console.log("[AIAssistantPanel] 현재 폴더 등록 완료: " + formatIndexResultMessage(result, "현재 폴더"))
                } else if (status === "indexed_all_notes") {
                    var result = updateLastIndexResultFromController()
                    console.log("[AIAssistantPanel] 전체 노트 등록 완료: " + formatIndexResultMessage(result, "전체 노트"))
                } else if (status === "indexed_notes") {
                    var result = updateLastIndexResultFromController()
                    console.log("[AIAssistantPanel] 노트 등록 완료: " + formatIndexResultMessage(result, "노트"))
                } else if (status === "indexed_external_files") {
                    var result = updateLastIndexResultFromController()
                    console.log("[AIAssistantPanel] 외부 문서 등록 완료: " + formatIndexResultMessage(result, "외부 문서"))
                } else if (status === "indexed_empty") {
                    console.log("[AIAssistantPanel] 등록할 노트 없음")
                } else if (status === "cleared") {
                    console.log("[AIAssistantPanel] 참고문서 등록 초기화됨")
                    clearRagState()
                }

                var shouldRefreshList = [
                    "indexed_current_note",
                    "indexed_folder",
                    "indexed_all_notes",
                    "indexed_notes",
                    "indexed_external_files",
                    "indexed_external_folder",
                    "indexed_empty",
                    "cleared",
                    "ready"
                ].indexOf(status) >= 0
                if (shouldRefreshList) {
                    refreshRagTargetDocumentsFromIndex()
                }
            })

            ragCtrl.errorOccurred.connect(function(error) {
                root.ragRequestRunning = false
                root.ragIndexingRunning = false
                clearRagIndexingProgress()
                console.log("[AIAssistantPanel] RAG 오류: " + error)
                // 상태 업데이트: 실패
                updateRagRunStatus(false, root.currentStreamingNoteId, root.currentStreamingTitle, error)
            })

            refreshRagTargetDocumentsFromIndex()
        }
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

        Column {
            id: headerArea
            Layout.fillWidth: true
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

            RowLayout {
                width: parent.width
                spacing: Metrics.xs

                Button {
                    id: currentDocTabButton
                    Layout.fillWidth: true
                    height: 32
                    focusPolicy: Qt.NoFocus
                    onClicked: setAiMode(0, "currentTab")
                    background: Rectangle {
                        radius: Metrics.radiusSm
                        color: root.aiModeIndex === 0 ? Colors.primary500 : Colors.bgSecondary
                        border.color: root.aiModeIndex === 0 ? Colors.primary500 : Colors.borderLight
                        border.width: 1
                    }
                    contentItem: Text {
                        anchors.centerIn: parent
                        text: "현재 문서 AI"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.caption
                        font.weight: root.aiModeIndex === 0 ? Typography.weightMedium : Typography.weightRegular
                        color: root.aiModeIndex === 0 ? Colors.white : Colors.textSecondary
                    }
                }

                Button {
                    id: referenceDocTabButton
                    Layout.fillWidth: true
                    height: 32
                    focusPolicy: Qt.NoFocus
                    onClicked: setAiMode(1, "referenceTab")
                    background: Rectangle {
                        radius: Metrics.radiusSm
                        color: root.aiModeIndex === 1 ? Colors.primary500 : Colors.bgSecondary
                        border.color: root.aiModeIndex === 1 ? Colors.primary500 : Colors.borderLight
                        border.width: 1
                    }
                    contentItem: Text {
                        anchors.centerIn: parent
                        text: "참고문서 AI"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.caption
                        font.weight: root.aiModeIndex === 1 ? Typography.weightMedium : Typography.weightRegular
                        color: root.aiModeIndex === 1 ? Colors.white : Colors.textSecondary
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

        ScrollView {
            id: tabScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ScrollBar.vertical.policy: ScrollBar.AsNeeded

            Column {
                width: tabScroll.width
                spacing: Metrics.lg

                Column {
                    id: tabContentColumn
                    width: parent.width
                    spacing: Metrics.lg

                    Rectangle {
                        width: parent.width
                        radius: Metrics.radiusLg
                        color: Colors.surface
                        border.color: Colors.borderLight
                        implicitHeight: quickActionsColumn.implicitHeight + (Metrics.md * 2)
                        visible: root.aiModeIndex === 0
                        height: visible ? implicitHeight : 0

                        Column {
                            id: quickActionsColumn
                            width: parent.width - (Metrics.md * 2)
                            spacing: Metrics.sm
                            anchors.top: parent.top
                            anchors.topMargin: Metrics.md
                            anchors.horizontalCenter: parent.horizontalCenter

                            Text {
                                text: "AI 기능 선택"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textPrimary
                            }

                            Rectangle {
                                width: parent.width
                                height: 200
                                implicitHeight: 200
                                color: "transparent"
                                clip: true

                                ListView {
                                    id: categoryFolderView
                                    width: parent.width
                                    height: parent.height
                                    spacing: Metrics.xs
                                    model: root.categoryList
                                    boundsBehavior: Flickable.StopAtBounds
                                    ScrollBar.vertical: ScrollBar {
                                        policy: ScrollBar.AsNeeded
                                    }

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

                                                Image {
                                                    source: "../assets/icons/AIfolder.png"
                                                    Layout.preferredWidth: 16
                                                    Layout.preferredHeight: 16
                                                    fillMode: Image.PreserveAspectFit
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
                                                    text: {
                                                        root.favoriteVersion
                                                        return root.filterActionsByCategory(categoryDelegate.categoryName).length
                                                    }
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
                                                model: {
                                                    root.favoriteVersion
                                                    return root.orderedActionsByCategory(categoryDelegate.categoryName)
                                                }

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

                                                        Image {
                                                            source: "../assets/icons/AIfeatures.png"
                                                            Layout.preferredWidth: 14
                                                            Layout.preferredHeight: 14
                                                            fillMode: Image.PreserveAspectFit
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
                                                            text: (root.favoriteActions.indexOf(modelData.action_id) >= 0) ? "★" : "☆"
                                                            font.pixelSize: 14
                                                            color: (root.favoriteActions.indexOf(modelData.action_id) >= 0) ? Colors.warning : Colors.textTertiary
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
                            }
                            }

                            Text {
                                visible: root.categoryList.length === 0
                                width: parent.width
                                text: "사용 가능한 AI 기능이 없습니다."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.textSecondary
                                horizontalAlignment: Text.AlignHCenter
                            }

                            Rectangle {
                                width: parent.width
                                height: 60
                                radius: Metrics.radiusMd
                                color: Colors.bgSecondary
                                border.color: Colors.borderLight
                                border.width: 1

                                Column {
                                    width: parent.width - (Metrics.md * 2)
                                    anchors.centerIn: parent
                                    spacing: Metrics.xs

                                    Text {
                                        width: parent.width
                                        text: (typeof root.selectedAction !== 'undefined' && root.selectedAction) ? (root.selectedAction.name || root.selectedAction.action_id || "") : "원하는 AI 기능을 선택하세요"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.bodyRegular
                                        font.weight: Font.Bold
                                        color: Colors.textPrimary
                                        horizontalAlignment: Text.AlignHCenter
                                    }

                                    Text {
                                        width: parent.width
                                        visible: typeof root.selectedAction !== 'undefined' && root.selectedAction && typeof root.selectedAction.description !== 'undefined' && root.selectedAction.description !== ""
                                        text: (typeof root.selectedAction !== 'undefined' && root.selectedAction) ? (root.selectedAction.description || "") : ""
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        color: Colors.textSecondary
                                        wrapMode: Text.Wrap
                                        horizontalAlignment: Text.AlignHCenter
                                    }
                                }
                            }

                            TextField {
                                id: actionInput
                                width: parent.width
                                height: 36
                                placeholderText: root.selectedAction ? (root.selectedAction.action_id === "current_note_qa" ? "현재 문서에 대해 질문하세요." : getInputModePlaceholder(root.selectedAction.input_mode)) : "AI 기능을 선택하세요"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                enabled: canUseAI() && !root.aiRunning
                            }

                            RowLayout {
                                width: parent.width
                                height: 36
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
                                                console.log("[AIAssistantPanel] 작업 취소됨")
                                            }
                                        } else {
                                            runSelectedAction()
                                        }
                                    }
                                }
                            }
                        }

                    }

                    // 현재문서 AI 프롬프트 미리보기 (메인 섹션 하단)
                    Rectangle {
                        width: parent.width
                        radius: Metrics.radiusMd
                        color: Colors.surface
                        border.color: Colors.borderLight
                        border.width: 1
                        implicitHeight: promptPreviewColumn.implicitHeight + (Metrics.sm * 2)
                        visible: root.aiModeIndex === 0
                        height: visible ? implicitHeight : 0

                        Column {
                            id: promptPreviewColumn
                            width: parent.width - (Metrics.sm * 2)
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.margins: Metrics.sm
                            spacing: Metrics.xs

                            Text {
                                text: "프롬프트 미리보기"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            Text {
                                text: (typeof root.selectedAction !== 'undefined' && root.selectedAction && root.selectedAction.current_prompt && root.selectedAction.current_prompt.title) ?
                                      root.selectedAction.current_prompt.title :
                                      "연결된 프롬프트 노트가 없습니다."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                font.weight: Font.Bold
                                color: Colors.textPrimary
                                visible: typeof root.selectedAction !== 'undefined' && root.selectedAction && typeof root.selectedAction.current_prompt !== 'undefined'
                            }

                            ScrollView {
                                width: parent.width
                                height: 80
                                clip: true
                                ScrollBar.vertical.policy: ScrollBar.AsNeeded
                                visible: typeof root.selectedAction !== 'undefined' && root.selectedAction && typeof root.selectedAction.current_prompt !== 'undefined' && typeof root.selectedAction.current_prompt.content_md !== 'undefined'

                                Text {
                                    text: (typeof root.selectedAction !== 'undefined' && root.selectedAction) ? ((typeof root.selectedAction.current_prompt !== 'undefined' && root.selectedAction.current_prompt) ? root.selectedAction.current_prompt.content_md : "") : ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: 10
                                    color: Colors.textSecondary
                                    wrapMode: Text.Wrap
                                    width: parent.width
                                }
                            }

                            Text {
                                text: "연결된 프롬프트 노트가 없습니다."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.textTertiary
                                horizontalAlignment: Text.AlignHCenter
                                width: parent.width
                                visible: !root.selectedAction || !root.selectedAction.current_prompt
                            }
                        }
                    }

                    Rectangle {
                        id: referenceDocsTab
                        objectName: "referenceDocsTab"
                        width: parent.width
                        radius: Metrics.radiusLg
                        color: Colors.surface
                        border.color: Colors.borderLight
                        implicitHeight: referenceDocsCardColumn.implicitHeight + (Metrics.md * 2)
                        visible: root.aiModeIndex === 1
                        height: visible ? implicitHeight : 0

                        Column {
                            id: referenceDocsCardColumn
                            width: parent.width - (Metrics.md * 2)
                            spacing: Metrics.sm
                            anchors.centerIn: parent

                            Text {
                                text: "참고문서 AI"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodyRegular
                                font.weight: Typography.weightSemibold
                                color: Colors.textPrimary
                            }

                            Text {
                                width: parent.width
                                text: "등록한 문서는 AI가 여러 문서에서 찾아 답변할 때 참고합니다."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: Colors.textSecondary
                                wrapMode: Text.WordWrap
                            }

                            Rectangle {
                                width: parent.width
                                height: 1
                                color: Colors.borderLight
                            }

                            Column {
                                width: parent.width
                                spacing: Metrics.xs

                                Text {
                                    text: "현재 문서 질문: 지금 열려 있는 문서 하나만 참고합니다."
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.textTertiary
                                }

                                Text {
                                    text: "등록된 문서 질문: 등록된 여러 문서에서 관련 내용을 찾아 답변합니다."
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.textTertiary
                                }
                            }

                            Rectangle {
                                width: parent.width
                                height: 1
                                color: Colors.borderLight
                            }

                            Text {
                                text: "참고문서 등록"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textPrimary
                            }

                            GridLayout {
                                width: parent.width
                                columns: 3
                                rows: 2
                                rowSpacing: Metrics.sm
                                columnSpacing: Metrics.sm

                                Button {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 32
                                    text: "현재 문서 등록"
                                    enabled: canUseAI() && !root.ragIndexingRunning && !root.ragRequestRunning
                                    contentItem: Text {
                                        text: parent.text
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                        color: parent.enabled ? Colors.textPrimary : Colors.textTertiary
                                    }
                                    background: Rectangle {
                                        color: parent.enabled ? Colors.surface : Colors.bgTertiary
                                        border.color: Colors.borderLight
                                        radius: Metrics.radiusSm
                                    }
                                    onClicked: {
                                        indexCurrentNoteForRag()
                                    }
                                }

                                Button {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 32
                                    text: "현재 폴더 등록"
                                    enabled: canUseAI() && !root.ragIndexingRunning && !root.ragRequestRunning
                                    contentItem: Text {
                                        text: parent.text
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                        color: parent.enabled ? Colors.textPrimary : Colors.textTertiary
                                    }
                                    background: Rectangle {
                                        color: parent.enabled ? Colors.surface : Colors.bgTertiary
                                        border.color: Colors.borderLight
                                        radius: Metrics.radiusSm
                                    }
                                    onClicked: {
                                        indexCurrentFolderForRag()
                                    }
                                }

                                Button {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 32
                                    text: "전체 노트 등록"
                                    enabled: canUseAI() && !root.ragIndexingRunning && !root.ragRequestRunning
                                    contentItem: Text {
                                        text: parent.text
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                        color: parent.enabled ? Colors.textPrimary : Colors.textTertiary
                                    }
                                    background: Rectangle {
                                        color: parent.enabled ? Colors.surface : Colors.bgTertiary
                                        border.color: Colors.borderLight
                                        radius: Metrics.radiusSm
                                    }
                                    onClicked: {
                                        indexAllNotesForRag()
                                    }
                                }

                                Button {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 32
                                    text: "외부 파일 등록"
                                    enabled: canUseAI() && !root.ragIndexingRunning && !root.ragRequestRunning
                                    contentItem: Text {
                                        text: parent.text
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                        color: parent.enabled ? Colors.textPrimary : Colors.textTertiary
                                    }
                                    background: Rectangle {
                                        color: parent.enabled ? Colors.surface : Colors.bgTertiary
                                        border.color: Colors.borderLight
                                        radius: Metrics.radiusSm
                                    }
                                    onClicked: {
                                        externalFileDialog.open()
                                    }
                                }

                                Button {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 32
                                    text: "외부 폴더 등록"
                                    enabled: canUseAI() && !root.ragIndexingRunning && !root.ragRequestRunning
                                    contentItem: Text {
                                        text: parent.text
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                        color: parent.enabled ? Colors.textPrimary : Colors.textTertiary
                                    }
                                    background: Rectangle {
                                        color: parent.enabled ? Colors.surface : Colors.bgTertiary
                                        border.color: Colors.borderLight
                                        radius: Metrics.radiusSm
                                    }
                                    onClicked: {
                                        externalFolderDialog.open()
                                    }
                                }

                                Button {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 32
                                    text: "참고문서 관리"
                                    enabled: canUseAI()
                                    contentItem: Text {
                                        text: parent.text
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                        color: parent.enabled ? Colors.textPrimary : Colors.textTertiary
                                    }
                                    background: Rectangle {
                                        color: parent.enabled ? Colors.surface : Colors.bgTertiary
                                        border.color: Colors.borderLight
                                        radius: Metrics.radiusSm
                                    }
                                    onClicked: {
                                        root.openReferenceDocsSettings()
                                    }
                                }
                            }

                            Rectangle {
                                width: parent.width
                                height: 1
                                color: Colors.borderLight
                            }

                            Text {
                                text: "등록된 문서 질문"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: Typography.weightMedium
                                color: Colors.textPrimary
                            }

                            TextField {
                                id: ragQuestionInput
                                width: parent.width
                                placeholderText: "등록된 문서에 대해 질문하세요."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                enabled: canUseAI() && !root.ragIndexingRunning && !root.ragRequestRunning && !root.aiRunning
                            }

                            Button {
                                width: parent.width
                                Layout.preferredHeight: 40
                                text: "질문하기"
                                enabled: canUseAI() && !root.ragIndexingRunning && !root.ragRequestRunning && !root.aiRunning && ragQuestionInput.text !== ""
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
                                    askIndexedDocuments(ragQuestionInput.text)
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
                    height: 0

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
                                console.log("[AIAssistantPanel] 질문 초기화")
                                var ac = getAssistantController()
                                if (ac && window.currentNote && window.currentNote.content && questionInput.text) {
                                    ac.askQuestion(window.currentNote.content, questionInput.text)
                                }
                            }
                        }
                    }
                }

                // 참고문서 AI 현재 RAG 대상 문서 목록 (메인 섹션 하단)
                Rectangle {
                    width: parent.width
                    radius: Metrics.radiusMd
                    color: Colors.surface
                    border.color: Colors.borderLight
                    border.width: 1
                    implicitHeight: ragTargetListColumn.implicitHeight + (Metrics.sm * 2)
                    visible: root.aiModeIndex === 1
                    height: visible ? implicitHeight : 0

                    Column {
                        id: ragTargetListColumn
                        width: parent.width - (Metrics.sm * 2)
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.margins: Metrics.sm
                        spacing: Metrics.xs

                        Text {
                            text: "현재 참고문서 대상 " + root.ragTargetDocumentsTotalCount + "개 / 표시 " + root.ragTargetDocuments.length + "개"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            font.weight: Typography.weightMedium
                            color: Colors.textSecondary
                        }
                        Text {
                            text: "최대 " + root.ragTargetDocumentsDisplayLimit + "개까지만 표시됩니다."
                            font.family: Typography.fontPrimary
                            font.pixelSize: 9
                            color: Colors.textTertiary
                            visible: root.ragTargetDocumentsTotalCount > root.ragTargetDocumentsDisplayLimit
                        }

                        ScrollView {
                            width: parent.width
                            height: 225
                            clip: true
                            ScrollBar.vertical.policy: ScrollBar.AlwaysOn
                            visible: root.ragTargetDocuments.length > 0

                            Column {
                                width: parent.width
                                spacing: 2
                                Repeater {
                                    model: root.ragTargetDocuments
                                    delegate: Row {
                                        spacing: Metrics.xs
                                        Text {
                                            text: (index + 1) + ". "
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 10
                                            color: Colors.textTertiary
                                        }
                                        Text {
                                            text: modelData.title || "제목 없음"
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 10
                                            color: Colors.textPrimary
                                            elide: Text.ElideRight
                                            Layout.maximumWidth: root.width - 80
                                        }
                                        Text {
                                            text: formatRagDocumentSubtitle(modelData)
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 9
                                            color: Colors.textTertiary
                                        }
                                    }
                                }
                            }
                        }

                        Text {
                            text: root.ragTargetDocumentsError !== "" ? root.ragTargetDocumentsError : "등록된 참고문서가 없습니다. 위에서 문서를 등록해주세요."
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: root.ragTargetDocumentsError !== "" ? Colors.error : Colors.textTertiary
                            horizontalAlignment: Text.AlignHCenter
                            width: parent.width
                            wrapMode: Text.Wrap
                            visible: root.ragTargetDocuments.length === 0 || root.ragTargetDocumentsError !== ""
                        }
                    }
                }
            }

        }

        // 공통 AI 실행 결과 섹션 (패널 하단 고정)
        Rectangle {
            Layout.fillWidth: true
            radius: Metrics.radiusMd
            color: Colors.bgSecondary
            border.color: Colors.borderLight
            border.width: 1
            implicitHeight: aiResultCommonColumn.implicitHeight + (Metrics.md * 2)
            visible: true

            Column {
                id: aiResultCommonColumn
                width: parent.width - (Metrics.md * 2)
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.margins: Metrics.sm
                spacing: Metrics.xs

                Column {
                    visible: root.aiModeIndex === 0
                    spacing: Metrics.xs

                    Row {
                        spacing: Metrics.xs
                        Text {
                            text: root.currentAiRunStatus.lastActionName || "AI 실행"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            font.weight: Typography.weightMedium
                            color: Colors.textPrimary
                        }
                        Text {
                            text: root.aiRunning ? "실행 중..." : (root.currentAiRunStatus.lastSuccess ? "실행 완료" : (root.currentAiRunStatus.lastErrorMessage ? "실행 실패" : ""))
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: root.aiRunning ? Colors.primary500 : (root.currentAiRunStatus.lastSuccess ? Colors.success : (root.currentAiRunStatus.lastErrorMessage ? Colors.error : Colors.textSecondary))
                        }
                    }

                    Text {
                        text: root.currentAiRunStatus.lastSuccess ?
                              (root.currentAiRunStatus.lastElapsedMs > 0 ? "소요시간: " + (root.currentAiRunStatus.lastElapsedMs / 1000).toFixed(1) + "초" : "") :
                              (root.currentAiRunStatus.lastErrorMessage || "")
                        font.family: Typography.fontPrimary
                        font.pixelSize: 10
                        color: root.currentAiRunStatus.lastSuccess ? Colors.textTertiary : Colors.error
                        visible: root.currentAiRunStatus.lastExecutedAt !== "" && !root.aiRunning
                    }

                    Text {
                        text: "리소스: " + root.currentAiRunStatus.lastResourceText
                        font.family: Typography.fontPrimary
                        font.pixelSize: 10
                        color: Colors.textTertiary
                        visible: root.currentAiRunStatus.lastSuccess && root.currentAiRunStatus.lastResourceText && !root.aiRunning
                    }

                    Text {
                        text: "결과 노트: " + (root.currentAiRunStatus.lastResultNoteTitle || root.currentAiRunStatus.lastResultNoteId || "생성 중...")
                        font.family: Typography.fontPrimary
                        font.pixelSize: 10
                        color: Colors.primary500
                        visible: root.currentAiRunStatus.lastResultNoteTitle !== "" && !root.aiRunning
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                if (root.currentAiRunStatus.lastResultNoteId && typeof selectedNoteId !== "undefined") {
                                    selectedNoteId = root.currentAiRunStatus.lastResultNoteId
                                }
                            }
                        }
                    }
                }

                Column {
                    visible: root.aiModeIndex === 1
                    spacing: Metrics.xs

                    Row {
                        spacing: Metrics.xs
                        Text {
                            text: root.ragRunStatus.lastQuestion ? (root.ragRunStatus.lastQuestion.substring(0, 20) + (root.ragRunStatus.lastQuestion.length > 20 ? "..." : "")) : "RAG 질문"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            font.weight: Typography.weightMedium
                            color: Colors.textPrimary
                        }
                        Text {
                            text: root.ragRequestRunning ? "실행 중..." : (root.ragRunStatus.lastSuccess ? "실행 완료" : (root.ragRunStatus.lastErrorMessage ? "실행 실패" : ""))
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.caption
                            color: root.ragRequestRunning ? Colors.primary500 : (root.ragRunStatus.lastSuccess ? Colors.success : (root.ragRunStatus.lastErrorMessage ? Colors.error : Colors.textSecondary))
                        }
                    }

                    Text {
                        text: root.ragRunStatus.lastSuccess ?
                              (root.ragRunStatus.lastElapsedMs > 0 ? "소요시간: " + (root.ragRunStatus.lastElapsedMs / 1000).toFixed(1) + "초" : "") :
                              (root.ragRunStatus.lastErrorMessage || "")
                        font.family: Typography.fontPrimary
                        font.pixelSize: 10
                        color: root.ragRunStatus.lastSuccess ? Colors.textTertiary : Colors.error
                        visible: root.ragRunStatus.lastExecutedAt !== "" && !root.ragRequestRunning
                    }

                    Text {
                        text: "리소스: " + root.ragRunStatus.lastResourceText
                        font.family: Typography.fontPrimary
                        font.pixelSize: 10
                        color: Colors.textTertiary
                        visible: root.ragRunStatus.lastSuccess && root.ragRunStatus.lastResourceText && !root.ragRequestRunning
                    }

                    Text {
                        text: "결과 노트: " + (root.ragRunStatus.lastResultNoteTitle || root.ragRunStatus.lastResultNoteId || "생성 중...")
                        font.family: Typography.fontPrimary
                        font.pixelSize: 10
                        color: Colors.primary500
                        visible: root.ragRunStatus.lastResultNoteTitle !== "" && !root.ragRequestRunning
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                if (root.ragRunStatus.lastResultNoteId && typeof selectedNoteId !== "undefined") {
                                    selectedNoteId = root.ragRunStatus.lastResultNoteId
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Item {
        id: progressOverlay
        anchors.fill: parent
        visible: root.aiRunning || root.ragRequestRunning || root.ragIndexingRunning
        opacity: visible ? 1 : 0
        z: 999
        enabled: visible

        Rectangle {
            anchors.fill: parent
            color: Colors.bgPrimary
            opacity: 0.92
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onClicked: {}
        }

        Column {
            anchors.centerIn: parent
            width: Math.min(root.width * 0.85, 420)
            spacing: Metrics.sm

            BusyIndicator {
                running: !root.ragIndexingRunning
                width: 48
                height: 48
                visible: !root.ragIndexingRunning
            }

            Text {
                text: root.ragIndexingRunning
                      ? "참고문서를 등록하는 중입니다..."
                      : (root.ragRequestRunning ? "답변 생성 중..." : "AI 작업 실행 중")
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.bodyLarge
                font.weight: Typography.weightSemibold
                color: Colors.textPrimary
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
            }

            Text {
                text: root.ragIndexingRunning
                      ? "선택된 파일/노트를 순서대로 색인하고 있습니다. 잠시만 기다려주세요."
                      : (root.ragRequestRunning ? "참고문서를 검색하고 답변을 생성 중입니다." : "작업이 완료될 때까지 다른 조작은 잠시 중단됩니다.")
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.caption
                color: Colors.textSecondary
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                width: parent.width
            }

            ProgressBar {
                visible: root.ragIndexingRunning
                Layout.fillWidth: true
                from: 0
                to: Math.max(1, root.ragIndexingProgressTotal)
                value: Math.min(root.ragIndexingProgressCurrent, Math.max(1, root.ragIndexingProgressTotal))
                indeterminate: root.ragIndexingProgressTotal <= 0
            }

            Text {
                visible: root.ragIndexingRunning
                text: root.ragIndexingProgressTotal > 0
                      ? (root.ragIndexingProgressCurrent + " / " + root.ragIndexingProgressTotal + " 문서 처리")
                      : "목록을 준비하고 있습니다..."
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.caption
                color: Colors.textSecondary
                horizontalAlignment: Text.AlignHCenter
                width: parent.width
            }

            Rectangle {
                visible: root.ragIndexingRunning && root.ragIndexingProgressItems.length > 0
                width: parent.width
                height: Math.min(220, root.ragIndexingProgressItems.length * 22 + Metrics.md * 2)
                radius: Metrics.radiusSm
                color: Colors.surface
                border.color: Colors.borderLight
                border.width: 1

                Column {
                    anchors.fill: parent
                    anchors.margins: Metrics.sm
                    spacing: Metrics.xs

                    Text {
                        text: "등록 중인 파일/노트 목록"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.caption
                        font.weight: Typography.weightMedium
                        color: Colors.textSecondary
                    }

                    ScrollView {
                        width: parent.width
                        height: parent.height - Metrics.lg
                        clip: true
                        ScrollBar.vertical.policy: ScrollBar.AsNeeded

                        Column {
                            width: parent.width
                            spacing: 2
                            Repeater {
                                model: root.ragIndexingProgressItems
                                delegate: Row {
                                    width: parent.width
                                    spacing: Metrics.xs
                                    Text {
                                        text: (Math.max(0, root.ragIndexingProgressCurrent - root.ragIndexingProgressItems.length) + index + 1) + "."
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: 10
                                        color: Colors.textTertiary
                                        width: 24
                                    }
                                    Text {
                                        text: modelData
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: 10
                                        color: Colors.textPrimary
                                        wrapMode: Text.NoWrap
                                        elide: Text.ElideRight
                                        width: parent.width - 24
                                    }
                                }
                            }
                        }
                    }
                }
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

    FileDialog {
        id: externalFileDialog
        title: "외부 문서 선택"
        nameFilters: ["Markdown (*.md *.markdown)", "HWPX (*.hwpx)", "HWP (*.hwp)", "All files (*)"]
        fileMode: FileDialog.OpenFiles
        onAccepted: {
            var paths = []
            for (var i = 0; i < selectedFiles.length; i++) {
                paths.push(fileUrlToLocalPath(selectedFiles[i]))
            }
            indexExternalFilesForRag(paths)
        }
    }

    FolderDialog {
        id: externalFolderDialog
        title: "외부 폴더 선택"
        onAccepted: {
            var folderPath = fileUrlToLocalPath(selectedFolder)
            indexExternalFolderForRag(folderPath)
        }
    }
}

