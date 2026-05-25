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
    clip: true

    signal openSettingsDialog()
    signal openReferenceDocsSettings()
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
    property int aiModeIndex: 0  // 0 = 현재 문서 AI, 1 = 참고문서 AI

    onAiModeIndexChanged: {
        console.log("[AIAssistantPanel][DIAG] aiModeIndex changed:", aiModeIndex)
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
                note_id: window.currentNote.id || "",
                title: window.currentNote.title || "",
                content: window.currentNote.content || "",
                tags: window.currentNote.tags || ""
            })
        }

        root.responseText = ""

        if (action.action_id === "current_note_qa") {
            if (!window.currentNote || !window.currentNote.content) {
                root.responseText = "현재 노트를 선택한 뒤 실행해주세요."
                console.log("[AIAssistantPanel] current_note_qa: no note selected")
                return
            }
            if (!userInput) {
                root.responseText = "질문 내용을 입력해주세요."
                console.log("[AIAssistantPanel] current_note_qa: no question input")
                return
            }

            console.log(
                "[AIAssistantPanel] current_note_qa: executing via runCustomAction, " +
                "userInput_len=" + userInput.length + ", content_len=" + (window.currentNote.content ? window.currentNote.content.length : 0)
            )

            try {
                ac.runCustomAction(action.action_id, userInput, currentNoteJson, selection, "[]")
            } catch (e) {
                console.log("[AIAssistantPanel] current_note_qa runCustomAction failed: " + e)
                console.log("[AIAssistantPanel] current_note_qa fallback to askQuestion")
                ac.askQuestion(window.currentNote.content, userInput)
            }
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
    }

    function clearRagState() {
        root.ragCitations = []
        root.ragWarnings = []
    }

    function formatHeadingPath(headingPath) {
        if (!headingPath || !Array.isArray(headingPath) || headingPath.length === 0) return ""
        return headingPath.join(" > ")
    }

    function indexCurrentNoteForRag() {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) {
            root.responseText = "[오류] RAG 컨트롤러를 사용할 수 없습니다"
            return
        }

        if (!window.currentNote || !window.currentNote.id) {
            root.responseText = "현재 노트가 없습니다"
            return
        }

        var note = window.currentNote
        var tagsJson = "[]"
        if (note.tags && Array.isArray(note.tags)) {
            tagsJson = JSON.stringify(note.tags)
        }

        clearRagState()
        root.ragIndexingRunning = true
        root.responseText = "참고문서를 등록하는 중..."

        console.log("[AIAssistantPanel] Indexing current note: id=" + note.id)
        ragCtrl.indexCurrentNote(note.id, note.title || "", note.content || "", tagsJson)
    }

    function askIndexedDocuments(questionText) {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) {
            root.responseText = "[오류] RAG 컨트롤러를 사용할 수 없습니다"
            return
        }

        var question = questionText || actionInput.text || ""
        if (!question) {
            root.responseText = "질문 내용을 입력해주세요."
            return
        }

        clearRagState()
        root.ragRequestRunning = true
        root.responseText = "답변 생성 중..."

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
            root.responseText = "[오류] RAG 컨트롤러를 사용할 수 없습니다"
            return
        }

        var folderCtrl = getFolderController()
        if (!folderCtrl) {
            root.responseText = "[오류] 폴더 컨트롤러를 사용할 수 없습니다"
            return
        }

        var currentFolderId = folderCtrl.currentFolderId
        if (!currentFolderId) {
            root.responseText = "현재 폴더가 선택되지 않았습니다"
            return
        }

        clearRagState()
        root.ragIndexingRunning = true
        root.responseText = "참고문서를 등록하는 중..."

        try {
            var descendantIds = folderCtrl.getDescendantIds(currentFolderId)
            var folderIds = [currentFolderId].concat(descendantIds || [])
            var notesJson = noteController.getNotesForRagByFolderIdsJson(JSON.stringify(folderIds))

            console.log("[AIAssistantPanel] Indexing folder: " + currentFolderId + ", notes count: " + (JSON.parse(notesJson).length || 0))
            ragCtrl.indexCurrentFolderNotes(notesJson, currentFolderId)
        } catch (e) {
            root.ragIndexingRunning = false
            root.responseText = "[오류] 참고문서 등록 실패: " + e
        }
    }

    function indexAllNotesForRag() {
        var ragCtrl = getAiRagController()
        if (!ragCtrl) {
            root.responseText = "[오류] RAG 컨트롤러를 사용할 수 없습니다"
            return
        }

        var noteCtrl = getNoteController()
        if (!noteCtrl) {
            root.responseText = "[오류] 노트 컨트롤러를 사용할 수 없습니다"
            return
        }

        clearRagState()
        root.ragIndexingRunning = true
        root.responseText = "참고문서를 등록하는 중..."

        try {
            var notesJson = noteCtrl.getAllNotesForRagJson()
            console.log("[AIAssistantPanel] Indexing all notes, count: " + (JSON.parse(notesJson).length || 0))
            ragCtrl.indexAllNotesJson(notesJson)
        } catch (e) {
            root.ragIndexingRunning = false
            root.responseText = "[오류] 참고문서 등록 실패: " + e
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

    function openCitation(citation) {
        var noteCtrl = getNoteController()
        if (!noteCtrl) {
            root.responseText += "\n[RAG 오류] 노트 컨트롤러를 사용할 수 없습니다"
            return
        }

        if (citation.note_id) {
            console.log("[AIAssistantPanel] Opening citation note: " + citation.note_id)
            var success = noteCtrl.selectNote(citation.note_id)
            if (success) {
                root.responseText += "\n[안내] 근거 노트를 열었습니다"
            } else {
                root.responseText += "\n[RAG 오류] 근거 노트를 찾을 수 없습니다"
            }
        } else if (citation.source_path) {
            var copied = copyCitationPath(citation)
            if (copied) {
                root.responseText += "\n[안내] 파일 경로를 복사했습니다"
            } else {
                root.responseText += "\n[안내] 파일 경로: " + citation.source_path
            }
        } else {
            root.responseText += "\n[안내] 열 수 있는 원문 정보가 없습니다"
        }
    }

    function formatCitationActionLabel(citation) {
        if (citation.note_id) return "노트 열기"
        if (citation.source_path) return "경로 복사"
        return ""
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

    function copyCitationPath(citation) {
        if (!citation || !citation.source_path) return false
        return copyTextToClipboard(citation.source_path)
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

    function fileUrlToLocalPath(fileUrl) {
        if (!fileUrl) return ""
        var path = fileUrl
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
            root.responseText = "[오류] RAG 컨트롤러를 사용할 수 없습니다"
            return
        }

        if (!paths || paths.length === 0) {
            root.responseText = "선택된 파일이 없습니다"
            return
        }

        clearRagState()
        root.ragIndexingRunning = true
        root.responseText = "참고문서를 등록하는 중..."

        try {
            var pathsJson = JSON.stringify(paths)
            console.log("[AIAssistantPanel] Indexing external files: " + paths.length + " files")
            ragCtrl.indexExternalFilesJson(pathsJson)
        } catch (e) {
            root.ragIndexingRunning = false
            root.responseText = "[오류] 참고문서 등록 실패: " + e
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
        root.refreshActionList()
        root.ensureActionSelection()

        // Connect aiRagController signals
        var ragCtrl = getAiRagController()
        if (ragCtrl) {
            ragCtrl.ragAnswerReady.connect(function(answerText) {
                console.log("[AIAssistantPanel] RAG answer received: len=" + answerText.length)
                root.ragRequestRunning = false
                root.responseText = "[등록된 문서 답변]\n" + answerText
                updateRagCitationsFromController()
                updateRagWarningsFromController()
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

            ragCtrl.indexStatusChanged.connect(function(status) {
                console.log("[AIAssistantPanel] RAG index status: " + status)
                root.ragIndexingRunning = false
                if (status === "indexed_current_note") {
                    root.responseText = "현재 문서가 등록되었습니다. '등록된 문서 질문' 버튼을 눌러 질문하세요."
                } else if (status === "indexed_folder") {
                    var result = updateLastIndexResultFromController()
                    root.responseText = formatIndexResultMessage(result, "현재 폴더")
                } else if (status === "indexed_all_notes") {
                    var result = updateLastIndexResultFromController()
                    root.responseText = formatIndexResultMessage(result, "전체 노트")
                } else if (status === "indexed_notes") {
                    var result = updateLastIndexResultFromController()
                    root.responseText = formatIndexResultMessage(result, "노트")
                } else if (status === "indexed_external_files") {
                    var result = updateLastIndexResultFromController()
                    root.responseText = formatIndexResultMessage(result, "외부 문서")
                } else if (status === "indexed_empty") {
                    root.responseText = "등록할 노트가 없습니다."
                } else if (status === "cleared") {
                    root.responseText = "참고문서 등록이 초기화되었습니다."
                    clearRagState()
                }
            })

            ragCtrl.errorOccurred.connect(function(error) {
                root.ragRequestRunning = false
                root.ragIndexingRunning = false
                root.responseText += "\n[RAG 오류] " + error
            })
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
                                implicitHeight: selectedActionTitle.implicitHeight + (selectedActionDescription.visible ? selectedActionDescription.implicitHeight + Metrics.xs : 0) + Metrics.md * 2
                                radius: Metrics.radiusMd
                                color: Colors.bgSecondary
                                border.color: Colors.borderLight
                                border.width: 1
                                visible: !!(root.selectedAction && root.selectedAction.action_id)

                                Column {
                                    width: parent.width - (Metrics.md * 2)
                                    anchors.top: parent.top
                                    anchors.topMargin: Metrics.sm
                                    anchors.bottom: parent.bottom
                                    anchors.bottomMargin: Metrics.sm
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    spacing: Metrics.xs

                                    Text {
                                        id: selectedActionTitle
                                        width: parent.width
                                        text: root.selectedAction ? (root.selectedAction.name || root.selectedAction.action_id) : ""
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.bodyRegular
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
                        id: referenceDocsTab
                        objectName: "referenceDocsTab"
                        width: parent.width
                        radius: Metrics.radiusLg
                        color: Colors.surface
                        border.color: Colors.borderLight
                        implicitHeight: referenceDocsCardColumn.implicitHeight + (Metrics.md * 2)
                        visible: root.aiModeIndex === 1

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

                            RowLayout {
                                width: parent.width
                                spacing: Metrics.sm

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
                            }

                            RowLayout {
                                width: parent.width
                                spacing: Metrics.sm

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

                            Rectangle {
                                width: parent.width
                                height: 1
                                color: Colors.borderLight
                            }

                            Button {
                                width: parent.width
                                Layout.preferredHeight: 36
                                text: "참고문서 관리"
                                enabled: canUseAI()
                                contentItem: Text {
                                    text: parent.text
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    font.weight: Typography.weightMedium
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
            }
        }

        Rectangle {
            Layout.fillWidth: true
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

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: ragCitationsColumn.implicitHeight + Metrics.sm
                        color: Colors.surface
                        border.color: Colors.borderLight
                        radius: Metrics.radiusSm
                        visible: root.hasRagCitations

                        Column {
                            id: ragCitationsColumn
                            width: parent.width - (Metrics.sm * 2)
                            anchors.horizontalCenter: parent.horizontalCenter
                            spacing: Metrics.xs

                            Text {
                                text: "근거 문서 (" + root.ragCitations.length + ")"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                font.weight: Typography.weightMedium
                                color: Colors.textSecondary
                            }

                            Repeater {
                                model: root.ragCitations
                                delegate: Column {
                                    width: parent.width
                                    spacing: 2

                                    Row {
                                        spacing: Metrics.xs
                                        Text {
                                            text: modelData.source_id + " · " + (modelData.title || "제목 없음")
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: Typography.caption
                                            color: Colors.textPrimary
                                            elide: Text.ElideRight
                                            Layout.maximumWidth: root.width - 100
                                        }
                                        Text {
                                            text: "답변에 인용됨"
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 10
                                            color: Colors.primary500
                                            visible: modelData.cited_in_answer
                                        }
                                    }

                                    Text {
                                        text: formatHeadingPath(modelData.heading_path)
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: 10
                                        color: Colors.textTertiary
                                        visible: modelData.heading_path && modelData.heading_path.length > 0
                                    }

                                    Text {
                                        text: modelData.source_type + (modelData.note_id ? " · note_id: " + modelData.note_id : (modelData.source_path ? " · " + formatSourcePath(modelData.source_path) : ""))
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: 10
                                        color: Colors.textTertiary
                                        elide: Text.ElideRight
                                        Layout.maximumWidth: root.width - 60
                                    }

                                    Row {
                                        spacing: Metrics.xs
                                        visible: modelData.note_id || modelData.source_path

                                        Button {
                                            implicitWidth: 60
                                            implicitHeight: 20
                                            padding: 0
                                            text: formatCitationActionLabel(modelData)
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 9
                                            onClicked: {
                                                openCitation(modelData)
                                            }
                                            background: Rectangle {
                                                color: Colors.bgSecondary
                                                border.color: Colors.borderLight
                                                radius: 3
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: ragWarningsColumn.implicitHeight + Metrics.sm
                        color: Colors.surface
                        border.color: Colors.warning
                        radius: Metrics.radiusSm
                        visible: root.hasRagWarnings

                        Column {
                            id: ragWarningsColumn
                            width: parent.width - (Metrics.sm * 2)
                            anchors.horizontalCenter: parent.horizontalCenter
                            spacing: Metrics.xs

                            Text {
                                text: "알림"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                font.weight: Typography.weightMedium
                                color: Colors.warning
                            }

                            Repeater {
                                model: root.ragWarnings
                                delegate: Text {
                                    text: "- " + formatRagWarningMessage(modelData)
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: 10
                                    color: Colors.textSecondary
                                    wrapMode: Text.Wrap
                                    width: parent.width
                                }
                            }
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
}

