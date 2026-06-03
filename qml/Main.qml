import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Dialogs
import theme
import components

Window {
    id: window

    visible: true
    width: 1400
    height: 900
    minimumWidth: 900
    minimumHeight: 600
    title: (typeof appName !== "undefined" && appName) ? appName : "Nuni Note"
    color: Colors.bgPrimary

    // Properties for note selection
    property string selectedNoteId: ""
    property var currentNote: null
    property var openTabs: []   // [{id, title}, ...]
    property bool noteSelectionMode: false
    property var selectedNoteIds: []
    property var selectableFolderItems: []
    property string batchActionMode: ""    // move | copy
    property string batchTargetFolderId: ""
    property string batchTargetFolderName: ""
    property string batchFolderHintMessage: ""
    property string folderMoveSourceId: ""
    property string folderMoveSourceName: ""
    property string folderMoveTargetId: ""
    property string folderMoveTargetName: ""
    property var folderMoveTargetItems: []
    property var folderOrderSiblingItems: []
    property int folderOrderDirection: 0

    // Draft model for folder placement (move/reorder)
    property var originalFolderSnapshot: []
    property var folderSettingsDraftItems: []
    property var folderMovePreviewItems: []
    property string selectedMoveTargetId: ""
    property string selectedMoveTargetName: ""
    property string draftParentId: ""
    property var draftOrderItems: []
    property string folderPlacementStatusMessage: ""
    property bool folderPlacementStatusError: false
    property int folderPlacementChangeCounter: 0
    property real editorZoom: 1.0
    property bool isDraftNewNote: false
    property string draftFolderId: ""
    property bool titleTouchedByUser: false
    property string exportDraftTitle: ""
    property string exportDraftMarkdown: ""
    property string exportDraftJson: ""
    property string exportFormat: "pdf"
    property string exportOutputDir: ""
    property string exportStatusMessage: ""
    property bool exportStatusError: false
    property string exportLastOutputPath: ""
    property bool folderExportMode: false
    property string folderExportScope: "folder"  // folder | all | favorites
    property string folderExportFolderId: ""
    property string folderExportLabel: ""
    property string importStatusMessage: ""
    property bool importStatusError: false
    property bool importBusy: false
    property bool exportBusy: false
    property bool importIncludeSubfolders: true
    property int importProgressValue: 0
    property int importProgressTotal: 0
    property int exportProgressValue: 0
    property int exportProgressTotal: 0
    property var templateSelectionItems: []
    property string templateDialogFolderId: ""
    property string templateDialogFolderName: ""
    property string templateDialogFolderPath: ""
    property string templateSelectedDefaultId: ""
    property string templateEditId: ""
    property string templateEditName: ""
    property string templateEditTitle: ""
    property string templateEditContent: ""
    property string templateStatusMessage: ""
    property bool templateStatusError: false
    property int folderSettingsMenuIndex: 0
    property string folderRenameEditName: ""
    property bool aiPanelOpen: true
    property bool promptRulesExpanded: false
    property bool promptVarsExpanded: false
    property string promptSampleDocId: "prompt_sample_current_doc"
    property var promptWarningMessages: []

    // AI Prompt Workspace Mode
    property string activeContentMode: "notes"  // "notes" | "ai_prompts"
    property string selectedAIPromptDocId: ""
    property var currentAIPromptDocument: null
    property string lastRealLibraryIdBeforeAIPromptMode: ""
    property int promptListRefreshCounter: 0  // Force ListView refresh
    property string aiPromptTitleDraft: ""
    property var promptRuleInsertItems: [
        { "icon": "\uD83C\uDFAD", "label": "역할", "description": "AI의 역할과 페르소나를 정의합니다", "value": "[역할]\n당신은 현재 문서와 사용자의 요청을 바탕으로 업무에 바로 활용할 수 있는 결과를 작성하는 AI 업무비서입니다.\n" },
        { "icon": "\uD83D\uDCE5", "label": "입력", "description": "프롬프트에 포함할 입력 데이터를 안내합니다", "value": "[입력]\n현재 문서 내용:\n{{CONTENT}}\n\n선택한 내용:\n{{SELECTION}}\n\n사용자 입력:\n{{USER_INPUT}}\n\n참고문서 내용:\n{{CONTEXT}}\n" },
        { "icon": "\uD83D\uDCCB", "label": "출력 형식", "description": "결과물의 구조를 정합니다", "value": "[출력 형식]\n사용자의 요청에 맞게 결과를 작성하세요.\n필요한 경우 제목, 핵심 요약, 주요 내용, 확인 필요 사항, 다음 작업으로 나누어 정리하세요.\n" },
        { "icon": "\uD83D\uDCCF", "label": "답변 길이", "description": "응답 분량을 안내합니다", "value": "[답변 길이]\n불필요하게 길게 쓰지 말고, 사용자가 바로 활용할 수 있을 정도로 간결하게 작성하세요.\n" },
        { "icon": "\uD83D\uDCAC", "label": "말투", "description": "문체와 어조를 설정합니다", "value": "[말투]\n자연스럽고 명확한 한국어 문장으로 작성하세요.\n" },
        { "icon": "\uD83D\uDEAB", "label": "금지 사항", "description": "AI가 하지 말아야 할 행동을 명시합니다", "value": "[금지 사항]\n문서에 없는 내용을 사실처럼 추가하지 마세요.\n사용자의 요청과 관련 없는 내용은 포함하지 마세요.\n선택한 내용이 있는 경우, 선택한 내용을 우선 기준으로 처리하세요.\n" },
        { "icon": "\u2753", "label": "불확실할 때", "description": "정보가 부족할 때 행동을 지정합니다", "value": "[불확실할 때]\n문서 내용만으로 판단하기 어려운 부분은 \"문서에서 확인할 수 없습니다\"라고 표시하세요.\n추측이 필요한 경우에는 \"추측입니다\"라고 밝혀 주세요.\n" },
        { "icon": "\uD83D\uDCDD", "label": "예시 출력", "description": "원하는 출력 예시를 보여줍니다", "value": "[예시 출력]\n핵심 요약:\n- \n\n확인 필요 사항:\n- \n\n다음 작업:\n- \n" }
    ]
    property var promptVariableInsertItems: [
        { "icon": "\uD83D\uDCC4", "label": "현재 문서 내용", "code": "{{CONTENT}}", "description": "현재 열려 있는 문서 전체 내용을 프롬프트에 넣습니다.", "value": "{{CONTENT}}" },
        { "icon": "\u2702\uFE0F", "label": "선택한 내용", "code": "{{SELECTION}}", "description": "사용자가 문서에서 선택한 텍스트를 프롬프트에 넣습니다.", "value": "{{SELECTION}}" },
        { "icon": "\u2328\uFE0F", "label": "사용자 입력", "code": "{{USER_INPUT}}", "description": "AI 실행창에 사용자가 입력한 요청을 프롬프트에 넣습니다.", "value": "{{USER_INPUT}}" },
        { "icon": "\uD83D\uDD0D", "label": "참고문서 내용", "code": "{{CONTEXT}}", "description": "참고문서 AI 또는 RAG 검색 결과를 프롬프트에 넣습니다.", "value": "{{CONTEXT}}" }
    ]

    // Reload prompt documents when switching to AI prompt mode
    onActiveContentModeChanged: {
        console.log("[Main] activeContentMode changed to:", window.activeContentMode)
        if (window.activeContentMode === "ai_prompts") {
            console.log("[Main] Switching to AI prompt mode, reloading documents")
            if (typeof promptDocumentController !== "undefined" && promptDocumentController) {
                promptDocumentController.loadPromptDocuments()
                window.promptListRefreshCounter++
                console.log("[Main] Incremented promptListRefreshCounter to:", window.promptListRefreshCounter)
                // Force ListView to refresh by resetting model
                window.forcePromptListRefresh()
            } else {
                console.log("[Main] promptDocumentController not available")
            }
        } else {
            window.promptWarningMessages = []
        }
    }

    onCurrentAIPromptDocumentChanged: {
        window.aiPromptTitleDraft = window.currentAIPromptDocument ? (window.currentAIPromptDocument.title || "") : ""
        if (aiPromptTitleField) {
            aiPromptTitleField.text = window.aiPromptTitleDraft
        }
        // Initialize editor with prompt content when in AI prompt mode
        if (window.activeContentMode === "ai_prompts" && window.currentAIPromptDocument && noteEditor) {
            var content = window.currentAIPromptDocument.content_md || ""
            noteEditor.resetEditor(content, "")
        }
    }

    onSelectedAIPromptDocIdChanged: {
        if (!window.selectedAIPromptDocId) {
            window.aiPromptTitleDraft = ""
            if (aiPromptTitleField) {
                aiPromptTitleField.text = ""
            }
        }
    }

    Timer {
        id: aiPromptTitleSaveTimer
        interval: 600
        repeat: false
        onTriggered: {
            if (window.activeContentMode === "ai_prompts" && window.selectedAIPromptDocId !== "" && !window.currentPromptReadonly()) {
                window.flushSaveIfDirty()
            }
        }
    }

    function currentPromptReadonly() {
        return !!(window.currentAIPromptDocument && window.currentAIPromptDocument.readonly)
    }

    function isPromptSample(doc) {
        if (!doc)
            return false
        if (doc.prompt_doc_id && doc.prompt_doc_id === window.promptSampleDocId)
            return true
        return doc.source_type && doc.source_type === "sample"
    }

    function updatePromptWarnings(markdown) {
        var text = markdown || ""
        var hasContent = text.indexOf("{{CONTENT}}") >= 0
        var hasSelection = text.indexOf("{{SELECTION}}") >= 0
        var hasUserInput = text.indexOf("{{USER_INPUT}}") >= 0
        var hasContext = text.indexOf("{{CONTEXT}}") >= 0

        var warnings = []
        if (!(hasContent || hasSelection || hasUserInput || hasContext)) {
            warnings.push("프롬프트에 입력 변수가 없습니다. AI가 문서나 사용자 입력을 참고하지 못할 수 있습니다.")
        }
        if (!hasUserInput) {
            warnings.push("사용자 입력 변수가 없습니다. AI 실행창에 입력한 내용이 반영되지 않을 수 있습니다.")
        }
        if (!hasContent && !hasSelection) {
            warnings.push("현재 문서 내용 또는 선택한 내용 변수가 없습니다. 문서 기반 작업이 어려울 수 있습니다.")
        }
        window.promptWarningMessages = warnings
    }

    function insertPromptSnippet(text) {
        if (window.activeContentMode !== "ai_prompts") return
        if (window.currentPromptReadonly()) return
        if (!text) return

        console.log("[Main] insertPromptSnippet called with text:", text)
        console.log("[Main] noteEditor available:", !!noteEditor)
        console.log("[Main] noteEditor._editorReady:", !!(noteEditor && noteEditor._editorReady))

        // Try insertMarkdownAtCursor first if noteEditor is ready
        if (noteEditor && noteEditor._editorReady) {
            console.log("[Main] calling noteEditor.insertMarkdownAtCursor")
            noteEditor.insertMarkdownAtCursor(text)
            return
        }

        console.log("[Main] noteEditor not ready, waiting for editor to be ready")
        var newContent = appendPromptText(text)
        scheduleEditorRetry(text, newContent)
    }

    function appendPromptText(text) {
        if (!window.currentAIPromptDocument) return ""
        var currentContent = window.currentAIPromptDocument.content_md || ""
        var snippet = text
        if (!currentContent.endsWith("\n") && snippet.length > 0) {
            snippet = "\n" + snippet
        }
        var updated = currentContent + snippet
        window.currentAIPromptDocument.content_md = updated
        window.updatePromptWarnings(updated)
        console.log("[Main] appendPromptText: updated content length:", updated.length)
        // Trigger binding update so fallback text appears immediately
        Qt.callLater(function() {
            var tempDoc = window.currentAIPromptDocument
            window.currentAIPromptDocument = null
            window.currentAIPromptDocument = tempDoc
        })
        return updated
    }

    function scheduleEditorRetry(text, contentSnapshot) {
        var retryTimer = Qt.createQmlObject(
            "import QtQuick 2.15; Timer { interval: 120; repeat: true }",
            window
        )
        var attempts = 0
        var maxAttempts = 25
        var cachedContent = contentSnapshot
        retryTimer.triggered.connect(function() {
            if (attempts >= maxAttempts) {
                console.log("[Main] scheduleEditorRetry exceeded max attempts; stopping")
                retryTimer.stop()
                retryTimer.destroy()
                return
            }
            attempts += 1
            if (window.noteEditor && window.noteEditor._editorReady) {
                console.log("[Main] scheduleEditorRetry: editor ready on attempt", attempts)
                if (window.currentAIPromptDocument) {
                    window.noteEditor.resetEditor(window.currentAIPromptDocument.content_md || "", "")
                }
                retryTimer.stop()
                retryTimer.destroy()
            } else {
                // Keep editor content in sync while waiting
                if (window.currentAIPromptDocument && window.currentAIPromptDocument.content_md !== cachedContent) {
                    cachedContent = window.currentAIPromptDocument.content_md
                }
            }
        })
        retryTimer.start()
    }

    function forcePromptListRefresh() {
        console.log("[Main] forcePromptListRefresh called")
        var listView = notesListView
        if (listView) {
            listView.model = []
            listView.model = promptDocumentController ? promptDocumentController.promptDocumentList : []
            console.log("[Main] ListView model refreshed, count:", listView.count)
        }
    }

    // Manual save shortcut (Ctrl+S)
    Shortcut {
        sequence: "Ctrl+S"
        onActivated: window.flushSaveIfDirty()
    }

    // Autosave flush helper: called by WebNoteEditor's debounced autosave and focusout flush.
    // Persists draft (if applicable) and triggers async save. Title is auto-derived only when
    // the user has not manually touched the title field and it is currently blank.
    function flushSaveIfDirty() {
        // Phase 2: AI prompt mode - save to promptDocumentController
        if (window.activeContentMode === "ai_prompts") {
            if (!window.selectedAIPromptDocId) {
                console.log("[flushSaveIfDirty] AI prompt mode - no prompt selected")
                return
            }

            // Check if readonly
            if (window.currentAIPromptDocument && window.currentAIPromptDocument.readonly) {
                console.log("[flushSaveIfDirty] AI prompt mode - readonly prompt, save skipped")
                return
            }

            // Get content from editor
            var liveTitle = (currentAIPromptDocument && currentAIPromptDocument.title !== undefined)
                ? currentAIPromptDocument.title : (noteEditor ? noteEditor.title : "")
            var liveMarkdown = (currentAIPromptDocument && currentAIPromptDocument.content_md !== undefined)
                ? currentAIPromptDocument.content_md : (noteEditor ? noteEditor.content : "")

            console.log("[flushSaveIfDirty] AI prompt mode - saving prompt:", window.selectedAIPromptDocId)

            // Save via promptDocumentController
            if (typeof promptDocumentController !== "undefined" && promptDocumentController) {
                promptDocumentController.savePromptDocument(window.selectedAIPromptDocId, liveTitle, liveMarkdown)
            }
            return
        }

        if (!noteController) {
            console.log("[flushSaveIfDirty] no noteController")
            return
        }

        var liveTitle = (currentNote && currentNote.title !== undefined)
            ? currentNote.title : (noteEditor ? noteEditor.title : "")
        var liveMarkdown = (currentNote && currentNote.content !== undefined)
            ? currentNote.content : (noteEditor ? noteEditor.content : "")
        var liveJson = (currentNote && currentNote.content_json !== undefined)
            ? currentNote.content_json : (noteEditor ? noteEditor.contentJson : "")

        console.log("[flushSaveIfDirty] draft=" + isDraftNewNote
                    + " title=" + (liveTitle ? liveTitle.substring(0,20) : "(empty)")
                    + " mdLen=" + (liveMarkdown ? liveMarkdown.length : 0)
                    + " jsonLen=" + (liveJson ? liveJson.length : 0))

        // Auto-derive title only when user hasn't touched it and it's blank
        var titleForSave = liveTitle
        if ((!titleForSave || !titleForSave.trim()) && !titleTouchedByUser) {
            titleForSave = deriveDraftTitle("", liveMarkdown) || ""
        }

        if (isDraftNewNote) {
            // Require some content or a title to materialize a draft
            var effectiveTitle = (titleForSave && titleForSave.trim()) ? titleForSave : "새 노트"
            if (!liveMarkdown && !titleForSave) {
                console.log("[flushSaveIfDirty] draft: nothing to save yet")
                return  // nothing to save yet
            }

            var newId = ensureDraftPersisted(effectiveTitle, liveMarkdown, liveJson)
            if (!newId) {
                console.log("[flushSaveIfDirty] draft: ensureDraftPersisted failed")
                return
            }

            noteController.updateNoteWithJson(newId, effectiveTitle, liveMarkdown, liveJson)
            updateTabTitle(newId, effectiveTitle)
        } else {
            var activeNoteId = selectedNoteId
            if (!activeNoteId) {
                console.log("[flushSaveIfDirty] existing: no activeNoteId")
                return
            }

            var saveTitle = titleForSave || ""
            noteController.updateNoteWithJson(activeNoteId, saveTitle, liveMarkdown, liveJson)
            if (saveTitle) updateTabTitle(activeNoteId, saveTitle)
        }

        console.log("[flushSaveIfDirty] calling saveCurrentNote")
        noteController.saveCurrentNote()
    }

    function openCurrentExportDialog(title, markdown, contentJson) {
        folderExportMode = false
        exportDraftTitle = (title || (currentNote ? currentNote.title : "") || "무제")
        exportDraftMarkdown = (markdown !== undefined && markdown !== null)
            ? markdown
            : ((currentNote && currentNote.content) ? currentNote.content : "")
        exportDraftJson = (contentJson !== undefined && contentJson !== null)
            ? contentJson
            : ((currentNote && currentNote.content_json) ? currentNote.content_json : "")
        exportStatusMessage = ""
        exportStatusError = false
        exportLastOutputPath = ""
        currentNoteExportDialog.visible = true
    }

    function openFolderExportDialog() {
        if (!folderController) {
            exportStatusError = true
            exportStatusMessage = "폴더 컨트롤러를 찾을 수 없습니다."
            return
        }
        var fid = folderController.currentFolderId || ""
        var fname = folderController.currentFolderName || "폴더"
        var scope = "folder"
        if (fid === "smart:all") {
            scope = "all"
        } else if (fid === "smart:favorites") {
            scope = "favorites"
        } else if (!fid) {
            exportStatusError = true
            exportStatusMessage = "내보낼 폴더를 선택해주세요."
            return
        }

        folderExportMode = true
        folderExportScope = scope
        folderExportFolderId = (scope === "folder") ? fid : ""
        folderExportLabel = fname

        // PDF는 폴더 일괄 내보내기에서 지원하지 않음 → 기본 hwpx로 보정
        if ((exportFormat || "").toLowerCase() === "pdf") {
            exportFormat = "hwpx"
        }
        exportStatusMessage = ""
        exportStatusError = false
        exportLastOutputPath = ""
        currentNoteExportDialog.visible = true
    }

    function runFolderImport(srcDir, includeSubfolders) {
        if (!folderImportController) {
            window.importStatusError = true
            window.importStatusMessage = "가져오기 컨트롤러를 찾을 수 없습니다."
            importStatusTimer.restart()
            return
        }
        if (!srcDir) return

        var parentId = ""
        if (folderController) {
            var fid = folderController.currentFolderId || ""
            if (fid && !folderController.isSmartFolder(fid)) {
                parentId = fid
            }
        }

        window.importBusy = true
        window.importStatusError = false
        window.importStatusMessage = "가져오는 중..."
        window.importProgressValue = 0
        window.importProgressTotal = 0

        folderImportController.importDirectoryAsync(srcDir, parentId, includeSubfolders)
    }

    function resolveNoteCreationFolderId(folderId) {
        if (!folderController) return ""
        var fid = folderId || ""
        if (!fid || folderController.isSmartFolder(fid)) {
            fid = folderController.getFirstRegularFolderId()
        }
        return fid || ""
    }

    function resolveTemplateDialogFolderId(folderId) {
        if (!folderController) return ""
        var fid = folderId || ""
        if (!fid || folderController.isSmartFolder(fid)) return ""
        return fid
    }

    function refreshSelectableFolderItems() {
        var items = []
        if (folderController && folderController.folders) {
            for (var i = 0; i < folderController.folders.length; i++) {
                var folder = folderController.folders[i]
                if (folder && !folder.is_smart) {
                    items.push(folder)
                }
            }
        }
        selectableFolderItems = items

        if (batchTargetFolderId) {
            var stillValid = false
            for (var j = 0; j < items.length; j++) {
                if (items[j] && String(items[j].id || "") === batchTargetFolderId) {
                    stillValid = true
                    break
                }
            }
            if (!stillValid) {
                batchTargetFolderId = ""
                batchTargetFolderName = ""
            }
        }

        if (batchActionMode || batchFolderPickerDialog.visible) {
            refreshBatchFolderHint()
        }
    }

    function getCurrentRegularFolderId() {
        if (!folderController) return ""
        var currentId = String(folderController.currentFolderId || "").trim()
        if (!currentId || folderController.isSmartFolder(currentId)) return ""
        return currentId
    }

    function getDefaultBatchTargetFolderId() {
        var currentId = getCurrentRegularFolderId()
        for (var i = 0; i < selectableFolderItems.length; i++) {
            var item = selectableFolderItems[i]
            if (item && item.id && String(item.id) !== currentId) {
                return String(item.id)
            }
        }
        return ""
    }

    function hasBatchFolderTargets() {
        return getDefaultBatchTargetFolderId() !== ""
    }

    function isBatchTargetFolderUsable(folderId) {
        var cleanId = String(folderId || "").trim()
        if (!cleanId) return false
        if (!batchActionMode) return false

        var currentId = getCurrentRegularFolderId()
        if (currentId && cleanId === currentId) {
            return false
        }

        for (var i = 0; i < selectableFolderItems.length; i++) {
            var item = selectableFolderItems[i]
            if (item && String(item.id || "") === cleanId) {
                return true
            }
        }
        return false
    }

    function refreshBatchFolderHint() {
        if (!selectableFolderItems || selectableFolderItems.length === 0) {
            batchFolderHintMessage = "선택할 수 있는 대상 폴더가 없습니다."
            return
        }

        var currentId = getCurrentRegularFolderId()
        var hasAlternateFolder = false
        for (var i = 0; i < selectableFolderItems.length; i++) {
            var item = selectableFolderItems[i]
            if (item && String(item.id || "") !== currentId) {
                hasAlternateFolder = true
                break
            }
        }

        if (!hasAlternateFolder) {
            batchFolderHintMessage = "현재 폴더와 다른 대상 폴더가 필요합니다."
        } else {
            batchFolderHintMessage = "이동/복사할 대상 폴더를 선택하세요. 스마트 폴더는 제외됩니다."
        }
    }

    function reorderFolderInSidebar(direction) {
        if (!folderController || !folderMoveSourceId) return false
        return folderController.reorderFolder(folderMoveSourceId, direction)
    }

    // ========== Draft Model Functions for Folder Placement ==========

    function buildFolderPlacementDraft() {
        if (!folderController || !templateDialogFolderId) return

        var sourceId = templateDialogFolderId
        var sourceFolder = folderController.getFolder(sourceId)
        if (!sourceFolder) return

        var sourceParentId = sourceFolder.parent_id !== undefined && sourceFolder.parent_id !== null ? String(sourceFolder.parent_id) : ""

        originalFolderSnapshot = []
        folderSettingsDraftItems = []
        folderMovePreviewItems = []

        if (folderController.folders) {
            for (var i = 0; i < folderController.folders.length; i++) {
                var f = folderController.folders[i]
                if (!f || f.is_smart) continue

                var originalCopy = {
                    id: String(f.id || ""),
                    name: f.name || "",
                    parent_id: f.parent_id !== undefined && f.parent_id !== null ? String(f.parent_id) : "",
                    sort_order: f.sort_order || 0,
                    depth: f.depth || 0,
                    color: f.color || Colors.primary400,
                    is_smart: false
                }
                var draftCopy = {
                    id: originalCopy.id,
                    name: originalCopy.name,
                    parent_id: originalCopy.parent_id,
                    sort_order: originalCopy.sort_order,
                    depth: originalCopy.depth,
                    color: originalCopy.color,
                    is_smart: originalCopy.is_smart
                }
                originalFolderSnapshot.push(originalCopy)
                folderSettingsDraftItems.push(draftCopy)
            }
        }

        folderMoveSourceId = sourceId
        folderMoveSourceName = templateDialogFolderName || ""
        draftParentId = sourceParentId

        selectedMoveTargetId = sourceParentId
        var initialTarget = sourceParentId ? getDraftFolderById(sourceParentId) : null
        selectedMoveTargetName = initialTarget ? initialTarget.name : "최상위"
        folderPlacementStatusMessage = ""
        folderPlacementStatusError = false
        folderPlacementChangeCounter = 0

        refreshFolderPlacementDraftViews()
    }

    function resetFolderPlacementDraft() {
        originalFolderSnapshot = []
        folderSettingsDraftItems = []
        folderMovePreviewItems = []
        selectedMoveTargetId = ""
        selectedMoveTargetName = "최상위"
        draftParentId = ""
        draftOrderItems = []
        folderPlacementStatusMessage = ""
        folderPlacementStatusError = false
        folderMoveSourceId = ""
        folderMoveSourceName = ""
        folderPlacementChangeCounter = 0
    }

    function getDraftFolderById(folderId) {
        for (var i = 0; i < folderSettingsDraftItems.length; i++) {
            if (folderSettingsDraftItems[i] && String(folderSettingsDraftItems[i].id) === folderId) {
                return folderSettingsDraftItems[i]
            }
        }
        return null
    }

    function getDescendantIdsInDraft(folderId) {
        var descendants = []
        var queue = [folderId]
        while (queue.length > 0) {
            var current = queue.shift()
            for (var i = 0; i < folderSettingsDraftItems.length; i++) {
                var f = folderSettingsDraftItems[i]
                if (f && String(f.parent_id) === current) {
                    descendants.push(f.id)
                    queue.push(f.id)
                }
            }
        }
        return descendants
    }

    function buildDraftFolderPreviewItems() {
        var result = []
        function appendChildren(parentId, depth) {
            var children = []
            for (var i = 0; i < folderSettingsDraftItems.length; i++) {
                var f = folderSettingsDraftItems[i]
                if (!f) continue
                var fParentId = f.parent_id !== undefined && f.parent_id !== null ? String(f.parent_id) : ""
                if (fParentId === parentId) {
                    children.push(f)
                }
            }
            children.sort(function(a, b) {
                return (a.sort_order || 0) - (b.sort_order || 0)
            })
            for (var j = 0; j < children.length; j++) {
                var child = children[j]
                result.push({
                    id: child.id,
                    name: child.name,
                    parent_id: child.parent_id,
                    sort_order: child.sort_order,
                    depth: depth,
                    color: child.color,
                    is_smart: child.is_smart
                })
                appendChildren(String(child.id), depth + 1)
            }
        }
        appendChildren("", 0)
        return result
    }

    function refreshFolderPlacementDraftViews() {
        if (!folderMoveSourceId) return

        var sourceId = folderMoveSourceId
        var descendants = getDescendantIdsInDraft(sourceId)

        var moveTargets = [{ id: "", name: "최상위", depth: 0, color: Colors.primary400 }]

        for (var i = 0; i < folderSettingsDraftItems.length; i++) {
            var f = folderSettingsDraftItems[i]
            if (!f) continue

            var fid = String(f.id)
            if (fid === sourceId) continue
            if (descendants.indexOf(fid) !== -1) continue

            var copy = {
                id: f.id,
                name: f.name,
                parent_id: f.parent_id,
                sort_order: f.sort_order,
                depth: f.depth,
                color: f.color,
                is_smart: f.is_smart
            }
            moveTargets.push(copy)
        }

        folderMoveTargetItems = moveTargets
        folderMovePreviewItems = buildDraftFolderPreviewItems()
        console.log("[refreshFolderPlacementDraftViews] folderMoveTargetItems length:", folderMoveTargetItems.length, "selectedMoveTargetId:", selectedMoveTargetId)

        var currentDraft = getDraftFolderById(sourceId)
        var currentParentId = currentDraft ? currentDraft.parent_id : ""

        var siblings = []
        for (var j = 0; j < folderSettingsDraftItems.length; j++) {
            var sf = folderSettingsDraftItems[j]
            if (!sf) continue

            var sfParentId = sf.parent_id !== undefined && sf.parent_id !== null ? String(sf.parent_id) : ""
            if (sfParentId === currentParentId) {
                var siblingCopy = {
                    id: sf.id,
                    name: sf.name,
                    parent_id: sf.parent_id,
                    sort_order: sf.sort_order,
                    depth: sf.depth,
                    color: sf.color,
                    is_smart: sf.is_smart
                }
                siblings.push(siblingCopy)
            }
        }

        siblings.sort(function(a, b) {
            return (a.sort_order || 0) - (b.sort_order || 0)
        })

        draftOrderItems = siblings
        console.log("[refreshFolderPlacementDraftViews] draftOrderItems length:", draftOrderItems.length)
    }

    function hasFolderPlacementChanges() {
        if (!folderMoveSourceId || originalFolderSnapshot.length === 0) return false

        var currentDraft = getDraftFolderById(folderMoveSourceId)
        if (!currentDraft) return false

        for (var i = 0; i < originalFolderSnapshot.length; i++) {
            var orig = originalFolderSnapshot[i]
            if (orig && String(orig.id) === folderMoveSourceId) {
                if (String(orig.parent_id || "") !== String(currentDraft.parent_id || "")) {
                    return true
                }
                if ((orig.sort_order || 0) !== (currentDraft.sort_order || 0)) {
                    return true
                }
                break
            }
        }

        return false
    }

    function canPreviewFolderMove() {
        if (!folderMoveSourceId) return false

        var currentDraft = getDraftFolderById(folderMoveSourceId)
        if (!currentDraft) return false

        var targetId = selectedMoveTargetId !== undefined && selectedMoveTargetId !== null
            ? String(selectedMoveTargetId)
            : ""

        var currentParentId = String(currentDraft.parent_id || "")
        if (targetId === currentParentId) {
            return false
        }

        return isValidMoveTarget(targetId)
    }

    function isValidMoveTarget(targetId) {
        if (!targetId) return true
        if (targetId === folderMoveSourceId) return false

        var descendants = getDescendantIdsInDraft(folderMoveSourceId)
        if (descendants.indexOf(targetId) !== -1) return false

        return true
    }

    function moveFolderInDraftOnly(targetParentId) {
        console.log("[moveFolderInDraftOnly] targetParentId:", targetParentId)
        if (!folderMoveSourceId) {
            console.log("[moveFolderInDraftOnly] no folderMoveSourceId")
            return
        }

        if (!isValidMoveTarget(targetParentId)) {
            console.log("[moveFolderInDraftOnly] invalid target")
            folderPlacementStatusMessage = "이동할 수 없는 대상입니다."
            folderPlacementStatusError = true
            return
        }

        var newSortOrder = 1
        for (var j = 0; j < folderSettingsDraftItems.length; j++) {
            var sf = folderSettingsDraftItems[j]
            if (!sf) continue
            var sfParentId = sf.parent_id !== undefined && sf.parent_id !== null ? String(sf.parent_id) : ""
            if (sfParentId === targetParentId && String(sf.id) !== folderMoveSourceId) {
                newSortOrder = Math.max(newSortOrder, (sf.sort_order || 0) + 1)
            }
        }

        console.log("[moveFolderInDraftOnly] newSortOrder:", newSortOrder)

        for (var i = 0; i < folderSettingsDraftItems.length; i++) {
            var f = folderSettingsDraftItems[i]
            if (f && String(f.id) === folderMoveSourceId) {
                f.parent_id = targetParentId
                f.sort_order = newSortOrder
                console.log("[moveFolderInDraftOnly] updated draft item parent_id to:", targetParentId)
                break
            }
        }

        // Force QML property change notification
        folderSettingsDraftItems = folderSettingsDraftItems.slice()

        draftParentId = targetParentId
        selectedMoveTargetId = targetParentId

        var targetFolder = getDraftFolderById(targetParentId)
        selectedMoveTargetName = targetFolder ? targetFolder.name : "최상위"

        folderPlacementStatusMessage = "미리보기: '" + folderMoveSourceName + "' → '" + selectedMoveTargetName + "'"
        folderPlacementStatusError = false
        folderPlacementChangeCounter++

        console.log("[moveFolderInDraftOnly] calling refreshFolderPlacementDraftViews")
        refreshFolderPlacementDraftViews()

        // Update ListView currentIndex to match selectedMoveTargetId
        for (var m = 0; m < folderMoveTargetItems.length; m++) {
            var item = folderMoveTargetItems[m]
            if (item && String(item.id || "") === targetParentId) {
                folderMoveListViewIntegrated.currentIndex = m
                break
            }
        }

        console.log("[moveFolderInDraftOnly] after refresh, folderMoveTargetItems length:", folderMoveTargetItems.length, "currentIndex:", folderMoveListViewIntegrated.currentIndex)
    }

    function reorderFolderInDraftOnly(direction) {
        if (!folderMoveSourceId || draftOrderItems.length <= 1) return

        var currentIndex = -1
        for (var i = 0; i < draftOrderItems.length; i++) {
            if (draftOrderItems[i] && String(draftOrderItems[i].id) === folderMoveSourceId) {
                currentIndex = i
                break
            }
        }

        if (currentIndex < 0) return

        if (direction === -1 && currentIndex === 0) return
        if (direction === 1 && currentIndex === draftOrderItems.length - 1) return

        var targetIndex = direction === -1 ? currentIndex - 1 : currentIndex + 1

        var temp = draftOrderItems[currentIndex]
        draftOrderItems[currentIndex] = draftOrderItems[targetIndex]
        draftOrderItems[targetIndex] = temp

        for (var j = 0; j < draftOrderItems.length; j++) {
            var f = draftOrderItems[j]
            if (f) {
                f.sort_order = j + 1
            }
        }

        for (var k = 0; k < folderSettingsDraftItems.length; k++) {
            var df = folderSettingsDraftItems[k]
            if (df && String(df.id) === folderMoveSourceId) {
                df.sort_order = targetIndex + 1
                break
            }
        }

        // Force QML property change notification
        draftOrderItems = draftOrderItems.slice()
        folderSettingsDraftItems = folderSettingsDraftItems.slice()

        folderPlacementStatusMessage = "미리보기: 순서 변경됨"
        folderPlacementStatusError = false
        folderPlacementChangeCounter++
    }

    function applyFolderPlacementChanges(closeDialog) {
        console.log("[applyFolderPlacementChanges] closeDialog:", closeDialog, "hasChanges:", hasFolderPlacementChanges())
        if (!hasFolderPlacementChanges()) {
            console.log("[applyFolderPlacementChanges] no changes, returning")
            if (closeDialog) {
                templateManagerDialog.visible = false
                resetFolderPlacementDraft()
            }
            return
        }

        var currentDraft = getDraftFolderById(folderMoveSourceId)
        if (!currentDraft) {
            console.log("[applyFolderPlacementChanges] no currentDraft")
            folderPlacementStatusMessage = "폴더 정보를 찾을 수 없습니다."
            folderPlacementStatusError = true
            return
        }

        var newParentId = currentDraft.parent_id || ""
        var newSortOrder = currentDraft.sort_order || 0
        console.log("[applyFolderPlacementChanges] newParentId:", newParentId, "newSortOrder:", newSortOrder)

        var originalSnapshot = null
        for (var i = 0; i < originalFolderSnapshot.length; i++) {
            if (originalFolderSnapshot[i] && String(originalFolderSnapshot[i].id) === folderMoveSourceId) {
                originalSnapshot = originalFolderSnapshot[i]
                break
            }
        }
        var originalParentId = originalSnapshot ? (originalSnapshot.parent_id || "") : ""
        var originalSortOrder = originalSnapshot ? (originalSnapshot.sort_order || 0) : 0
        console.log("[applyFolderPlacementChanges] originalParentId:", originalParentId, "originalSortOrder:", originalSortOrder)

        var success = false
        var parentChanged = (newParentId !== originalParentId)
        var orderChanged = (newSortOrder !== originalSortOrder)

        if (parentChanged) {
            console.log("[applyFolderPlacementChanges] parent changed, calling moveFolder")
            success = folderController.moveFolder(folderMoveSourceId, newParentId)
            console.log("[applyFolderPlacementChanges] moveFolder result:", success)
        } else if (orderChanged) {
            console.log("[applyFolderPlacementChanges] order changed only, calling updatePlacement")
            // Use updatePlacement to move to specific index in one operation
            success = folderController.updateFolderPlacement(folderMoveSourceId, newParentId, newSortOrder - 1)
            console.log("[applyFolderPlacementChanges] updateFolderPlacement result:", success)
        }

        if (success) {
            folderPlacementStatusMessage = parentChanged ? "이동이 완료되었습니다." : "순서 변경이 완료되었습니다."
            folderPlacementStatusError = false
            if (closeDialog) {
                templateManagerDialog.visible = false
                resetFolderPlacementDraft()
            }
        } else {
            folderPlacementStatusMessage = parentChanged ? "폴더 이동에 실패했습니다." : "순서 변경에 실패했습니다."
            folderPlacementStatusError = true
        }
    }

    function setupFolderOrderData() {
        if (!folderController || !templateDialogFolderId) return

        refreshSelectableFolderItems()
        var currentFolderId = templateDialogFolderId
        var currentFolder = folderController.getFolder(currentFolderId)
        var parentFolderId = currentFolder && currentFolder.parent_id ? String(currentFolder.parent_id) : ""

        var siblings = []
        for (var i = 0; i < selectableFolderItems.length; i++) {
            var item = selectableFolderItems[i]
            if (!item) continue

            var itemParentId = item.parent_id !== undefined && item.parent_id !== null ? String(item.parent_id) : ""
            if (itemParentId === parentFolderId && String(item.id) !== currentFolderId) {
                siblings.push(item)
            }
        }
        folderOrderSiblingItems = siblings
    }

    function clearNoteSelectionState() {
        noteSelectionMode = false
        selectedNoteIds = []
        batchActionMode = ""
        batchTargetFolderId = ""
        batchTargetFolderName = ""
        batchFolderHintMessage = ""
        batchFolderPickerDialog.visible = false
        batchDeleteConfirmDialog.visible = false
    }

    function enterNoteSelectionMode() {
        noteSelectionMode = true
        if (!selectedNoteIds) selectedNoteIds = []
        // Defer folder refresh to avoid blocking UI
        Qt.callLater(function() {
            if (!selectableFolderItems || selectableFolderItems.length === 0) {
                refreshSelectableFolderItems()
            }
        })
    }

    function exitNoteSelectionMode() {
        clearNoteSelectionState()
    }

    function collectSelectedNoteIds() {
        var result = []
        var seen = {}
        for (var i = 0; i < (selectedNoteIds || []).length; i++) {
            var noteId = String(selectedNoteIds[i] || "").trim()
            if (noteId && !seen[noteId]) {
                seen[noteId] = true
                result.push(noteId)
            }
        }
        return result
    }

    function isNoteSelected(noteId) {
        var cleanId = String(noteId || "").trim()
        if (!cleanId) return false
        return selectedNoteIds.indexOf(cleanId) !== -1
    }

    function toggleNoteSelection(noteId) {
        var cleanId = String(noteId || "").trim()
        if (!cleanId) return
        var ids = collectSelectedNoteIds().slice()
        var idx = ids.indexOf(cleanId)
        if (idx >= 0) {
            ids.splice(idx, 1)
        } else {
            ids.push(cleanId)
        }
        selectedNoteIds = ids
        noteSelectionMode = true
    }

    function selectedNoteCount() {
        return collectSelectedNoteIds().length
    }

    function getVisibleNoteIds() {
        var ids = []
        if (!noteController || !noteController.filteredNotes) return ids
        for (var i = 0; i < noteController.filteredNotes.length; i++) {
            var note = noteController.filteredNotes[i]
            var noteId = note && note.id ? String(note.id).trim() : ""
            if (noteId) ids.push(noteId)
        }
        return ids
    }

    function isAllVisibleNotesSelected() {
        var ids = getVisibleNoteIds()
        if (!ids.length) return false
        for (var i = 0; i < ids.length; i++) {
            if (!isNoteSelected(ids[i])) return false
        }
        return true
    }

    function toggleSelectAllVisibleNotes() {
        var ids = getVisibleNoteIds()
        if (!ids.length) return

        if (isAllVisibleNotesSelected()) {
            clearNoteSelectionState()
            return
        }

        selectedNoteIds = ids
        noteSelectionMode = true
    }

    function syncSelectionAfterFolderChange() {
        clearNoteSelectionState()
    }

    function applyBatchNoteAction() {
        if (!noteController) return false
        var ids = collectSelectedNoteIds()
        if (!ids.length || !batchTargetFolderId) return false

        var ok = false
        if (batchActionMode === "move") {
            ok = noteController.moveNotesToFolder(ids, batchTargetFolderId)
        } else if (batchActionMode === "copy") {
            ok = noteController.copyNotesToFolder(ids, batchTargetFolderId)
        }

        if (ok) {
            clearNoteSelectionState()
        }
        return ok
    }

    function openBatchFolderPicker(actionMode) {
        if (!folderController) return
        refreshSelectableFolderItems()
        batchActionMode = actionMode
        batchTargetFolderId = getDefaultBatchTargetFolderId()
        batchTargetFolderName = ""
        for (var i = 0; i < selectableFolderItems.length; i++) {
            var folder = selectableFolderItems[i]
            if (folder && String(folder.id || "") === batchTargetFolderId) {
                batchTargetFolderName = folder.name || ""
                break
            }
        }
        refreshBatchFolderHint()
        batchFolderPickerDialog.visible = true
    }

    function openBatchDeleteConfirm() {
        if (!selectedNoteCount()) return
        batchDeleteConfirmDialog.visible = true
    }

    function closeTabsForDeletedNotes(noteIds) {
        var idSet = {}
        for (var i = 0; i < (noteIds || []).length; i++) {
            var cleanId = String(noteIds[i] || "").trim()
            if (cleanId) idSet[cleanId] = true
        }

        var remaining = []
        for (var j = 0; j < openTabs.length; j++) {
            var tab = openTabs[j]
            if (tab && !idSet[tab.id]) {
                remaining.push(tab)
            }
        }
        openTabs = remaining

        if (selectedNoteId && idSet[selectedNoteId]) {
            if (noteController) noteController.selectNote("")
            selectedNoteId = ""
            currentNote = null
        }
    }

    function getTemplateById(templateId) {
        if (!templateId || !templateController) return null
        var templateObj = templateController.getTemplate(templateId)
        if (!templateObj || templateObj.id === undefined) return null
        return templateObj
    }

    function getDefaultTemplateForFolder(folderId) {
        if (!folderController || !templateController || !folderId) return null
        var templateId = folderController.getFolderDefaultTemplateId(folderId)
        if (!templateId) return null
        return getTemplateById(templateId)
    }

    function refreshTemplateSelectionItems() {
        var items = [{ id: "", name: "기본 템플릿 없음" }]
        var list = templateController ? templateController.templates : []
        for (var i = 0; i < list.length; i++) {
            items.push({
                id: list[i].id,
                name: (list[i].name && list[i].name.length > 0) ? list[i].name : "이름 없는 템플릿"
            })
        }
        templateSelectionItems = items
    }

    function indexOfTemplateSelection(templateId) {
        var targetId = templateId || ""
        for (var i = 0; i < templateSelectionItems.length; i++) {
            if ((templateSelectionItems[i].id || "") === targetId) {
                return i
            }
        }
        return 0
    }

    function extractTitleFromContent(content) {
        if (!content) return ""
        var lines = content.split(/\r?\n/)
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim()
            if (!line) continue
            var m = line.match(/^#+\s+(.*)$/)
            if (m) return m[1].trim()
            return line
        }
        return ""
    }

    function clearTemplateEditor() {
        templateEditId = ""
        templateEditName = ""
        templateEditTitle = ""
        templateEditContent = ""
    }

    function loadTemplateEditor(templateId) {
        var templateObj = getTemplateById(templateId)
        if (!templateObj) {
            clearTemplateEditor()
            return
        }
        templateEditId = templateObj.id || ""
        templateEditName = templateObj.name || ""
        templateEditContent = templateObj.content || ""
        templateEditTitle = templateObj.title || extractTitleFromContent(templateEditContent)
    }

    function openTemplateManagerDialog() {
        if (!folderController) return

        var selectedFolderId = folderController.currentFolderId || ""
        if (!selectedFolderId || folderController.isSmartFolder(selectedFolderId)) {
            return
        }

        refreshTemplateSelectionItems()
        templateDialogFolderId = resolveTemplateDialogFolderId(selectedFolderId)
        templateDialogFolderName = "현재 폴더 없음"
        templateSelectedDefaultId = ""
        folderSettingsMenuIndex = 0

        if (templateDialogFolderId && folderController) {
            var folderObj = folderController.getFolder(templateDialogFolderId)
            templateDialogFolderName = (folderObj && folderObj.name !== undefined)
                ? folderObj.name : (folderController.currentFolderName || "현재 폴더")
            folderRenameEditName = templateDialogFolderName
            templateDialogFolderPath = folderController.getFolderPath(templateDialogFolderId) || ""
            templateSelectedDefaultId = folderController.getFolderDefaultTemplateId(templateDialogFolderId) || ""

            buildFolderPlacementDraft()
        }

        templateStatusMessage = ""
        templateStatusError = false
        clearTemplateEditor()
        templateManagerDialog.visible = true
    }

    function saveFolderNameSetting() {
        if (!folderController || !templateDialogFolderId) return

        var cleanName = (folderRenameEditName || "").trim()
        if (!cleanName) {
            templateStatusError = true
            templateStatusMessage = "폴더 이름을 입력해주세요."
            return
        }

        if (folderController.renameFolder(templateDialogFolderId, cleanName)) {
            templateDialogFolderName = cleanName
            templateStatusError = false
            templateStatusMessage = "폴더 이름이 변경되었습니다."
        } else {
            templateStatusError = true
            templateStatusMessage = "폴더 이름 변경에 실패했습니다."
        }
    }

    function canOpenFolderSettingsDialog() {
        if (!folderController) return false
        var fid = folderController.currentFolderId || ""
        return !!fid && !folderController.isSmartFolder(fid)
    }

    function saveTemplateEditor() {
        if (!templateController) return

        var cleanName = (templateEditName || "").trim()
        if (!cleanName) {
            templateStatusError = true
            templateStatusMessage = "템플릿 이름을 입력해주세요."
            return
        }

        var derivedTitle = extractTitleFromContent(templateEditContent)
        var ok = false
        if (templateEditId) {
            ok = templateController.updateTemplate(
                templateEditId,
                cleanName,
                derivedTitle,
                templateEditContent || ""
            )
            if (ok) {
                templateStatusError = false
                templateStatusMessage = "템플릿이 저장되었습니다."
            }
        } else {
            var newId = templateController.createTemplate(
                cleanName,
                derivedTitle,
                templateEditContent || ""
            )
            ok = !!newId
            if (ok) {
                refreshTemplateSelectionItems()
                loadTemplateEditor(newId)
                templateStatusError = false
                templateStatusMessage = "템플릿이 생성되었습니다."
            }
        }

        if (!ok) {
            templateStatusError = true
            templateStatusMessage = "템플릿 저장에 실패했습니다."
            return
        }

        refreshTemplateSelectionItems()
    }

    function deleteCurrentTemplate() {
        if (!templateController || !templateEditId) return

        var deletedId = templateEditId
        if (templateController.deleteTemplate(deletedId)) {
            if (templateSelectedDefaultId === deletedId) {
                templateSelectedDefaultId = ""
            }
            clearTemplateEditor()
            refreshTemplateSelectionItems()
            templateStatusError = false
            templateStatusMessage = "템플릿이 삭제되었습니다."
        } else {
            templateStatusError = true
            templateStatusMessage = "템플릿 삭제에 실패했습니다."
        }
    }

    function applySelectedFolderTemplate() {
        if (!folderController || !templateDialogFolderId) {
            templateStatusError = true
            templateStatusMessage = "기본 템플릿을 설정할 일반 폴더를 먼저 선택해주세요."
            return
        }

        if (folderController.setFolderDefaultTemplate(templateDialogFolderId, templateSelectedDefaultId || "")) {
            templateStatusError = false
            templateStatusMessage = "폴더 기본 템플릿이 저장되었습니다."
        } else {
            templateStatusError = true
            templateStatusMessage = "폴더 기본 템플릿 저장에 실패했습니다."
        }
    }

    function startFolderExport() {
        if (!exportOutputDir || exportOutputDir.length === 0) {
            exportStatusError = true
            exportStatusMessage = "출력 폴더를 선택해주세요."
            return
        }
        var fmt = (exportFormat || "").toLowerCase()
        if (fmt === "pdf") {
            exportStatusError = true
            exportStatusMessage = "PDF는 폴더 일괄 내보내기에서 지원하지 않습니다."
            return
        }
        if (!currentExportController) {
            exportStatusError = true
            exportStatusMessage = "내보내기 컨트롤러를 찾을 수 없습니다."
            return
        }

        window.exportBusy = true
        window.exportStatusMessage = "내보내는 중..."
        window.exportProgressValue = 0
        window.exportProgressTotal = 0

        flushSaveIfDirty()
        currentExportController.exportFolderNotesAsync(
            folderExportScope,
            folderExportFolderId,
            fmt,
            exportOutputDir
        )
    }

    function _buildCurrentExportPath(fmt) {
        var safeTitle = (currentExportController && currentExportController.safeFilename)
            ? currentExportController.safeFilename(exportDraftTitle || "무제")
            : (exportDraftTitle || "무제")
        var normalized = (exportOutputDir || "").replace(/\\/g, "/")
        if (!normalized) return ""
        return normalized + "/" + safeTitle + "." + fmt
    }

    function startCurrentNoteExport() {
        if (!exportOutputDir || exportOutputDir.length === 0) {
            exportStatusError = true
            exportStatusMessage = "출력 폴더를 선택해주세요."
            return
        }

        var fmt = (exportFormat || "").toLowerCase()
        if (fmt === "pdf") {
            if (!noteEditor || !noteEditor.exportCurrentPdf) {
                exportStatusError = true
                exportStatusMessage = "PDF 내보내기를 실행할 수 없습니다."
                return
            }
            var pdfPath = _buildCurrentExportPath("pdf")
            if (!pdfPath) {
                exportStatusError = true
                exportStatusMessage = "출력 경로를 만들 수 없습니다."
                return
            }
            flushSaveIfDirty()
            window.exportBusy = true
            exportStatusError = false
            exportStatusMessage = "PDF 생성 중..."
            exportLastOutputPath = ""
            noteEditor.exportCurrentPdf(pdfPath)
            // PDF export is async; onPdfExportFinished will set exportBusy=false
            return
        }

        if (!currentExportController) {
            exportStatusError = true
            exportStatusMessage = "내보내기 컨트롤러를 찾을 수 없습니다."
            return
        }

        window.exportBusy = true
        window.exportStatusMessage = "보내는 중..."

        flushSaveIfDirty()
        currentExportController.exportCurrentNoteAsync(
            exportDraftTitle || "무제",
            exportDraftMarkdown || "",
            exportDraftJson || "",
            fmt,
            exportOutputDir
        )
    }

    function addOrActivateTab(noteId, noteTitle) {
        for (var i = 0; i < openTabs.length; i++) {
            if (openTabs[i].id === noteId) return
        }
        var t = openTabs.slice()
        t.push({ id: noteId, title: noteTitle || "제목 없음" })
        openTabs = t
    }

    function updateTabTitle(noteId, title) {
        if (!title) return
        for (var i = 0; i < openTabs.length; i++) {
            if (openTabs[i].id === noteId) {
                var t = openTabs.slice()
                t[i] = { id: noteId, title: title }
                openTabs = t
                return
            }
        }
    }

    function startDraftNote() {
        isDraftNewNote = true
        draftFolderId = resolveNoteCreationFolderId(folderController ? folderController.currentFolderId : "")
        selectedNoteId = ""
        var templateObj = getDefaultTemplateForFolder(draftFolderId)
        var folderObj = (folderController && draftFolderId)
            ? folderController.getFolder(draftFolderId) : null
        var folderName = (folderObj && folderObj.name !== undefined)
            ? (folderObj.name || "") : ""
        var renderedTemplate = (templateObj && templateObj.id !== undefined && templateController)
            ? templateController.renderTemplate(templateObj.id, draftFolderId, folderName)
            : null
        var initialTitle = (renderedTemplate && renderedTemplate.title !== undefined)
            ? (renderedTemplate.title || "")
            : (templateObj ? (templateObj.title || "") : "")
        var initialContent = (renderedTemplate && renderedTemplate.content !== undefined)
            ? (renderedTemplate.content || "")
            : (templateObj ? (templateObj.content || "") : "")
        titleTouchedByUser = !!(initialTitle && initialTitle.trim())
        currentNote = { title: initialTitle, content: initialContent, content_json: "" }
        if (noteEditor) {
            noteEditor.resetEditor(initialContent, "")
            noteEditor.focusContent()
        }
    }

    function ensureDraftPersisted(newTitle, newMarkdown, newJson) {
        console.log("[ensureDraftPersisted] called title=" + (newTitle || "(empty)")
                    + " mdLen=" + (newMarkdown ? newMarkdown.length : 0))
        if (!isDraftNewNote || !noteController) {
            console.log("[ensureDraftPersisted] skip: draft=" + isDraftNewNote + " ctrl=" + !!noteController)
            return selectedNoteId
        }
        var titleText = (newTitle || "").trim()
        if (!titleText) {
            console.log("[ensureDraftPersisted] skip: empty title")
            return ""
        }

        // Save current editor state before transition
        // Prefer latest payload from contentUpdated to avoid losing trailing chars.
        var editorState = {
            title: (newTitle !== undefined && newTitle !== null) ? newTitle : noteEditor.title,
            content: (newMarkdown !== undefined && newMarkdown !== null) ? newMarkdown : noteEditor.content,
            contentJson: (newJson !== undefined && newJson !== null) ? newJson : noteEditor.contentJson
        }

        var targetFolderId = draftFolderId
        if (!targetFolderId && folderController) {
            targetFolderId = folderController.currentFolderId
        }

        var newId = noteController.createNote(titleText, newMarkdown || "", newJson || "", targetFolderId)
        console.log("[ensureDraftPersisted] createNote returned id=" + newId)
        if (!newId) return ""

        isDraftNewNote = false
        selectedNoteId = newId

        // Restore editor state to prevent content loss during re-binding
        Qt.callLater(function() {
            // Only restore if we're still on the newly created note (user hasn't switched away)
            if (window.selectedNoteId !== newId) return
            
            // Update currentNote first so editor binding gets correct values
            window.currentNote = {
                title: editorState.title,
                content: editorState.content,
                content_json: editorState.contentJson
            }
        })

        return newId
    }

    function deriveDraftTitle(titleCandidate, markdownCandidate) {
        var titleText = (titleCandidate || "").trim()
        if (titleText) return titleText

        var md = (markdownCandidate || "")
        if (!md) return ""

        var lines = md.split(/\r?\n/)
        for (var i = 0; i < lines.length; i++) {
            var line = (lines[i] || "").trim()
            if (!line) continue

            // Remove common heading / emphasis markers for title extraction
            line = line.replace(/^#{1,6}\s+/, "")
                       .replace(/\*\*/g, "")
                       .replace(/\*/g, "")
                       .replace(/`/g, "")
                       .trim()

            if (line) return line.substring(0, 100)
        }

        return ""
    }

    function closeTab(noteId) {
        var idx = -1
        for (var i = 0; i < openTabs.length; i++) {
            if (openTabs[i].id === noteId) { idx = i; break }
        }
        if (idx < 0) return
        var t = openTabs.slice()
        t.splice(idx, 1)
        openTabs = t
        if (noteId === selectedNoteId) {
            if (t.length === 0) {
                if (noteController) noteController.selectNote("")
                selectedNoteId = ""
            } else {
                var next = t[Math.min(idx, t.length - 1)]
                if (noteController) noteController.selectNote(next.id)
                selectedNoteId = next.id
            }
        }
    }

    onCurrentNoteChanged: {
        if (currentNote && selectedNoteId) {
            updateTabTitle(selectedNoteId, currentNote.title || "제목 없음")
        }
    }

    onSelectedNoteIdChanged: {
        if (selectedNoteId && noteController) {
            window.isDraftNewNote = false
            window.currentNote = noteController.getNote(selectedNoteId)
            var title = window.currentNote ? (window.currentNote.title || "") : ""
            // Loaded notes: treat existing non-empty title as user-owned so autosave doesn't overwrite it.
            window.titleTouchedByUser = !!(title && title.trim())
            addOrActivateTab(selectedNoteId, title || "제목 없음")
        } else {
            if (!window.isDraftNewNote) {
                window.currentNote = null
            }
        }
    }

    // Library change handling - force refresh
    Connections {
        target: folderController
        function onLibraryChanged() {
            foldersListView.model = null
            foldersListView.model = folderController ? folderController.folders : []
            window.openTabs = []
            window.selectedNoteId = ""
            window.syncSelectionAfterFolderChange()
        }
        function onFoldersChanged() {
            foldersListView.model = null
            foldersListView.model = folderController ? folderController.folders : []
            window.refreshSelectableFolderItems()
        }
        function onCurrentFolderChanged() {
            window.syncSelectionAfterFolderChange()
        }
    }

    Connections {
        target: templateController
        function onTemplatesChanged() {
            window.refreshTemplateSelectionItems()
        }
    }

    Connections {
        target: noteController
        function onLibraryChanged() {
            notesListView.model = null
            notesListView.model = noteController ? noteController.filteredNotes : []
            window.selectedNoteId = ""
            window.syncSelectionAfterFolderChange()
        }
        function onFilteredNotesChanged() {
            var prevSelected = window.selectedNoteId
            notesListView.model = null
            notesListView.model = noteController ? noteController.filteredNotes : []
            window.selectedNoteId = prevSelected
        }
        function onNoteSelected(noteId) {
            window.selectedNoteId = noteId
        }
    }

    // Handle prompt document open requests from AISettingsDialog
    Connections {
        target: typeof promptController !== "undefined" ? promptController : null
        enabled: typeof promptController !== "undefined"
        function onOpenPromptDocumentRequested(prompt_doc_id) {
            console.log("[Main.qml] Open prompt document requested:", prompt_doc_id)
            // Switch to AI prompt mode
            window.activeContentMode = "ai_prompts"
            // Clear note selection
            window.selectedNoteId = ""
            window.currentNote = null
            // Load prompt documents
            if (typeof promptDocumentController !== "undefined" && promptDocumentController) {
                promptDocumentController.loadPromptDocuments()
                promptDocumentController.selectPromptDocument(prompt_doc_id)
            }
        }
    }

    Connections {
        target: typeof promptDocumentController !== "undefined" ? promptDocumentController : null
        enabled: typeof promptDocumentController !== "undefined"
        function onSelectedPromptDocIdChanged() {
            window.selectedAIPromptDocId = promptDocumentController ? (promptDocumentController.selectedPromptDocId || "") : ""
            if (!window.selectedAIPromptDocId) {
                window.promptWarningMessages = []
            }
        }
        function onCurrentPromptDocumentChanged() {
            var currentDoc = promptDocumentController ? promptDocumentController.currentPromptDocument : null
            window.currentAIPromptDocument = currentDoc && Object.keys(currentDoc).length > 0 ? currentDoc : null
            if (window.currentAIPromptDocument && window.currentAIPromptDocument.content_md !== undefined) {
                window.updatePromptWarnings(window.currentAIPromptDocument.content_md || "")
            } else {
                window.promptWarningMessages = []
            }
        }
        function onPromptDocumentsChanged() {
            if (window.activeContentMode === "ai_prompts") {
                window.forcePromptListRefresh()
            }
            if (promptDocumentController && promptDocumentController.promptDocumentList) {
                var docs = promptDocumentController.promptDocumentList
                for (var i = 0; i < docs.length; i++) {
                    if (window.isPromptSample(docs[i])) {
                        window.promptSampleDocId = docs[i].prompt_doc_id || window.promptSampleDocId
                        break
                    }
                }
            }
        }
    }

    Connections {
        target: libraryService
        function onLibrariesChanged() {
            if (libraryRepeater && libraryService) {
                libraryRepeater.model = libraryService.getAllLibraries()
            }
        }
        function onLibraryAdded(libraryId) {
            if (libraryRepeater && libraryService) {
                libraryRepeater.model = libraryService.getAllLibraries()
            }
        }
    }

    Connections {
        target: folderImportController
        function onImportProgress(current, total, message) {
            window.importProgressValue = current
            window.importProgressTotal = total
            window.importStatusMessage = message + " (" + current + "/" + total + ")"
        }
        function onImportFinished(ok, message, rootFolderId, noteCount, folderCount, failedCount) {
            window.importBusy = false
            if (ok) {
                window.importStatusError = false
                window.importStatusMessage = message || "가져오기 완료"
                if (folderController) {
                    // Refresh folder list first
                    folderController.foldersChanged()
                    // Also refresh notes list
                    if (noteController) {
                        noteController.notesChanged()
                        noteController.filteredNotesChanged()
                    }
                    if (rootFolderId) {
                        folderController.selectFolder(rootFolderId)
                    }
                }
            } else {
                window.importStatusError = true
                window.importStatusMessage = message || "가져오기에 실패했습니다."
            }
            importStatusTimer.restart()
        }
    }

    Connections {
        target: currentExportController
        function onExportProgress(current, total, message) {
            window.exportProgressValue = current
            window.exportProgressTotal = total
            window.exportStatusMessage = message + " (" + current + "/" + total + ")"
        }
        function onExportFinished(ok, message, outputPath, count, failedCount) {
            window.exportBusy = false
            if (ok) {
                window.exportStatusError = false
                window.exportStatusMessage = message || "보내기 완료"
                window.exportLastOutputPath = outputPath || ""
            } else {
                window.exportStatusError = true
                window.exportStatusMessage = message || "보내기에 실패했습니다."
                window.exportLastOutputPath = outputPath || ""
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        AppHeader {
            id: appHeader
            Layout.fillWidth: true
            currentNoteExportIconSource: "../assets/icons/export.svg"
            importIconSource: "../assets/icons/import.svg"
            exportIconSource: "../assets/icons/export.svg"
            onLogoClicked: {
                // 사이클: 0=모두 표시 → 1=사이드바 숨김 → 2=모두 숨김 → 0
                var sb = sidebar.Layout.preferredWidth > 0
                var nl = noteList.Layout.preferredWidth > 0
                if (sb && nl) {
                    // State 0 → 1: 사이드바 숨김
                    sidebar.Layout.preferredWidth = 0
                } else if (!sb && nl) {
                    // State 1 → 2: 노트목록도 숨김
                    noteList.Layout.preferredWidth = 0
                } else {
                    // State 2 → 0: 모두 복원
                    sidebar.Layout.preferredWidth = Metrics.sidebarWidth
                    noteList.Layout.preferredWidth = Metrics.noteListWidth
                }
            }
            onImportClicked: {
                importOptionsDialog.visible = true
            }
            onCurrentNoteExportClicked: {
                if (!(window.selectedNoteId !== "" || window.isDraftNewNote)) {
                    window.exportStatusError = true
                    window.exportStatusMessage = "먼저 내보낼 노트를 열어주세요."
                    return
                }
                window.openCurrentExportDialog(
                    window.currentNote ? (window.currentNote.title || "") : "",
                    window.currentNote ? (window.currentNote.content || "") : "",
                    window.currentNote ? (window.currentNote.content_json || "") : ""
                )
            }
            onExportClicked: {
                window.openFolderExportDialog()
            }
            onSettingsClicked: {
                uiScaleDialog.visible = true
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.xs

            Rectangle {
                id: sidebar
                Layout.preferredWidth: Metrics.sidebarWidth
                Layout.fillHeight: true
                color: "transparent"
                z: 3000
                clip: true
                property int sidebarTabIdx: 0  // 0=폴더, 1=태그

                Behavior on Layout.preferredWidth {
                    NumberAnimation { duration: Metrics.durationNormal; easing.type: Easing.InOutQuart }
                }

                MouseArea {
                    anchors.fill: parent
                    visible: folderAddMenu.visible
                    z: 4999
                    onClicked: function(mouse) {
                        if (mouse.x < folderAddMenu.x ||
                            mouse.x > folderAddMenu.x + folderAddMenu.width ||
                            mouse.y < folderAddMenu.y ||
                            mouse.y > folderAddMenu.y + folderAddMenu.height) {
                            folderAddMenu.close()
                        }
                    }
                }

                GlassCard {
                    anchors.fill: parent
                    anchors.margins: Metrics.md
                    anchors.leftMargin: Metrics.lg
                    anchors.rightMargin: 0
                    radius: Metrics.radiusXxl
                    baseOpacity: 0.9

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Metrics.sm
                        spacing: Metrics.sm

                        // Library Selector
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.sm
                            z: 100

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.md

                                Text {
                                    text: "서재"
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightSemibold
                                    font.pixelSize: Typography.caption
                                    color: Colors.textTertiary
                                    font.letterSpacing: Typography.letterSpacingWide
                                }

                                Item { Layout.fillWidth: true }

                                // Add library button (visible next to header)
                                Rectangle {
                                    width: 24
                                    height: 24
                                    radius: Metrics.radiusFull
                                    color: addLibHeaderMouse.containsMouse ? Colors.primary100 : "transparent"
                                    border.width: 1
                                    border.color: addLibHeaderMouse.containsMouse ? Colors.primary200 : "transparent"

                                    Text {
                                        anchors.centerIn: parent
                                        text: "+"
                                        font.pixelSize: 16
                                        color: addLibHeaderMouse.containsMouse ? Colors.primary600 : Colors.primary500
                                    }

                                    MouseArea {
                                        id: addLibHeaderMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: newLibraryDialog.open()
                                    }
                                }

                            }

                            // Library dropdown / selector
                            Rectangle {
                                Layout.fillWidth: true
                                height: 36
                                radius: Metrics.radiusLg
                                color: libraryDropdown.opened ? Colors.bgTertiary : Colors.bgSecondary
                                border.color: libraryDropdown.opened ? Colors.primary200 : "transparent"
                                border.width: 1
                                z: 10  // Ensure dropdown renders above folders list

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: Metrics.md
                                    anchors.rightMargin: Metrics.md
                                    spacing: Metrics.sm

                                    Text {
                                        Layout.fillWidth: true
                                        text: libraryService ? libraryService.currentLibraryName : "내 서재"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: 14
                                        color: Colors.textPrimary
                                        elide: Text.ElideRight
                                    }

                                    Text {
                                        text: libraryDropdown.opened ? "▲" : "▼"
                                        font.pixelSize: 10
                                        color: Colors.textSecondary
                                    }
                                }

                                MouseArea {
                                    id: libraryDropdown
                                    property bool opened: false
                                    anchors.fill: parent
                                    onClicked: opened = !opened
                                }

                                // Library dropdown menu
                                Rectangle {
                                    visible: libraryDropdown.opened
                                    anchors.top: parent.bottom
                                    anchors.topMargin: Metrics.xs
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    // Calculate height dynamically based on actual Repeater content + 2 extra items
                                    property int totalHeight: {
                                        if (!libraryRepeater || !libraryRepeater.count) {
                                            return 2 * Metrics.sm + 32; // min height for empty state
                                        }
                                        var h = 2 * Metrics.sm; // top/bottom margins
                                        // Repeater count reflects actual library count
                                        for (var i = 0; i < libraryRepeater.count; i++) {
                                            // Use itemAt to get actual delegate and check its height or modelData
                                            var item = libraryRepeater.itemAt(i);
                                            if (item && item.modelData) {
                                                h += (item.modelData.description ? 48 : 32);
                                            } else {
                                                h += 32; // default height
                                            }
                                            if (i < libraryRepeater.count - 1) h += Metrics.xs;
                                        }
                                        // Add space for 2 extra items so list feels roomy
                                        h += 2 * 32 + 2 * Metrics.xs;
                                        return h;
                                    }
                                    height: Math.min(totalHeight, 500) // cap at 500px, scroll if more
                                    radius: Metrics.radiusLg
                                    color: "white"
                                    border.color: Colors.borderLight
                                    border.width: 1
                                    opacity: 1.0
                                    z: 1000  // Very high z to render above everything
                                    clip: false

                                    // Close dropdown when clicking outside
                                    MouseArea {
                                        id: dropdownOverlay
                                        visible: libraryDropdown.opened
                                        anchors.fill: parent
                                        anchors.margins: -10000  // Cover entire screen
                                        z: -1  // Below the dropdown content but above other UI
                                        onClicked: {
                                            libraryDropdown.opened = false
                                        }
                                    }

                                    // Scrollable content area
                                    Flickable {
                                        anchors.fill: parent
                                        anchors.margins: Metrics.sm
                                        contentHeight: libraryMenuContent.height
                                        clip: true
                                        interactive: contentHeight > height

                                        ColumnLayout {
                                            id: libraryMenuContent
                                            width: parent.width
                                            spacing: Metrics.xs

                                            // Virtual AI Prompt Library (work_ai_editor only)
                                            Rectangle {
                                                Layout.fillWidth: true
                                                height: 32
                                                radius: Metrics.radiusMd
                                                color: aiPromptLibMouse.containsMouse ? Colors.bgTertiary : "transparent"
                                                visible: typeof appVariant !== "undefined" && appVariant === "work_ai_editor"

                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.leftMargin: Metrics.sm
                                                    anchors.rightMargin: Metrics.sm
                                                    spacing: Metrics.sm

                                                    Text {
                                                        Layout.fillWidth: true
                                                        text: "AI 프롬프트"
                                                        font.family: Typography.fontPrimary
                                                        font.weight: window.activeContentMode === "ai_prompts" ? Typography.weightSemibold : Typography.weightRegular
                                                        font.pixelSize: 14
                                                        color: window.activeContentMode === "ai_prompts" ? Colors.primary500 : Colors.textPrimary
                                                    }

                                                    Text {
                                                        text: "●"
                                                        font.pixelSize: 8
                                                        color: "#3B82F6"
                                                        visible: window.activeContentMode === "ai_prompts"
                                                    }
                                                }

                                                MouseArea {
                                                    id: aiPromptLibMouse
                                                    anchors.fill: parent
                                                    hoverEnabled: true
                                                    onClicked: {
                                                        // Save current real library ID before switching
                                                        if (libraryService && libraryService.currentLibraryId) {
                                                            window.lastRealLibraryIdBeforeAIPromptMode = libraryService.currentLibraryId
                                                        }
                                                        // Switch to AI prompt mode without calling libraryService.setCurrentLibrary
                                                        window.activeContentMode = "ai_prompts"
                                                        window.selectedAIPromptDocId = ""
                                                        window.currentAIPromptDocument = null
                                                        // Clear note selection
                                                        window.selectedNoteId = ""
                                                        window.currentNote = null
                                                        // Load prompt documents
                                                        if (typeof promptDocumentController !== "undefined" && promptDocumentController) {
                                                            promptDocumentController.loadPromptDocuments()
                                                        }
                                                        libraryDropdown.opened = false
                                                    }
                                                }
                                            }

                                            // Divider for virtual library
                                            Rectangle {
                                                Layout.fillWidth: true
                                                height: 1
                                                color: Colors.borderLight
                                                visible: typeof appVariant !== "undefined" && appVariant === "work_ai_editor"
                                            }

                                            Repeater {
                                                id: libraryRepeater
                                                model: libraryService ? libraryService.getAllLibraries() : []

                                                delegate: Rectangle {
                                                Layout.fillWidth: true
                                                height: modelData.description ? 48 : 32
                                                radius: Metrics.radiusMd
                                                color: libraryMouse.containsMouse ? Colors.bgTertiary : "transparent"
                                                property int noteCount: libraryService ? libraryService.getLibraryNoteCount(modelData.id) : 0

                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.leftMargin: Metrics.sm
                                                    anchors.rightMargin: Metrics.sm
                                                    spacing: Metrics.sm

                                                    ColumnLayout {
                                                        Layout.fillWidth: true
                                                        spacing: 0

                                                        Text {
                                                            Layout.fillWidth: true
                                                            text: modelData.name
                                                            font.family: Typography.fontPrimary
                                                            font.weight: libraryService && libraryService.currentLibraryId === modelData.id ? Typography.weightSemibold : Typography.weightRegular
                                                            font.pixelSize: 14
                                                            color: libraryService && libraryService.currentLibraryId === modelData.id ? Colors.primary500 : Colors.textPrimary
                                                        }

                                                        Text {
                                                            Layout.fillWidth: true
                                                            text: modelData.description || ""
                                                            font.family: Typography.fontPrimary
                                                            font.weight: Typography.weightRegular
                                                            font.pixelSize: Typography.caption
                                                            color: Colors.textTertiary
                                                            visible: modelData.description
                                                            elide: Text.ElideRight
                                                        }
                                                    }

                                                    Text {
                                                        text: "●"
                                                        font.pixelSize: 8
                                                        color: "#3B82F6"
                                                        visible: libraryService && libraryService.currentLibraryId === modelData.id
                                                    }

                                                    Rectangle {
                                                        width: 18
                                                        height: 18
                                                        radius: Metrics.radiusFull
                                                        color: editLibArea.containsMouse ? Colors.primary100 : "transparent"

                                                        Text {
                                                            anchors.centerIn: parent
                                                            text: "✎"
                                                            font.pixelSize: 10
                                                            color: Colors.textSecondary
                                                        }

                                                        MouseArea {
                                                            id: editLibArea
                                                            anchors.fill: parent
                                                            hoverEnabled: true
                                                            onClicked: {
                                                                newLibraryDialog.openForEdit(modelData.id, modelData.name, modelData.description || "")
                                                                libraryDropdown.opened = false
                                                            }
                                                        }
                                                    }

                                                    Rectangle {
                                                        width: 18
                                                        height: 18
                                                        radius: Metrics.radiusFull
                                                        color: deleteLibArea.containsMouse ? Colors.accentRoseLight : "transparent"
                                                        opacity: noteCount === 0 ? 1.0 : 0.5

                                                        Text {
                                                            anchors.centerIn: parent
                                                            text: "x"
                                                            font.pixelSize: 10
                                                            color: noteCount === 0 ? Colors.accentRose : Colors.textTertiary
                                                        }

                                                        MouseArea {
                                                            id: deleteLibArea
                                                            anchors.fill: parent
                                                            hoverEnabled: true
                                                            onClicked: {
                                                                deleteLibraryDialog.openForLibrary(modelData.id, modelData.name)
                                                                libraryDropdown.opened = false
                                                            }
                                                        }
                                                    }
                                                }

                                                MouseArea {
                                                    id: libraryMouse
                                                    anchors.fill: parent
                                                    anchors.rightMargin: 52
                                                    hoverEnabled: true
                                                    onClicked: {
                                                        libraryService.setCurrentLibrary(modelData.id)
                                                        // Switch back to notes mode if coming from AI prompt mode
                                                        window.activeContentMode = "notes"
                                                        window.selectedAIPromptDocId = ""
                                                        window.currentAIPromptDocument = null
                                                        libraryDropdown.opened = false
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                        // Divider
                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Colors.borderLight
                            z: 0
                        }

                        // ── Tab switcher: 폴더 | 태그 ──────────────────────────
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.leftMargin: Metrics.xs
                            Layout.rightMargin: Metrics.xs
                            spacing: 4

                            // 폴더 tab
                            Rectangle {
                                height: 26
                                width: 54
                                radius: Metrics.radiusMd
                                color: sidebar.sidebarTabIdx === 0 ? Colors.primary500 : (folderTabMA.containsMouse ? Colors.primary50 : "transparent")
                                border.color: sidebar.sidebarTabIdx === 0 ? Colors.primary600 : (folderTabMA.containsMouse ? Colors.primary200 : Colors.borderLight)
                                border.width: 1
                                Text {
                                    anchors.centerIn: parent
                                    text: "폴더"
                                    font.family: Typography.fontPrimary
                                    font.weight: sidebar.sidebarTabIdx === 0 ? Typography.weightSemibold : Typography.weightRegular
                                    font.pixelSize: 11
                                    color: sidebar.sidebarTabIdx === 0 ? "white" : Colors.textSecondary
                                }
                                MouseArea {
                                    id: folderTabMA
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: {
                                        sidebar.sidebarTabIdx = 0
                                        if (noteController) noteController.clearTagFilter()
                                    }
                                }
                            }

                            // 태그 tab
                            Rectangle {
                                height: 26
                                width: 54
                                radius: Metrics.radiusMd
                                color: sidebar.sidebarTabIdx === 1 ? Colors.primary500 : (tagTabMA.containsMouse ? Colors.primary50 : "transparent")
                                border.color: sidebar.sidebarTabIdx === 1 ? Colors.primary600 : (tagTabMA.containsMouse ? Colors.primary200 : Colors.borderLight)
                                border.width: 1
                                Text {
                                    anchors.centerIn: parent
                                    text: "태그"
                                    font.family: Typography.fontPrimary
                                    font.weight: sidebar.sidebarTabIdx === 1 ? Typography.weightSemibold : Typography.weightRegular
                                    font.pixelSize: 11
                                    color: sidebar.sidebarTabIdx === 1 ? "white" : Colors.textSecondary
                                }
                                MouseArea {
                                    id: tagTabMA
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: {
                                        sidebar.sidebarTabIdx = 1
                                        // Auto-select first tag when switching to tag tab
                                        if (noteController && noteController.allTags && noteController.allTags.length > 0) {
                                            var firstTag = noteController.allTags[0]
                                            if (firstTag && firstTag.name) {
                                                noteController.selectTag(firstTag.name)
                                            }
                                        }
                                    }
                                }
                            }

                            Item { Layout.fillWidth: true }

                            Rectangle {
                                id: manageTemplateButton
                                visible: sidebar.sidebarTabIdx === 0
                                width: 28
                                height: 20
                                radius: Metrics.radiusMd
                                color: canOpenFolderSettingsDialog() && manageTemplateArea.containsMouse ? Colors.primary100 : "transparent"
                                border.width: 1
                                border.color: canOpenFolderSettingsDialog() && manageTemplateArea.containsMouse ? Colors.primary200 : "transparent"
                                opacity: canOpenFolderSettingsDialog() ? 1.0 : 0.4

                                MouseArea {
                                    id: manageTemplateArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    enabled: canOpenFolderSettingsDialog()
                                    onClicked: window.openTemplateManagerDialog()
                                }

                                Image {
                                    anchors.centerIn: parent
                                    source: "assets/icons/folder_properties.svg"
                                    sourceSize: Qt.size(16, 16)
                                    opacity: manageTemplateArea.containsMouse ? 1.0 : 0.6
                                }
                            }

                            // Add folder button (폴더 탭에서만 표시)
                            Rectangle {
                                id: addFolderButton
                                visible: sidebar.sidebarTabIdx === 0
                                width: 20
                                height: 20
                                z: 2101
                                radius: Metrics.radiusFull
                                color: addFolderArea.containsMouse ? Colors.primary100 : "transparent"
                                border.width: 1
                                border.color: addFolderArea.containsMouse ? Colors.primary200 : "transparent"

                                Behavior on color {
                                    ColorAnimation { duration: Metrics.durationFast }
                                }

                                MouseArea {
                                    id: addFolderArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: function(mouse) {
                                        // Show folder creation menu
                                        folderAddMenu.open(mouse.x, mouse.y)
                                    }
                                }

                                Text {
                                    anchors.centerIn: parent
                                    text: "+"
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightSemibold
                                    font.pixelSize: 14
                                    color: addFolderArea.containsMouse ? Colors.primary600 : Colors.textTertiary
                                }

                                // Folder creation menu
                                Rectangle {
                                    id: folderAddMenu
                                    parent: window.contentItem
                                    visible: false
                                    property string baseFolderId: ""
                                    x: 0
                                    y: 0
                                    width: 180
                                    height: menuBackground.implicitHeight + (2 * Metrics.sm)
                                    radius: Metrics.radiusMd
                                    color: "#FFFFFF"
                                    border.color: Colors.borderMedium
                                    border.width: 1
                                    z: 10000  // Above all other elements

                                    // Drop shadow using multiple rectangles
                                    Rectangle {
                                        anchors.fill: parent
                                        anchors.margins: -6
                                        color: "transparent"
                                        radius: Metrics.radiusMd + 6
                                        z: -3

                                        Rectangle {
                                            anchors.fill: parent
                                            anchors.margins: 6
                                            color: "#20000000"
                                            radius: Metrics.radiusMd
                                        }
                                    }

                                    Rectangle {
                                        anchors.fill: parent
                                        anchors.margins: -4
                                        color: "transparent"
                                        radius: Metrics.radiusMd + 4
                                        z: -2

                                        Rectangle {
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            color: "#30000000"
                                            radius: Metrics.radiusMd
                                        }
                                    }

                                    Rectangle {
                                        anchors.fill: parent
                                        anchors.margins: -2
                                        color: "transparent"
                                        radius: Metrics.radiusMd + 2
                                        z: -1

                                        Rectangle {
                                            anchors.fill: parent
                                            anchors.margins: 2
                                            color: "#40000000"
                                            radius: Metrics.radiusMd
                                        }
                                    }

                                    function open(mouseX, mouseY) {
                                        var currentId = (folderController && folderController.currentFolderId) ? folderController.currentFolderId : ""
                                        baseFolderId = (folderController && folderController.isSmartFolder(currentId)) ? "" : currentId
                                        var p = addFolderArea.mapToItem(window.contentItem, mouseX, mouseY)
                                        x = p.x + Metrics.xs
                                        y = p.y
                                        visible = true
                                    }

                                    function parentIdOf(folderId) {
                                        if (!folderController || !folderId) return ""
                                        if (folderController.isSmartFolder(folderId)) return ""
                                        var list = folderController.folders
                                        for (var i = 0; i < list.length; i++) {
                                            if (list[i].id === folderId) {
                                                return list[i].parent_id ? list[i].parent_id : ""
                                            }
                                        }
                                        return ""
                                    }

                                    function depthOf(folderId) {
                                        if (!folderController || !folderId) return 0
                                        if (folderController.isSmartFolder(folderId)) return -1
                                        var list = folderController.folders
                                        for (var i = 0; i < list.length; i++) {
                                            if (list[i].id === folderId) {
                                                return list[i].depth || 0
                                            }
                                        }
                                        return 0
                                    }

                                    function canCreateChild() {
                                        if (!baseFolderId) return false
                                        var d = depthOf(baseFolderId)
                                        return d < 2  // Root (0) and child (1) folders can have children, grandchild (2) cannot
                                    }

                                    function close() {
                                        visible = false
                                    }

                                    // Solid white background container
                                    Rectangle {
                                        id: menuBackground
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.top: parent.top
                                        anchors.margins: Metrics.sm
                                        implicitHeight: folderAddColumn.implicitHeight + 8
                                        height: implicitHeight
                                        color: "#FFFFFF"
                                        radius: Metrics.radiusSm

                                        Column {
                                            id: folderAddColumn
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            spacing: 2

                                        // Same level option
                                        Rectangle {
                                            width: parent.width
                                            height: 28
                                            radius: Metrics.radiusSm
                                            color: sameLevelArea.containsMouse ? Colors.primary100 : "#FFFFFF"

                                            Row {
                                                anchors.fill: parent
                                                anchors.leftMargin: 8
                                                spacing: 6

                                                // Icon placeholder
                                                Rectangle {
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    width: 16
                                                    height: 16
                                                    color: "transparent"

                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: "📁"
                                                        font.pixelSize: 12
                                                    }
                                                }

                                                Text {
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    text: "같은 레벨에 생성"
                                                    font.family: Typography.fontPrimary
                                                    font.weight: Typography.weightMedium
                                                    font.pixelSize: 12
                                                    color: Colors.textPrimary
                                                }
                                            }

                                            MouseArea {
                                                id: sameLevelArea
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onClicked: {
                                                    folderAddMenu.close()
                                                    if (folderController) {
                                                        var parentId = folderAddMenu.parentIdOf(folderAddMenu.baseFolderId)
                                                        folderController.createFolder("새 폴더", String(Colors.primary500), parentId)
                                                    }
                                                }
                                            }
                                        }

                                        // Divider
                                        Rectangle {
                                            width: parent.width - 16
                                            height: 1
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            color: Colors.borderLight
                                        }

                                        // Child folder option
                                        Rectangle {
                                            width: parent.width
                                            height: 28
                                            radius: Metrics.radiusSm
                                            color: childArea.containsMouse ? Colors.primary100 : "#FFFFFF"
                                            opacity: folderAddMenu.canCreateChild() ? 1.0 : 0.5

                                            Row {
                                                anchors.fill: parent
                                                anchors.leftMargin: 8
                                                spacing: 6

                                                // Icon placeholder
                                                Rectangle {
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    width: 16
                                                    height: 16
                                                    color: "transparent"

                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: "📂"
                                                        font.pixelSize: 12
                                                    }
                                                }

                                                Text {
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    text: "하위 폴더로 생성"
                                                    font.family: Typography.fontPrimary
                                                    font.weight: Typography.weightMedium
                                                    font.pixelSize: 12
                                                    color: folderAddMenu.canCreateChild() ? Colors.textPrimary : Colors.textTertiary
                                                }
                                            }

                                            MouseArea {
                                                id: childArea
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                enabled: folderAddMenu.canCreateChild()
                                                onClicked: {
                                                    folderAddMenu.close()
                                                    if (folderController && folderAddMenu.baseFolderId !== "") {
                                                        folderController.createFolder("새 폴더", String(Colors.primary500), folderAddMenu.baseFolderId)
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                                }
                            }
                        }

                        // Folders list from controller
                        ListView {
                            id: foldersListView
                            Layout.fillWidth: true
                            Layout.fillHeight: sidebar.sidebarTabIdx === 0
                            visible: sidebar.sidebarTabIdx === 0 && window.activeContentMode === "notes"
                            z: 0
                            model: folderController ? folderController.folders : []
                            spacing: Metrics.xs
                            clip: true
                            ScrollBar.vertical: ScrollBar {
                                policy: ScrollBar.AlwaysOn
                                implicitWidth: 6
                                contentItem: Rectangle {
                                    radius: 3
                                    color: Colors.borderMedium
                                    opacity: parent.active ? 0.8 : 0.3
                                }
                                background: Item {}
                            }

                            delegate: FolderItem {
                                width: ListView.view.width
                                folderId: modelData ? modelData.id : ""
                                folderName: modelData ? modelData.name : ""
                                folderColor: {
                                    if (modelData && modelData.is_smart) {
                                        return modelData.color || Colors.primary400
                                    }
                                    var d = modelData ? (modelData.depth || 0) : 0
                                    if (d === 0) return Colors.primary500
                                    if (d === 1) return Colors.primary300
                                    if (d >= 2) return Colors.primary200
                                    return Colors.primary500
                                }
                                noteCount: modelData ? modelData.note_count : 0
                                depth: modelData ? (modelData.depth || 0) : 0
                                hasChildren: modelData ? (modelData.has_children || false) : false
                                isSmart: modelData ? (modelData.is_smart || false) : false
                                isLastSmart: {
                                    if (!modelData || !modelData.is_smart) return false
                                    var idx = index
                                    var listModel = foldersListView.model
                                    return (idx === listModel.length - 1) || !(listModel[idx + 1] && listModel[idx + 1].is_smart)
                                }
                                isExpanded: folderController && modelData ? !folderController.isFolderCollapsed(modelData.id) : false
                                isSelected: folderController && modelData && folderController.currentFolderId === modelData.id

                                Component.onCompleted: {
                                    console.log("[QML] FolderItem rendered: " + folderName + " (depth=" + depth + ")")
                                }

                                onClicked: {
                                    if (folderController && modelData) folderController.selectFolder(modelData.id)
                                }

                                onToggleExpanded: {
                                    if (folderController && modelData && !(modelData.is_smart || false)) folderController.toggleFolderExpanded(modelData.id)
                                }

                                onRenameRequested: (newName) => {
                                    if (folderController && modelData && !(modelData.is_smart || false)) folderController.renameFolder(modelData.id, newName)
                                }

                                onDeleteRequested: {
                                    if (folderController && modelData && !(modelData.is_smart || false)) folderController.deleteFolder(modelData.id)
                                }
                            }
                        }

                        // AI Prompt Mode Helper (shown in folder pane when in ai_prompts mode)
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: sidebar.sidebarTabIdx === 0
                            visible: sidebar.sidebarTabIdx === 0 && window.activeContentMode === "ai_prompts"
                            color: "transparent"

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: Metrics.md
                                spacing: Metrics.md

                                Text {
                                    text: "AI 프롬프트 문서"
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightSemibold
                                    font.pixelSize: 14
                                    color: Colors.textPrimary
                                }

                                Text {
                                    text: "AI 프롬프트 문서는 별도 라이브러리에 저장되며,\n폴더 구조와 독립적으로 관리됩니다."
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightRegular
                                    font.pixelSize: 11
                                    color: Colors.textSecondary
                                    lineHeight: 1.4
                                }

                                Item {
                                    Layout.fillHeight: true
                                }
                            }
                        }

                        // ── Tag list (태그 탭) ───────────────────────────────
                        Item {
                            Layout.fillWidth: true
                            Layout.fillHeight: sidebar.sidebarTabIdx === 1
                            visible: sidebar.sidebarTabIdx === 1

                            ColumnLayout {
                                anchors.fill: parent
                                spacing: 2

                                // "전체 해제" chip — only shown when a tag is selected
                                Rectangle {
                                    Layout.fillWidth: true
                                    visible: noteController && noteController.selectedTag !== ""
                                    height: 26
                                    radius: Metrics.radiusMd
                                    color: Colors.primary50
                                    border.color: Colors.primary200
                                    border.width: 1

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: Metrics.sm
                                        anchors.rightMargin: Metrics.sm
                                        spacing: 4
                                        Text {
                                            text: "#" + (noteController ? noteController.selectedTag : "")
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 11
                                            color: Colors.primary600
                                            font.weight: Typography.weightMedium
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }
                                        Text {
                                            text: "✕"
                                            font.pixelSize: 10
                                            color: Colors.primary400
                                        }
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: if (noteController) noteController.clearTagFilter()
                                    }
                                }

                                // Tag list
                                ListView {
                                    id: tagListView
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    spacing: 1
                                    model: noteController ? noteController.allTags : []
                                    ScrollBar.vertical: ScrollBar {
                                        policy: ScrollBar.AlwaysOn
                                        implicitWidth: 6
                                        contentItem: Rectangle {
                                            radius: 3
                                            color: Colors.borderMedium
                                            opacity: parent.active ? 0.8 : 0.3
                                        }
                                        background: Item {}
                                    }

                                    Connections {
                                        target: noteController
                                        function onTagsChanged() { tagListView.model = noteController ? noteController.allTags : [] }
                                    }

                                    delegate: Rectangle {
                                        property var tagData: modelData
                                        property string tagName:    tagData ? (tagData.name        || "") : ""
                                        property string tagDisplay: tagData ? (tagData.display     || tagName) : ""
                                        property int    tagCount:   tagData ? (tagData.count       || 0)  : 0
                                        property int    tagDepth:   tagData ? (tagData.depth       || 0)  : 0
                                        property bool   tagHasChildren: tagData ? (tagData.has_children || false) : false
                                        property bool   isSelected: noteController && noteController.selectedTag === tagName
                                        property bool   tagHovered: false

                                        width: tagListView.width
                                        height: 28
                                        radius: Metrics.radiusMd
                                        color: isSelected
                                            ? Colors.primary500
                                            : (tagHovered ? Colors.primary50 : "transparent")

                                        Behavior on color { ColorAnimation { duration: Metrics.durationFast } }

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.leftMargin: Metrics.sm + tagDepth * 14
                                            anchors.rightMargin: Metrics.sm
                                            spacing: 3

                                            // Tree connector line for children
                                            Text {
                                                visible: tagDepth > 0
                                                text: "└"
                                                font.pixelSize: 10
                                                color: isSelected ? Qt.rgba(1,1,1,0.45) : Colors.borderMedium
                                                Layout.alignment: Qt.AlignVCenter
                                            }

                                            // Expand/collapse indicator for parent nodes
                                            Text {
                                                visible: tagHasChildren
                                                text: "▸"
                                                font.pixelSize: 8
                                                color: isSelected ? Qt.rgba(1,1,1,0.7) : Colors.textTertiary
                                                Layout.alignment: Qt.AlignVCenter
                                            }

                                            // # prefix (only for leaf nodes)
                                            Text {
                                                visible: !tagHasChildren
                                                text: "#"
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: 11
                                                color: isSelected ? Qt.rgba(1,1,1,0.7) : Colors.primary400
                                                font.weight: Typography.weightMedium
                                                Layout.alignment: Qt.AlignVCenter
                                            }

                                            // Display label (leaf segment only)
                                            Text {
                                                text: tagDisplay
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: tagHasChildren ? 11 : 12
                                                color: isSelected ? "white" : Colors.textPrimary
                                                font.weight: (isSelected || tagHasChildren)
                                                    ? Typography.weightSemibold
                                                    : Typography.weightRegular
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                                Layout.alignment: Qt.AlignVCenter
                                            }

                                            // Note count badge
                                            Rectangle {
                                                width: Math.max(18, countText.implicitWidth + 8)
                                                height: 16
                                                radius: Metrics.radiusFull
                                                color: isSelected ? Qt.rgba(1,1,1,0.2) : Colors.bgTertiary
                                                Layout.alignment: Qt.AlignVCenter
                                                Text {
                                                    id: countText
                                                    anchors.centerIn: parent
                                                    text: tagCount
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: 10
                                                    color: isSelected ? "white" : Colors.textTertiary
                                                }
                                            }
                                        }

                                        MouseArea {
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            onEntered: parent.tagHovered = true
                                            onExited: parent.tagHovered = false
                                            onClicked: {
                                                if (noteController) noteController.selectTag(tagName)
                                            }
                                        }
                                    }

                                    // Empty state
                                    Text {
                                        anchors.centerIn: parent
                                        visible: tagListView.count === 0
                                        text: "태그가 없습니다\n노트에 #태그를 추가하세요"
                                        horizontalAlignment: Text.AlignHCenter
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        color: Colors.textTertiary
                                        lineHeight: 1.6
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                id: noteList
                Layout.preferredWidth: Metrics.noteListWidth
                Layout.fillHeight: true
                color: "transparent"
                clip: true

                Behavior on Layout.preferredWidth {
                    NumberAnimation { duration: Metrics.durationNormal; easing.type: Easing.InOutQuart }
                }

                GlassCard {
                    anchors.fill: parent
                    anchors.margins: Metrics.md
                    anchors.leftMargin: 0
                    anchors.rightMargin: 0
                    radius: Metrics.radiusXxl
                    baseOpacity: 0.9

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Metrics.sm
                        spacing: Metrics.sm

                        RowLayout {
                            Layout.fillWidth: true

                            Text {
                                text: {
                                    if (window.activeContentMode === "ai_prompts") return "AI 프롬프트"
                                    if (!noteController) return "노트"
                                    if (noteController.selectedTag !== "") return "#" + noteController.selectedTag
                                    return noteController.currentFolderName || "노트"
                                }
                                font.family: Typography.fontPrimary
                                font.weight: Typography.weightSemibold
                                font.pixelSize: Typography.h5
                                color: Colors.textPrimary
                            }

                            Text {
                                text: "(" + (notesListView.count || 0) + ")"
                                font.family: Typography.fontPrimary
                                font.weight: Typography.weightRegular
                                font.pixelSize: Typography.caption
                                color: Colors.textTertiary
                            }

                            // Include subfolders toggle
                            Rectangle {
                                width: 40
                                height: 22
                                radius: 11
                                color: noteController && noteController.includeSubfolders ? Colors.primary500 : Colors.bgSecondary
                                border.width: 1
                                border.color: noteController && noteController.includeSubfolders ? Colors.primary500 : Colors.borderLight
                                visible: window.activeContentMode === "notes" && noteController && noteController.selectedTag === ""

                                Rectangle {
                                    width: 18
                                    height: 18
                                    radius: 9
                                    color: Colors.white
                                    anchors.left: parent.left
                                    anchors.leftMargin: noteController && noteController.includeSubfolders ? 20 : 2
                                    anchors.verticalCenter: parent.verticalCenter

                                    Behavior on anchors.leftMargin {
                                        NumberAnimation { duration: 150; easing.type: Easing.InOutQuad }
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    ToolTip.text: noteController && noteController.includeSubfolders ? "하위 폴더 노트 포함 (켜짐)" : "하위 폴더 노트 포함 (꺼짐)"
                                    ToolTip.visible: containsMouse
                                    ToolTip.delay: 500
                                    onClicked: {
                                        if (noteController) {
                                            noteController.setIncludeSubfolders(!noteController.includeSubfolders)
                                        }
                                    }
                                }
                            }

                            Item { Layout.fillWidth: true }

                            Rectangle {
                                width: 28
                                height: 28
                                radius: Metrics.radiusFull
                                color: addNoteArea.containsMouse ? Colors.primary100 : Colors.bgSecondary
                                border.width: 1
                                border.color: addNoteArea.containsMouse ? Colors.primary200 : Colors.borderLight
                                visible: (window.activeContentMode === "notes" && noteController && noteController.selectedTag === "") || (window.activeContentMode === "ai_prompts")

                                Behavior on color {
                                    ColorAnimation { duration: Metrics.durationFast }
                                }

                                MouseArea {
                                    id: addNoteArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: {
                                        if (window.activeContentMode === "ai_prompts") {
                                            if (typeof promptDocumentController !== "undefined" && promptDocumentController) {
                                                var newDoc = promptDocumentController.createPromptDocument("새 AI 프롬프트", "", "새로 만든 프롬프트입니다.")
                                                if (newDoc && newDoc.prompt_doc_id) {
                                                    promptDocumentController.selectPromptDocument(newDoc.prompt_doc_id)
                                                    window.selectedAIPromptDocId = newDoc.prompt_doc_id
                                                    window.currentAIPromptDocument = newDoc
                                                }
                                            }
                                        } else {
                                            window.startDraftNote()
                                        }
                                    }
                                }

                                Text {
                                    anchors.centerIn: parent
                                    text: "+"
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightSemibold
                                    font.pixelSize: 18
                                    color: addNoteArea.containsMouse ? Colors.primary600 : Colors.textSecondary
                                }
                            }

                            Rectangle {
                                width: 28
                                height: 28
                                radius: Metrics.radiusMd
                                color: noteSelectionMode ? Colors.primary200 : (selectModeArea.containsMouse ? Colors.primary100 : Colors.bgSecondary)
                                border.width: 1
                                border.color: noteSelectionMode ? Colors.primary300 : Colors.borderLight
                                visible: window.activeContentMode === "notes" && noteController && noteController.selectedTag === ""

                                Image {
                                    anchors.centerIn: parent
                                    source: "assets/icons/note_select.svg"
                                    sourceSize: Qt.size(16, 16)
                                    opacity: noteSelectionMode ? 1.0 : 0.6
                                }

                                MouseArea {
                                    id: selectModeArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: {
                                        if (noteSelectionMode) {
                                            window.exitNoteSelectionMode()
                                        } else {
                                            window.enterNoteSelectionMode()
                                        }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            visible: noteSelectionMode
                            Layout.fillWidth: true
                            height: 40
                            radius: Metrics.radiusMd
                            color: Colors.bgSecondary
                            border.width: 1
                            border.color: Colors.borderLight

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: Metrics.xs
                                spacing: 4

                                Text {
                                    text: selectedNoteCount()
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: 10
                                    font.weight: Typography.weightSemibold
                                    color: Colors.textPrimary
                                }

                                Rectangle {
                                    width: 28
                                    height: 28
                                    radius: Metrics.radiusMd
                                    color: Colors.bgSecondary
                                    border.width: 1
                                    border.color: Colors.borderLight
                                    opacity: (notesListView.count || 0) > 0 ? 1.0 : 0.5

                                    Text {
                                        anchors.centerIn: parent
                                        text: window.isAllVisibleNotesSelected() ? "☑" : "☐"
                                        font.pixelSize: 14
                                        color: Colors.textSecondary
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        enabled: (notesListView.count || 0) > 0
                                        onClicked: window.toggleSelectAllVisibleNotes()
                                    }
                                }

                                Item { Layout.fillWidth: true }

                                Rectangle {
                                    width: 28
                                    height: 28
                                    radius: Metrics.radiusMd
                                    color: selectedNoteCount() > 0 && window.hasBatchFolderTargets() ? Colors.primary200 : Colors.bgTertiary
                                    opacity: selectedNoteCount() > 0 && window.hasBatchFolderTargets() ? 1.0 : 0.85
                                    border.width: selectedNoteCount() > 0 && window.hasBatchFolderTargets() ? 0 : 1
                                    border.color: Colors.borderLight
                                    Image {
                                        anchors.centerIn: parent
                                        source: "assets/icons/note_move.svg"
                                        sourceSize: Qt.size(16, 16)
                                        opacity: selectedNoteCount() > 0 && window.hasBatchFolderTargets() ? 1.0 : 0.6
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        enabled: selectedNoteCount() > 0 && window.hasBatchFolderTargets()
                                        onClicked: window.openBatchFolderPicker("move")
                                    }
                                }

                                Rectangle {
                                    width: 28
                                    height: 28
                                    radius: Metrics.radiusMd
                                    color: selectedNoteCount() > 0 && window.hasBatchFolderTargets() ? Colors.primary200 : Colors.bgTertiary
                                    opacity: selectedNoteCount() > 0 && window.hasBatchFolderTargets() ? 1.0 : 0.85
                                    border.width: selectedNoteCount() > 0 && window.hasBatchFolderTargets() ? 0 : 1
                                    border.color: Colors.borderLight
                                    Image {
                                        anchors.centerIn: parent
                                        source: "assets/icons/note_copy.svg"
                                        sourceSize: Qt.size(16, 16)
                                        opacity: selectedNoteCount() > 0 && window.hasBatchFolderTargets() ? 1.0 : 0.6
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        enabled: selectedNoteCount() > 0 && window.hasBatchFolderTargets()
                                        onClicked: window.openBatchFolderPicker("copy")
                                    }
                                }

                                Rectangle {
                                    width: 28
                                    height: 28
                                    radius: Metrics.radiusMd
                                    color: selectedNoteCount() > 0 ? "#FEE2E2" : Colors.bgTertiary
                                    opacity: selectedNoteCount() > 0 ? 1.0 : 0.85
                                    border.width: selectedNoteCount() > 0 ? 0 : 1
                                    border.color: Colors.borderLight
                                    Image {
                                        anchors.centerIn: parent
                                        source: "assets/icons/note_delete.svg"
                                        sourceSize: Qt.size(16, 16)
                                        opacity: selectedNoteCount() > 0 ? 1.0 : 0.6
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        enabled: selectedNoteCount() > 0
                                        onClicked: window.openBatchDeleteConfirm()
                                    }
                                }

                                Rectangle {
                                    width: 28
                                    height: 28
                                    radius: Metrics.radiusMd
                                    color: Colors.bgSecondary
                                    border.width: 1
                                    border.color: Colors.borderLight
                                    Image {
                                        anchors.centerIn: parent
                                        source: "assets/icons/action_cancel.svg"
                                        sourceSize: Qt.size(16, 16)
                                        opacity: 0.6
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: window.exitNoteSelectionMode()
                                    }
                                }
                            }
                        }

                        // Sort & Filter bar
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.xs

                            // Row 1: Sort controls + filter toggle icon
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.sm

                                // Sort field buttons (disabled when filter active)
                                Rectangle {
                                    Layout.preferredWidth: 200
                                    Layout.preferredHeight: 28
                                    radius: Metrics.radiusMd
                                    color: noteController && noteController.isFilterActive ? Colors.bgTertiary : Colors.bgSecondary
                                    border.color: Colors.borderLight
                                    border.width: 1
                                    opacity: noteController && noteController.isFilterActive ? 0.5 : 1.0

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 2
                                        spacing: 2

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            radius: Metrics.radiusSm
                                            color: noteController && noteController.sortField === "updated_at" && !(noteController && noteController.isFilterActive) ? Colors.primary500 : "transparent"
                                            Text {
                                                anchors.centerIn: parent
                                                text: "수정일"
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: 11
                                                color: noteController && noteController.sortField === "updated_at" && !(noteController && noteController.isFilterActive) ? "white" : Colors.textTertiary
                                            }
                                            MouseArea {
                                                anchors.fill: parent
                                                onClicked: if (noteController && !noteController.isFilterActive) noteController.setSortField("updated_at")
                                            }
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            radius: Metrics.radiusSm
                                            color: noteController && noteController.sortField === "created_at" && !(noteController && noteController.isFilterActive) ? Colors.primary500 : "transparent"
                                            Text {
                                                anchors.centerIn: parent
                                                text: "생성일"
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: 11
                                                color: noteController && noteController.sortField === "created_at" && !(noteController && noteController.isFilterActive) ? "white" : Colors.textTertiary
                                            }
                                            MouseArea {
                                                anchors.fill: parent
                                                onClicked: if (noteController && !noteController.isFilterActive) noteController.setSortField("created_at")
                                            }
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            radius: Metrics.radiusSm
                                            color: noteController && noteController.sortField === "title" && !(noteController && noteController.isFilterActive) ? Colors.primary500 : "transparent"
                                            Text {
                                                anchors.centerIn: parent
                                                text: "제목"
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: 11
                                                color: noteController && noteController.sortField === "title" && !(noteController && noteController.isFilterActive) ? "white" : Colors.textTertiary
                                            }
                                            MouseArea {
                                                anchors.fill: parent
                                                onClicked: if (noteController && !noteController.isFilterActive) noteController.setSortField("title")
                                            }
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            radius: Metrics.radiusSm
                                            color: noteController && noteController.sortField === "content" && !(noteController && noteController.isFilterActive) ? Colors.primary500 : "transparent"
                                            Text {
                                                anchors.centerIn: parent
                                                text: "내용"
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: 11
                                                color: noteController && noteController.sortField === "content" && !(noteController && noteController.isFilterActive) ? "white" : Colors.textTertiary
                                            }
                                            MouseArea {
                                                anchors.fill: parent
                                                onClicked: if (noteController && !noteController.isFilterActive) noteController.setSortField("content")
                                            }
                                        }
                                    }
                                }

                                // Sort order toggle (disabled when filter active)
                                Rectangle {
                                    Layout.preferredWidth: 28
                                    Layout.preferredHeight: 28
                                    radius: Metrics.radiusMd
                                    color: noteController && noteController.isFilterActive ? Colors.bgTertiary : (orderMouseArea.containsMouse ? Colors.primary100 : Colors.bgSecondary)
                                    border.color: Colors.borderLight
                                    border.width: 1
                                    opacity: noteController && noteController.isFilterActive ? 0.5 : 1.0

                                    Text {
                                        anchors.centerIn: parent
                                        text: noteController && noteController.sortOrder === "asc" ? "▲" : "▼"
                                        font.pixelSize: 10
                                        color: noteController && noteController.isFilterActive ? Colors.textTertiary : Colors.textSecondary
                                    }

                                    MouseArea {
                                        id: orderMouseArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        enabled: !(noteController && noteController.isFilterActive)
                                        onClicked: if (noteController) noteController.toggleSortOrder()
                                    }
                                }

                                Item { Layout.fillWidth: true }

                                // Filter toggle button
                                Rectangle {
                                    Layout.preferredWidth: 28
                                    Layout.preferredHeight: 28
                                    radius: Metrics.radiusMd
                                    color: filterPanelVisible
                                        ? (noteController && noteController.searchKeyword !== "" ? Colors.primary500 : Colors.primary100)
                                        : (filterIconArea.containsMouse ? Colors.bgTertiary : "transparent")
                                    border.color: filterPanelVisible ? Colors.primary300 : Colors.borderLight
                                    border.width: 1

                                    property bool filterPanelVisible: false

                                    Text {
                                        anchors.centerIn: parent
                                        text: "⌕"
                                        font.pixelSize: 16
                                        color: parent.filterPanelVisible
                                            ? (noteController && noteController.searchKeyword !== "" ? "white" : Colors.primary600)
                                            : (filterIconArea.containsMouse ? Colors.textSecondary : Colors.textTertiary)
                                    }

                                    MouseArea {
                                        id: filterIconArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: {
                                            parent.filterPanelVisible = !parent.filterPanelVisible
                                            if (!parent.filterPanelVisible && noteController) {
                                                noteController.setSearchKeyword("")
                                                searchField.text = ""
                                            } else if (parent.filterPanelVisible) {
                                                searchField.forceActiveFocus()
                                            }
                                        }
                                    }

                                    id: filterToggleBtn
                                }
                            }

                            // Row 2: Filter panel (collapsible)
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.xs
                                visible: filterToggleBtn.filterPanelVisible

                                // Text search row (always shown in filter panel)
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 28
                                    radius: Metrics.radiusMd
                                    color: Colors.bgSecondary
                                    border.color: searchField.activeFocus ? Colors.primary300 : Colors.borderLight
                                    border.width: 1

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 4
                                        spacing: Metrics.xs

                                        Text {
                                            text: "⌕"
                                            font.pixelSize: 13
                                            color: Colors.textTertiary
                                        }

                                        TextInput {
                                            id: searchField
                                            Layout.fillWidth: true
                                            verticalAlignment: TextInput.AlignVCenter
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: Typography.caption
                                            color: Colors.textPrimary
                                            clip: true
                                            onTextChanged: {
                                                if (noteController) noteController.setSearchKeyword(text)
                                            }

                                            Text {
                                                anchors.fill: parent
                                                verticalAlignment: Text.AlignVCenter
                                                text: "제목 또는 내용 검색..."
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: Typography.caption
                                                color: Colors.textTertiary
                                                visible: parent.text === "" && !parent.activeFocus
                                            }
                                        }

                                        Text {
                                            text: "✕"
                                            font.pixelSize: 11
                                            color: Colors.textTertiary
                                            visible: searchField.text !== ""
                                            MouseArea {
                                                anchors.fill: parent
                                                onClicked: {
                                                    searchField.text = ""
                                                    if (noteController) noteController.setSearchKeyword("")
                                                }
                                            }
                                        }
                                    }
                                }

                                // Date range row (shown only when sort field is created_at or updated_at)
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: Metrics.xs
                                    visible: noteController && (noteController.sortField === "created_at" || noteController.sortField === "updated_at")

                                    Text {
                                        text: noteController && noteController.sortField === "created_at" ? "생성일" : "수정일"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.caption
                                        color: Colors.textTertiary
                                        Layout.preferredWidth: 30
                                    }

                                    // From date input with calendar button
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: Metrics.xs

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 28
                                            radius: Metrics.radiusMd
                                            color: Colors.bgSecondary
                                            border.color: fromDateField.activeFocus ? Colors.primary300 : Colors.borderLight
                                            border.width: 1

                                            TextInput {
                                                id: fromDateField
                                                anchors.fill: parent
                                                anchors.margins: 4
                                                anchors.leftMargin: 8
                                                verticalAlignment: TextInput.AlignVCenter
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: Typography.caption
                                                color: Colors.textPrimary
                                                clip: true
                                                inputMethodHints: Qt.ImhDigitsOnly
                                                maximumLength: 10
                                                onTextChanged: {
                                                    if (noteController && (text.length === 0 || text.length === 10))
                                                        noteController.setFilterFromDate(text)
                                                }

                                                Text {
                                                    anchors.fill: parent
                                                    verticalAlignment: Text.AlignVCenter
                                                    text: "시작일 YYYY-MM-DD"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.caption
                                                    color: Colors.textTertiary
                                                    visible: parent.text === "" && !parent.activeFocus
                                                }
                                            }
                                        }

                                        // Calendar button for from date
                                        Rectangle {
                                            Layout.preferredWidth: 26
                                            Layout.preferredHeight: 28
                                            radius: Metrics.radiusMd
                                            color: fromCalBtnArea.containsMouse ? Colors.primary100 : Colors.bgSecondary
                                            border.color: Colors.borderLight
                                            border.width: 1

                                            Text {
                                                anchors.centerIn: parent
                                                text: "📅"
                                                font.pixelSize: 12
                                            }

                                            MouseArea {
                                                id: fromCalBtnArea
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onClicked: {
                                                    if (noteController) {
                                                        var selected = noteController.showCalendarDialog(fromDateField.text)
                                                        if (selected !== "") {
                                                            fromDateField.text = selected
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }

                                    Text {
                                        text: "~"
                                        font.pixelSize: Typography.caption
                                        color: Colors.textTertiary
                                    }

                                    // To date input with calendar button
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: Metrics.xs

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 28
                                            radius: Metrics.radiusMd
                                            color: Colors.bgSecondary
                                            border.color: toDateField.activeFocus ? Colors.primary300 : Colors.borderLight
                                            border.width: 1

                                            TextInput {
                                                id: toDateField
                                                anchors.fill: parent
                                                anchors.margins: 4
                                                anchors.leftMargin: 8
                                                verticalAlignment: TextInput.AlignVCenter
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: Typography.caption
                                                color: Colors.textPrimary
                                                clip: true
                                                inputMethodHints: Qt.ImhDigitsOnly
                                                maximumLength: 10
                                                onTextChanged: {
                                                    if (noteController && (text.length === 0 || text.length === 10))
                                                        noteController.setFilterToDate(text)
                                                }

                                                Text {
                                                    anchors.fill: parent
                                                    verticalAlignment: Text.AlignVCenter
                                                    text: "종료일 YYYY-MM-DD"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.caption
                                                    color: Colors.textTertiary
                                                    visible: parent.text === "" && !parent.activeFocus
                                                }
                                            }
                                        }

                                        // Calendar button for to date
                                        Rectangle {
                                            Layout.preferredWidth: 26
                                            Layout.preferredHeight: 28
                                            radius: Metrics.radiusMd
                                            color: toCalBtnArea.containsMouse ? Colors.primary100 : Colors.bgSecondary
                                            border.color: Colors.borderLight
                                            border.width: 1

                                            Text {
                                                anchors.centerIn: parent
                                                text: "📅"
                                                font.pixelSize: 12
                                            }

                                            MouseArea {
                                                id: toCalBtnArea
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onClicked: {
                                                    if (noteController) {
                                                        var selected = noteController.showCalendarDialog(toDateField.text)
                                                        if (selected !== "") {
                                                            toDateField.text = selected
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }

                                    // Clear date range
                                    Text {
                                        text: "✕"
                                        font.pixelSize: 11
                                        color: Colors.textTertiary
                                        visible: fromDateField.text !== "" || toDateField.text !== ""
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                fromDateField.text = ""
                                                toDateField.text = ""
                                                if (noteController) {
                                                    noteController.setFilterFromDate("")
                                                    noteController.setFilterToDate("")
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        // Notes list from controller - filtered by current folder
                        ListView {
                            id: notesListView
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: Metrics.xs
                            clip: true
                            reuseItems: true  // Enable delegate recycling for performance with large datasets
                            cacheBuffer: 500  // Pre-render 500px of content for smoother scrolling

                            // Load more notes when scrolling to bottom (infinite scroll)
                            onAtYEndChanged: {
                                if (atYEnd && noteController && notesListView.count > 0) {
                                    // Save current scroll position before loading more
                                    var scrollY = contentY
                                    noteController.loadMoreNotes()
                                    // Restore scroll position after model update
                                    Qt.callLater(function() {
                                        contentY = scrollY
                                    })
                                }
                            }
                            ScrollBar.vertical: ScrollBar {
                                policy: ScrollBar.AlwaysOn
                                implicitWidth: 6
                                contentItem: Rectangle {
                                    radius: 3
                                    color: Colors.borderMedium
                                    opacity: parent.active ? 0.8 : 0.3
                                }
                                background: Item {}
                            }

                            // Branch model based on activeContentMode - use refreshCounter to force re-evaluation
                            model: {
                                if (window.activeContentMode === "notes") {
                                    return noteController ? noteController.filteredNotes : []
                                } else {
                                    // Access refreshCounter to create dependency
                                    var _ = window.promptListRefreshCounter
                                    return promptDocumentController ? promptDocumentController.promptDocumentList : []
                                }
                            }

                            // Transition animations for list changes (disabled for performance with large datasets)
                            /*
                            add: Transition {
                                NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Metrics.durationNormal }
                                NumberAnimation { property: "y"; from: 20; to: 0; duration: Metrics.durationNormal }
                            }
                            remove: Transition {
                                NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Metrics.durationFast }
                                NumberAnimation { property: "scale"; from: 1; to: 0.95; duration: Metrics.durationFast }
                            }
                            displaced: Transition {
                                NumberAnimation { property: "y"; duration: Metrics.durationNormal }
                            }
                            */

                            delegate: window.activeContentMode === "notes" ? noteListDelegate : aiPromptListDelegate

                            Component {
                                id: noteListDelegate
                                NoteListItem {
                                id: noteItem
                                width: ListView.view.width

                                // Strong binding for noteId
                                property var modelRef: modelData
                                property string noteId: modelRef && modelRef.id ? modelRef.id : ""

                                title: modelRef ? modelRef.title || "" : ""
                                preview: modelRef && modelRef.content ? (modelRef.content.substring(0, 80) + (modelRef.content.length > 80 ? "..." : "")) : ""
                                createdDate: modelRef && modelRef.created_at ? noteController.formatDate(modelRef.created_at) : ""
                                updatedDate: modelRef && modelRef.updated_at ? noteController.formatDate(modelRef.updated_at) : ""
                                tags: modelRef && modelRef.tags ? modelRef.tags : []
                                isPinned: noteItem.pinState
                                folderPath: noteController && noteItem.noteId ? noteController.getFolderPathForNote(noteItem.noteId) : ""
                                selectionMode: window.noteSelectionMode
                                isBatchHighlighted: window.noteSelectionMode && window.isNoteSelected(noteItem.noteId)
                                isSelected: {
                                    var selected = noteController && noteController.currentNoteId === noteItem.noteId
                                    return selected
                                }

                                // Internal pin state source for NoteListItem.isPinned
                                property bool pinState: false

                                function updateIsPinned() {
                                    if (noteItem.noteId && noteController) {
                                        pinState = noteController.isNotePinned(noteItem.noteId)
                                    } else {
                                        pinState = false
                                    }
                                }

                                Component.onCompleted: updateIsPinned()
                                onNoteIdChanged: updateIsPinned()

                                // Refresh when notes change
                                Connections {
                                    target: noteController
                                    function onNotesChanged() {
                                        noteItem.updateIsPinned()
                                    }
                                }

                                onSelectionClicked: {
                                    if (noteItem.noteId) {
                                        window.toggleNoteSelection(noteItem.noteId)
                                    }
                                }

                                onClicked: {
                                    if (noteItem.noteId) {
                                        if (window.noteSelectionMode) {
                                            window.toggleNoteSelection(noteItem.noteId)
                                        } else {
                                            console.log("[QML] Note clicked:", noteItem.noteId)
                                            if (noteController) {
                                                noteController.selectNote(noteItem.noteId)
                                            }
                                        }
                                    }
                                }

                                onPinClicked: {
                                    console.log("[QML] Pin clicked for note:", noteItem.noteId, "model id:", modelRef ? modelRef.id : "null")
                                    if (noteItem.noteId) {
                                        if (noteController) {
                                            noteController.selectNote(noteItem.noteId)
                                            noteController.togglePinned(noteItem.noteId)
                                        }
                                    }
                                }

                                onDeleteClicked: {
                                    if (noteItem.noteId) {
                                        deleteConfirmDialog.targetNoteId = noteItem.noteId
                                        deleteConfirmDialog.targetNoteTitle = noteItem.title || "제목 없음"
                                        deleteConfirmDialog.visible = true
                                    }
                                }
                                }
                            }

                            Component {
                                id: aiPromptListDelegate
                                Rectangle {
                                    id: aiPromptItem
                                    width: ListView.view.width
                                    height: 60
                                    property bool isSample: modelData && window.isPromptSample(modelData)
                                    property bool isSelected: modelData && window.selectedAIPromptDocId === (modelData.prompt_doc_id || "")
                                    color: {
                                        if (aiPromptItem.isSelected) return Colors.surfaceHigh
                                        if (aiPromptMouse.containsMouse) return Colors.bgTertiary
                                        if (aiPromptItem.isSample) return Qt.rgba(249/255, 115/255, 22/255, 0.08)
                                        return "transparent"
                                    }
                                    border.width: aiPromptItem.isSelected ? 2 : (aiPromptItem.isSample ? 1 : 0)
                                    border.color: aiPromptItem.isSelected ? Colors.primary400 : (aiPromptItem.isSample ? Colors.accentOrangeLight : "transparent")
                                    radius: Metrics.radiusMd

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: Metrics.md
                                        anchors.rightMargin: Metrics.md
                                        spacing: Metrics.md

                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 2

                                            Text {
                                                Layout.fillWidth: true
                                                text: modelData.title || ""
                                                font.family: Typography.fontPrimary
                                                font.weight: Typography.weightMedium
                                                font.pixelSize: 14
                                                color: Colors.textPrimary
                                                elide: Text.ElideRight
                                            }

                                            Text {
                                                Layout.fillWidth: true
                                                text: modelData.description || ""
                                                font.family: Typography.fontPrimary
                                                font.weight: Typography.weightRegular
                                                font.pixelSize: 11
                                                color: Colors.textSecondary
                                                elide: Text.ElideRight
                                            }

                                            Row {
                                                spacing: Metrics.xs

                                                Rectangle {
                                                    height: 16
                                                    radius: Metrics.radiusSm
                                                    color: aiPromptItem.isSample ? Qt.rgba(249/255, 115/255, 22/255, 0.15) : Colors.primary50
                                                    border.color: aiPromptItem.isSample ? Colors.accentOrangeLight : "transparent"
                                                    visible: true

                                                    Text {
                                                        anchors.centerIn: parent
                                                        anchors.leftMargin: 4
                                                        anchors.rightMargin: 4
                                                        text: aiPromptItem.isSample ? "샘플" : "사용자"
                                                        font.family: Typography.fontPrimary
                                                        font.pixelSize: 9
                                                        color: aiPromptItem.isSample ? Colors.accentOrange : Colors.primary700
                                                    }
                                                }

                                                Rectangle {
                                                    height: 16
                                                    radius: Metrics.radiusSm
                                                    color: aiPromptItem.isSample ? Qt.rgba(249/255, 115/255, 22/255, 0.15) : Colors.bgSecondary
                                                    border.color: aiPromptItem.isSample ? Colors.accentOrangeLight : "transparent"
                                                    visible: !!(modelData && modelData.readonly)

                                                    Text {
                                                        anchors.centerIn: parent
                                                        anchors.leftMargin: 4
                                                        anchors.rightMargin: 4
                                                        text: "읽기 전용"
                                                        font.family: Typography.fontPrimary
                                                        font.pixelSize: 9
                                                        color: aiPromptItem.isSample ? Colors.accentOrange : Colors.textSecondary
                                                    }
                                                }
                                            }
                                        }

                                        ColumnLayout {
                                            spacing: 2

                                            Text {
                                                text: {
                                                    if (!modelData || !modelData.updated_at) return ""
                                                    try {
                                                        var dt = new Date(modelData.updated_at)
                                                        var year = dt.getFullYear()
                                                        var month = String(dt.getMonth() + 1).padStart(2, '0')
                                                        var day = String(dt.getDate()).padStart(2, '0')
                                                        var hours = String(dt.getHours()).padStart(2, '0')
                                                        var minutes = String(dt.getMinutes()).padStart(2, '0')
                                                        return year + "." + month + "." + day + " " + hours + ":" + minutes
                                                    } catch (e) {
                                                        return modelData.updated_at
                                                    }
                                                }
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: 10
                                                color: Colors.textTertiary
                                            }
                                        }
                                    }

                                    MouseArea {
                                        id: aiPromptMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: {
                                            if (modelData.prompt_doc_id && promptDocumentController) {
                                                promptDocumentController.selectPromptDocument(modelData.prompt_doc_id)
                                                window.selectedAIPromptDocId = modelData.prompt_doc_id
                                                window.currentAIPromptDocument = modelData
                                            }
                                        }
                                    }
                                }
                            }

                            // Helper function to format AI prompt date
                            function formatAIPromptDate(isoDate) {
                                if (!isoDate) return ""
                                try {
                                    var dt = new Date(isoDate)
                                    var year = dt.getFullYear()
                                    var month = String(dt.getMonth() + 1).padStart(2, '0')
                                    var day = String(dt.getDate()).padStart(2, '0')
                                    var hours = String(dt.getHours()).padStart(2, '0')
                                    var minutes = String(dt.getMinutes()).padStart(2, '0')
                                    return year + "." + month + "." + day + " " + hours + ":" + minutes
                                } catch (e) {
                                    return isoDate
                                }
                            }

                            // Show empty state when no notes
                            Rectangle {
                                visible: notesListView.count === 0
                                anchors.fill: parent
                                color: "transparent"

                                Text {
                                    anchors.centerIn: parent
                                    text: "이 폴더에 노트가 없습니다"
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightRegular
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textTertiary
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                id: editorArea
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                GlassCard {
                    anchors.fill: parent
                    anchors.margins: Metrics.md
                    anchors.leftMargin: 0
                    radius: Metrics.radiusXxl
                    baseOpacity: 0.95

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Metrics.sm
                        spacing: 0

                        // Tab bar - visible when any tab is open
                        Rectangle {
                            id: tabBar
                            Layout.fillWidth: true
                            visible: window.openTabs.length > 0
                            color: "transparent"

                            // ── Layout metrics ───────────────────────────────────────────
                            readonly property int tabH:    30
                            readonly property int minTW:   72
                            readonly property int maxTW:   180
                            readonly property int cnt:     window.openTabs.length
                            readonly property int fitIn1:  Math.max(1, Math.floor(width / (minTW + 2)))
                            readonly property int rows:    (cnt === 0 || cnt <= fitIn1) ? 1 : 2
                            readonly property int perRow:  rows === 1 ? cnt : Math.ceil(cnt / 2)
                            readonly property int tabW:    perRow === 0 ? maxTW
                                                               : Math.max(minTW, Math.min(maxTW, Math.floor(width / perRow) - 2))
                            readonly property int rowW:    perRow * (tabW + 2)

                            Layout.preferredHeight: rows * tabH + (rows > 1 ? 2 : 0)

                            // ── Shared tab delegate ──────────────────────────────────────
                            Component {
                                id: tabDelegate
                                Rectangle {
                                    property bool isActive: modelData.id === window.selectedNoteId
                                    width:  tabBar.tabW
                                    height: tabBar.tabH
                                    radius: Metrics.radiusSm
                                    color: isActive
                                        ? Colors.primary500
                                        : (tabMouse.containsMouse ? Colors.primary50 : "transparent")
                                    border.color: isActive ? Colors.primary600
                                        : (tabMouse.containsMouse ? Colors.primary200 : Colors.borderLight)
                                    border.width: 1

                                    // tab click area (declared first → lower z)
                                    MouseArea {
                                        id: tabMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: {
                                            if (noteController) noteController.selectNote(modelData.id)
                                            window.selectedNoteId = modelData.id
                                        }
                                    }

                                    // content row (on top of tabMouse)
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 6
                                        anchors.rightMargin: 4
                                        spacing: 3

                                        Text {
                                            Layout.fillWidth: true
                                            text: modelData.title || "제목 없음"
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 11
                                            font.weight: isActive ? Typography.weightSemibold : Typography.weightRegular
                                            color: isActive ? "white" : Colors.textSecondary
                                            elide: Text.ElideRight
                                        }

                                        // Close button
                                        Rectangle {
                                            width: 14
                                            height: 14
                                            radius: Metrics.radiusFull
                                            visible: tabMouse.containsMouse || isActive
                                            color: closeMA.containsMouse
                                                ? (isActive ? Qt.rgba(1,1,1,0.25) : Colors.bgTertiary)
                                                : "transparent"

                                            Text {
                                                anchors.centerIn: parent
                                                text: "×"
                                                font.pixelSize: 12
                                                color: isActive ? "white" : Colors.textSecondary
                                            }

                                            MouseArea {
                                                id: closeMA
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onClicked: window.closeTab(modelData.id)
                                            }
                                        }
                                    }
                                }
                            }

                            // ── RowLayout: [left btn] [Flickable] [right btn] ─────────────
                            RowLayout {
                                anchors.fill: parent
                                spacing: 0

                                // Left scroll button
                                Rectangle {
                                    id: tabScrollLeft
                                    Layout.preferredWidth: (tabBar.rowW > tabBar.width && tabFlickable.contentX > 1) ? 22 : 0
                                    Layout.fillHeight: true
                                    clip: true
                                    color: leftBtnMA.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                                    border.color: Colors.borderLight
                                    border.width: Layout.preferredWidth > 0 ? 1 : 0
                                    radius: Metrics.radiusSm

                                    Behavior on Layout.preferredWidth {
                                        NumberAnimation { duration: Metrics.durationFast }
                                    }

                                    Text {
                                        anchors.centerIn: parent
                                        text: "‹"
                                        font.pixelSize: 16
                                        color: Colors.textSecondary
                                        visible: tabScrollLeft.Layout.preferredWidth > 10
                                    }
                                    MouseArea {
                                        id: leftBtnMA
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        enabled: tabScrollLeft.Layout.preferredWidth > 0
                                        onClicked: tabFlickable.contentX = Math.max(0, tabFlickable.contentX - 120)
                                    }
                                }

                                // Flickable
                                Flickable {
                                    id: tabFlickable
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    contentWidth: Math.max(tabBar.rowW, width)
                                    flickableDirection: Flickable.HorizontalFlick
                                    interactive: tabBar.rowW > width
                                    clip: true

                                    Behavior on contentX {
                                        NumberAnimation { duration: Metrics.durationNormal; easing.type: Easing.OutCubic }
                                    }

                                    Column {
                                        spacing: 2

                                        // Row 1
                                        Row {
                                            spacing: 2
                                            Repeater {
                                                model: window.openTabs.slice(0, tabBar.perRow)
                                                delegate: tabDelegate
                                            }
                                        }

                                        // Row 2 (only when rows === 2)
                                        Row {
                                            spacing: 2
                                            visible: tabBar.rows === 2
                                            Repeater {
                                                model: window.openTabs.slice(tabBar.perRow)
                                                delegate: tabDelegate
                                            }
                                        }
                                    }
                                }

                                // Right scroll button
                                Rectangle {
                                    id: tabScrollRight
                                    Layout.preferredWidth: (tabBar.rowW > tabBar.width &&
                                        tabFlickable.contentX < tabFlickable.contentWidth - tabFlickable.width - 1) ? 22 : 0
                                    Layout.fillHeight: true
                                    clip: true
                                    color: rightBtnMA.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                                    border.color: Colors.borderLight
                                    border.width: Layout.preferredWidth > 0 ? 1 : 0
                                    radius: Metrics.radiusSm

                                    Behavior on Layout.preferredWidth {
                                        NumberAnimation { duration: Metrics.durationFast }
                                    }

                                    Text {
                                        anchors.centerIn: parent
                                        text: "›"
                                        font.pixelSize: 16
                                        color: Colors.textSecondary
                                        visible: tabScrollRight.Layout.preferredWidth > 10
                                    }
                                    MouseArea {
                                        id: rightBtnMA
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        enabled: tabScrollRight.Layout.preferredWidth > 0
                                        onClicked: tabFlickable.contentX = Math.min(
                                            tabFlickable.contentWidth - tabFlickable.width,
                                            tabFlickable.contentX + 120)
                                    }
                                }
                            }
                        }

                        // Thin separator below tab bar
                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Colors.borderLight
                            visible: window.openTabs.length > 0
                        }

                        // Empty state - only visible when no note selected
                        Rectangle {
                            visible: window.activeContentMode === "notes" ? (!window.selectedNoteId && !window.isDraftNewNote) : (!window.selectedAIPromptDocId)
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "transparent"

                            ColumnLayout {
                                anchors.centerIn: parent
                                spacing: Metrics.md

                                Text {
                                    Layout.alignment: Qt.AlignHCenter
                                    text: window.activeContentMode === "ai_prompts" ? "📋" : "📝"
                                    font.pixelSize: 48
                                }

                                Text {
                                    Layout.alignment: Qt.AlignHCenter
                                    text: window.activeContentMode === "ai_prompts" ? "프롬프트를 선택하거나 새로 만들어보세요" : "노트를 선택하거나 새로 만들어보세요"
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightMedium
                                    font.pixelSize: 14
                                    color: Colors.textSecondary
                                }

                                // Notes mode: 새 노트 만들기
                                Rectangle {
                                    Layout.alignment: Qt.AlignHCenter
                                    width: 140
                                    height: 36
                                    radius: Metrics.radiusLg
                                    color: createNoteBtnArea.containsMouse ? Colors.primary500 : Colors.primary400
                                    visible: window.activeContentMode === "notes"

                                    MouseArea {
                                        id: createNoteBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: {
                                            window.startDraftNote()
                                        }
                                    }

                                    Text {
                                        anchors.centerIn: parent
                                        text: "새 노트 만들기"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightSemibold
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textInverse
                                    }
                                }

                                // AI Prompts mode: 새 프롬프트 만들기
                                Rectangle {
                                    Layout.alignment: Qt.AlignHCenter
                                    width: 160
                                    height: 36
                                    radius: Metrics.radiusLg
                                    color: createPromptBtnArea.containsMouse ? Colors.primary500 : Colors.primary400
                                    visible: window.activeContentMode === "ai_prompts"

                                    MouseArea {
                                        id: createPromptBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: {
                                            if (typeof promptDocumentController !== "undefined" && promptDocumentController) {
                                                var newDoc = promptDocumentController.createPromptDocument("새 AI 프롬프트", "", "새로 만든 프롬프트입니다.")
                                                if (newDoc && newDoc.prompt_doc_id) {
                                                    promptDocumentController.selectPromptDocument(newDoc.prompt_doc_id)
                                                    window.selectedAIPromptDocId = newDoc.prompt_doc_id
                                                    window.currentAIPromptDocument = newDoc
                                                }
                                            }
                                        }
                                    }

                                    Text {
                                        anchors.centerIn: parent
                                        text: "새 프롬프트 만들기"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightSemibold
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textInverse
                                    }
                                }

                                // AI Prompts mode: 샘플에서 새 프롬프트 만들기
                                Rectangle {
                                    Layout.alignment: Qt.AlignHCenter
                                    width: 220
                                    height: 32
                                    radius: Metrics.radiusLg
                                    visible: window.activeContentMode === "ai_prompts"
                                    color: Colors.bgSecondary
                                    border.color: Colors.primary200
                                    border.width: 1

                                    MouseArea {
                                        id: samplePromptBtnArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            if (typeof promptDocumentController !== "undefined" && promptDocumentController && window.promptSampleDocId) {
                                                promptDocumentController.duplicatePromptDocument(window.promptSampleDocId)
                                            }
                                        }
                                    }

                                    Text {
                                        anchors.centerIn: parent
                                        text: "샘플에서 새 프롬프트 만들기"
                                        font.family: Typography.fontPrimary
                                        font.weight: Typography.weightMedium
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textSecondary
                                    }
                                }
                            }
                        }

                        // AI Prompt Mode Status Bar (shown above editor in ai_prompts mode)
                        Rectangle {
                            Layout.fillWidth: true
                            visible: typeof appVariant !== "undefined" && appVariant === "work_ai_editor" && window.activeContentMode === "ai_prompts" && window.selectedAIPromptDocId !== ""
                            implicitHeight: promptEditorToolsLayout.implicitHeight + Metrics.md * 2
                            color: Colors.bgSecondary
                            border.color: Colors.borderLight
                            border.width: 1

                            ColumnLayout {
                                id: promptEditorToolsLayout
                                anchors.fill: parent
                                anchors.margins: Metrics.md
                                spacing: Metrics.sm

                                TextField {
                                    id: aiPromptTitleField
                                    Layout.fillWidth: true
                                    height: 36
                                    text: window.aiPromptTitleDraft
                                    readOnly: window.currentPromptReadonly()
                                    selectByMouse: true
                                    placeholderText: "프롬프트 제목"
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textPrimary
                                    background: Rectangle {
                                        color: window.currentPromptReadonly() ? Colors.bgSecondary : Colors.bgPrimary
                                        radius: Metrics.radiusMd
                                        border.color: Colors.borderLight
                                        border.width: 1
                                    }
                                    onTextEdited: {
                                        window.aiPromptTitleDraft = text
                                        if (!window.currentAIPromptDocument) {
                                            window.currentAIPromptDocument = {}
                                        }
                                        window.currentAIPromptDocument.title = text
                                        aiPromptTitleSaveTimer.restart()
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: Metrics.md

                                    // Status badge
                                    Rectangle {
                                        height: 24
                                        radius: Metrics.radiusSm
                                        color: {
                                            if (!window.currentAIPromptDocument) return Colors.borderLight
                                            if (window.isPromptSample(window.currentAIPromptDocument)) return Colors.accentOrangeLight
                                            return Colors.success
                                        }
                                        visible: window.currentAIPromptDocument !== null && !window.isPromptSample(window.currentAIPromptDocument)

                                        Text {
                                            anchors.centerIn: parent
                                            anchors.leftMargin: 8
                                            anchors.rightMargin: 8
                                            text: !window.currentAIPromptDocument ? "프롬프트를 선택하세요" : "사용자 프롬프트 · 편집 가능"
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 11
                                            color: {
                                                if (!window.currentAIPromptDocument) return Colors.textSecondary
                                                return Colors.white
                                            }
                                        }
                                    }

                                    // Spacer
                                    Item {
                                        Layout.fillWidth: true
                                    }

                                    // Duplicate button (only for sample prompt)
                                    Rectangle {
                                        width: 200
                                        height: 28
                                        radius: Metrics.radiusMd
                                        color: duplicateBtnArea.containsMouse ? Colors.primary500 : Colors.primary400
                                        visible: window.isPromptSample(window.currentAIPromptDocument)

                                        Text {
                                            anchors.centerIn: parent
                                            text: "샘플에서 새 프롬프트 만들기"
                                            font.family: Typography.fontPrimary
                                            font.weight: Typography.weightMedium
                                            font.pixelSize: 11
                                            color: Colors.textInverse
                                        }

                                        MouseArea {
                                            id: duplicateBtnArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            onClicked: {
                                                if (typeof promptDocumentController !== "undefined" && promptDocumentController && window.promptSampleDocId) {
                                                    promptDocumentController.duplicatePromptDocument(window.promptSampleDocId)
                                                }
                                            }
                                        }
                                    }

                                    // Delete button (only for user prompts)
                                    Rectangle {
                                        width: 80
                                        height: 28
                                        radius: Metrics.radiusMd
                                        color: deletePromptBtnArea.containsMouse ? Colors.error500 : Colors.error400
                                        visible: window.currentAIPromptDocument && !window.currentPromptReadonly() && window.currentAIPromptDocument.source_type !== "default"

                                        Text {
                                            anchors.centerIn: parent
                                            text: "삭제"
                                            font.family: Typography.fontPrimary
                                            font.weight: Typography.weightMedium
                                            font.pixelSize: 11
                                            color: Colors.textInverse
                                        }

                                        MouseArea {
                                            id: deletePromptBtnArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            onClicked: {
                                                console.log("[Main] Delete button clicked, selectedAIPromptDocId:", window.selectedAIPromptDocId)
                                                if (typeof promptDocumentController !== "undefined" && promptDocumentController && window.selectedAIPromptDocId) {
                                                    var bindingCount = promptDocumentController.countBindingsForPrompt(window.selectedAIPromptDocId)
                                                    console.log("[Main] Binding count:", bindingCount)
                                                    if (bindingCount > 0) {
                                                        var boundActions = promptDocumentController.listActionsBoundToPrompt(window.selectedAIPromptDocId)
                                                        var actionNames = boundActions.map(function(a) { return a.name || a.action_id }).join(", ")
                                                        promptDeleteDialog.text = "이 프롬프트는 다음 AI 기능에 연결되어 있습니다: " + actionNames + ". 완전히 삭제하시겠습니까?"
                                                        promptDeleteDialog.pendingPromptDocId = window.selectedAIPromptDocId
                                                        promptDeleteDialog.open()
                                                    } else {
                                                        promptDeleteDialog.text = "이 AI 프롬프트를 완전히 삭제하시겠습니까?"
                                                        promptDeleteDialog.pendingPromptDocId = window.selectedAIPromptDocId
                                                        promptDeleteDialog.open()
                                                    }
                                                } else {
                                                    console.log("[Main] promptDocumentController not available or no prompt selected")
                                                }
                                            }
                                        }
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: Metrics.xs
                                    visible: window.promptWarningMessages.length > 0

                                    Repeater {
                                        model: window.promptWarningMessages

                                        Rectangle {
                                            Layout.fillWidth: true
                                            implicitHeight: warningText.implicitHeight + Metrics.xs * 2
                                            radius: Metrics.radiusSm
                                            color: Qt.rgba(245/255, 158/255, 11/255, 0.12)
                                            border.color: Colors.warning
                                            border.width: 1

                                            Text {
                                                id: warningText
                                                anchors.fill: parent
                                                anchors.margins: Metrics.xs
                                                text: modelData
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: Typography.caption
                                                color: Colors.warning
                                                wrapMode: Text.Wrap
                                            }
                                        }
                                    }
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: "작성 샘플은 편집할 수 없습니다. 샘플을 복사해 새 프롬프트를 만들어주세요."
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.textSecondary
                                    wrapMode: Text.Wrap
                                    visible: window.isPromptSample(window.currentAIPromptDocument)
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: promptToolCardLayout.implicitHeight + Metrics.md * 2
                                    radius: Metrics.radiusMd
                                    color: Colors.bgPrimary
                                    border.color: Colors.borderLight
                                    border.width: 1

                                    ColumnLayout {
                                        id: promptToolCardLayout
                                        anchors.fill: parent
                                        anchors.margins: Metrics.md
                                        spacing: Metrics.xs

                                        // --- 구조 블록 접이식 헤더 ---
                                        Rectangle {
                                            Layout.fillWidth: true
                                            implicitHeight: 28
                                            radius: Metrics.radiusSm
                                            color: ruleHeaderMA.containsMouse ? Colors.bgSecondary : "transparent"

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.leftMargin: Metrics.xs
                                                anchors.rightMargin: Metrics.xs
                                                spacing: Metrics.xs

                                                Text {
                                                    text: window.promptRulesExpanded ? "▼" : "▶"
                                                    font.pixelSize: 9
                                                    color: Colors.textTertiary
                                                }
                                                Text {
                                                    text: "구조 블록"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.bodySmall
                                                    font.weight: Typography.weightMedium
                                                    color: Colors.textPrimary
                                                }
                                                Text {
                                                    text: "클릭하면 커서 위치에 삽입"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: 10
                                                    color: Colors.textTertiary
                                                }
                                                Item { Layout.fillWidth: true }
                                            }

                                            MouseArea {
                                                id: ruleHeaderMA
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: window.promptRulesExpanded = !window.promptRulesExpanded
                                            }
                                        }

                                        // --- 구조 블록 칩 목록 (접이식) ---
                                        Item {
                                            Layout.fillWidth: true
                                            visible: window.promptRulesExpanded
                                            implicitHeight: ruleChipFlow.implicitHeight

                                            Flow {
                                                id: ruleChipFlow
                                                width: parent.width
                                                spacing: Metrics.xs

                                                Repeater {
                                                    model: window.promptRuleInsertItems

                                                    Rectangle {
                                                        implicitWidth: ruleChipRow.implicitWidth + Metrics.sm * 2
                                                        implicitHeight: 26
                                                        radius: Metrics.radiusFull
                                                        color: ruleChipMA.containsMouse ? Colors.primary50 : Colors.bgSecondary
                                                        border.color: ruleChipMA.containsMouse ? Colors.primary200 : Colors.borderLight
                                                        border.width: 1
                                                        opacity: window.currentPromptReadonly() ? 0.5 : 1.0

                                                        Row {
                                                            id: ruleChipRow
                                                            anchors.centerIn: parent
                                                            spacing: Metrics.xs

                                                            Text {
                                                                text: modelData.icon
                                                                font.pixelSize: 12
                                                                anchors.verticalCenter: parent.verticalCenter
                                                            }
                                                            Text {
                                                                text: modelData.label
                                                                font.family: Typography.fontPrimary
                                                                font.pixelSize: 11
                                                                font.weight: Typography.weightMedium
                                                                color: Colors.textPrimary
                                                                anchors.verticalCenter: parent.verticalCenter
                                                            }
                                                        }

                                                        MouseArea {
                                                            id: ruleChipMA
                                                            anchors.fill: parent
                                                            hoverEnabled: true
                                                            cursorShape: window.currentPromptReadonly() ? Qt.ArrowCursor : Qt.PointingHandCursor
                                                            ToolTip.visible: containsMouse
                                                            ToolTip.delay: 300
                                                            ToolTip.text: modelData.description
                                                            onClicked: {
                                                                if (!window.currentPromptReadonly()) {
                                                                    window.insertPromptSnippet(modelData.value)
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }

                                        // --- 변수 접이식 헤더 ---
                                        Rectangle {
                                            Layout.fillWidth: true
                                            implicitHeight: 28
                                            radius: Metrics.radiusSm
                                            color: varHeaderMA.containsMouse ? Colors.bgSecondary : "transparent"

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.leftMargin: Metrics.xs
                                                anchors.rightMargin: Metrics.xs
                                                spacing: Metrics.xs

                                                Text {
                                                    text: window.promptVarsExpanded ? "▼" : "▶"
                                                    font.pixelSize: 9
                                                    color: Colors.textTertiary
                                                }
                                                Text {
                                                    text: "변수"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: Typography.bodySmall
                                                    font.weight: Typography.weightMedium
                                                    color: Colors.textPrimary
                                                }
                                                Text {
                                                    text: "동적 데이터를 삽입"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: 10
                                                    color: Colors.textTertiary
                                                }
                                                Item { Layout.fillWidth: true }
                                            }

                                            MouseArea {
                                                id: varHeaderMA
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: window.promptVarsExpanded = !window.promptVarsExpanded
                                            }
                                        }

                                        // --- 변수 칩 목록 (접이식) ---
                                        Item {
                                            Layout.fillWidth: true
                                            visible: window.promptVarsExpanded
                                            implicitHeight: varChipFlow.implicitHeight

                                            Flow {
                                                id: varChipFlow
                                                width: parent.width
                                                spacing: Metrics.xs

                                                Repeater {
                                                    model: window.promptVariableInsertItems

                                                    Rectangle {
                                                        implicitWidth: varChipRow.implicitWidth + Metrics.sm * 2
                                                        implicitHeight: 26
                                                        radius: Metrics.radiusFull
                                                        color: varChipMA.containsMouse ? Colors.primary50 : Colors.bgSecondary
                                                        border.color: varChipMA.containsMouse ? Colors.primary200 : Colors.borderLight
                                                        border.width: 1
                                                        opacity: window.currentPromptReadonly() ? 0.5 : 1.0

                                                        Row {
                                                            id: varChipRow
                                                            anchors.centerIn: parent
                                                            spacing: Metrics.xs

                                                            Text {
                                                                text: modelData.icon
                                                                font.pixelSize: 12
                                                                anchors.verticalCenter: parent.verticalCenter
                                                            }
                                                            Text {
                                                                text: modelData.label
                                                                font.family: Typography.fontPrimary
                                                                font.pixelSize: 11
                                                                font.weight: Typography.weightMedium
                                                                color: Colors.textPrimary
                                                                anchors.verticalCenter: parent.verticalCenter
                                                            }
                                                            Rectangle {
                                                                implicitWidth: varChipCodeText.implicitWidth + 6
                                                                implicitHeight: varChipCodeText.implicitHeight + 2
                                                                radius: 3
                                                                color: Colors.bgTertiary
                                                                anchors.verticalCenter: parent.verticalCenter

                                                                Text {
                                                                    id: varChipCodeText
                                                                    anchors.centerIn: parent
                                                                    text: modelData.code
                                                                    font.family: Typography.fontMono
                                                                    font.pixelSize: 9
                                                                    color: Colors.textSecondary
                                                                }
                                                            }
                                                        }

                                                        MouseArea {
                                                            id: varChipMA
                                                            anchors.fill: parent
                                                            hoverEnabled: true
                                                            cursorShape: window.currentPromptReadonly() ? Qt.ArrowCursor : Qt.PointingHandCursor
                                                            ToolTip.visible: containsMouse
                                                            ToolTip.delay: 300
                                                            ToolTip.text: modelData.description
                                                            onClicked: {
                                                                if (!window.currentPromptReadonly()) {
                                                                    window.insertPromptSnippet(modelData.value)
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }

                                        Text {
                                            text: "작성 샘플은 읽기 전용입니다. '샘플에서 새 프롬프트 만들기'를 눌러 복사본을 만든 뒤 수정하세요."
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 11
                                            color: Colors.textSecondary
                                            wrapMode: Text.Wrap
                                            visible: window.isPromptSample(window.currentAIPromptDocument)
                                        }
                                    }
                                }
                            }
                        }

                        // Web-based WYSIWYG Editor - only visible when note selected or AI prompt selected
                        WebNoteEditor {
                            id: noteEditor
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            visible: window.activeContentMode === "notes" ? (window.selectedNoteId !== "" || window.isDraftNewNote) : (window.selectedAIPromptDocId !== "")

                            noteId: window.activeContentMode === "notes" ? window.selectedNoteId : window.selectedAIPromptDocId
                            title: window.activeContentMode === "notes" ? (window.currentNote ? (window.currentNote.title || "") : "") : (window.currentAIPromptDocument ? (window.currentAIPromptDocument.title || "") : "")
                            content: window.activeContentMode === "notes" ? (window.currentNote ? (window.currentNote.content || "") : "") : (window.currentAIPromptDocument ? (window.currentAIPromptDocument.content_md || "") : "")
                            contentJson: window.activeContentMode === "notes" ? (window.currentNote ? (window.currentNote.content_json || "") : "") : ""
                            saveStatus: noteController ? noteController.saveStatus : "saved"
                            editorZoom: window.editorZoom
                            readOnly: window.activeContentMode === "ai_prompts" && (window.currentAIPromptDocument && window.currentAIPromptDocument.readonly)

                            // Primary handler: receives title + markdown + JSON in one shot
                            // Updates in-memory state only; persistence is driven by the debounced autosave.
                            onContentUpdated: (newTitle, newMarkdown, newJson) => {
                                if (window.activeContentMode === "ai_prompts") {
                                    // Update AI prompt document cache
                                    if (!window.currentAIPromptDocument) window.currentAIPromptDocument = {}
                                    window.currentAIPromptDocument.content_md = newMarkdown || ""
                                    window.updatePromptWarnings(newMarkdown || "")
                                    return
                                }

                                if (!noteController) return

                                // Detect title-touched: any non-empty title coming from editor counts
                                if (newTitle && newTitle.trim()) {
                                    window.titleTouchedByUser = true
                                }

                                // Update local cache so flushSaveIfDirty sees fresh values.
                                // Reassigning currentNote would retrigger editor bindings; we mutate members
                                // and only emit a property reset on title change to refresh tab title.
                                if (!window.currentNote) window.currentNote = {}
                                var titleChanged = (window.currentNote.title || "") !== (newTitle || "")
                                window.currentNote.title = newTitle || ""
                                window.currentNote.content = newMarkdown || ""
                                window.currentNote.content_json = newJson || ""

                                if (!window.isDraftNewNote && titleChanged && newTitle) {
                                    window.updateTabTitle(window.selectedNoteId, newTitle)
                                }
                                // Actual DB write happens when autosaveTimer fires (requestAutosave)
                                // or on focusout (requestFlush).
                            }

                            // Fallback: old-format signals (backward compat)
                            onTitleEdited: (newTitle) => {
                                if (newTitle && newTitle.trim()) {
                                    window.titleTouchedByUser = true
                                }
                                if (!window.currentNote) window.currentNote = {}
                                window.currentNote.title = newTitle || ""
                            }

                            onContentEdited: (newContent) => {
                                // In-memory cache only; autosave timer handles persistence
                                if (!window.currentNote) window.currentNote = {}
                                window.currentNote.content = newContent || ""
                            }

                            // Debounced autosave (fires after user stops typing ~1.2s)
                            onRequestAutosave: window.flushSaveIfDirty()

                            // Focus-out flush: stop debounce and save immediately
                            onRequestFlush: window.flushSaveIfDirty()

                            onRequestExportCurrentNote: (newTitle, newMarkdown, newJson) => {
                                window.openCurrentExportDialog(newTitle, newMarkdown, newJson)
                            }

                            onPdfExportFinished: (filePath, success) => {
                                window.exportBusy = false
                                if (success) {
                                    window.exportStatusError = false
                                    window.exportStatusMessage = "PDF 내보내기가 완료되었습니다."
                                    window.exportLastOutputPath = filePath || ""
                                } else {
                                    window.exportStatusError = true
                                    window.exportStatusMessage = "PDF 내보내기에 실패했습니다."
                                    window.exportLastOutputPath = ""
                                }
                            }
                        }

                        // ── Tag row (note tags display + edit) ───────────────
                        RowLayout {
                            Layout.fillWidth: true
                            visible: window.selectedNoteId !== ""
                            spacing: 4

                            Text {
                                text: "#"
                                font.family: Typography.fontPrimary
                                font.pixelSize: 11
                                color: Colors.textTertiary
                                font.weight: Typography.weightMedium
                            }

                            // Existing tags
                            Repeater {
                                model: window.currentNote ? (window.currentNote.tags || []) : []
                                delegate: Item {
                                    property bool tagChipHovered: false
                                    height: 20
                                    width: chipRow.implicitWidth + 12

                                    Rectangle {
                                        anchors.fill: parent
                                        radius: Metrics.radiusFull
                                        color: tagChipHovered ? Colors.primary100 : Colors.bgTertiary
                                        border.color: tagChipHovered ? Colors.primary300 : Colors.borderLight
                                        border.width: 1
                                        Behavior on color { ColorAnimation { duration: Metrics.durationFast } }
                                    }

                                    Row {
                                        id: chipRow
                                        anchors.centerIn: parent
                                        spacing: 3
                                        Text {
                                            text: modelData
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 10
                                            color: Colors.primary600
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                        Rectangle {
                                            width: 16
                                            height: 16
                                            color: "transparent"
                                            anchors.verticalCenter: parent.verticalCenter

                                            Text {
                                                id: deleteX
                                                anchors.centerIn: parent
                                                text: "×"
                                                font.pixelSize: 9
                                                color: tagChipHovered ? "#DC2626" : Colors.textTertiary
                                            }

                                            MouseArea {
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                cursorShape: Qt.PointingHandCursor
                                                onEntered: parent.parent.parent.tagChipHovered = true
                                                onExited: parent.parent.parent.tagChipHovered = false
                                                onClicked: {
                                                    console.log("X button clicked for tag:", modelData)
                                                    if (!window.selectedNoteId || !noteController) return
                                                    var tags = (window.currentNote && window.currentNote.tags) ? window.currentNote.tags.slice() : []
                                                    var idx = tags.indexOf(modelData)
                                                    if (idx >= 0) tags.splice(idx, 1)
                                                    noteController.updateNoteTags(window.selectedNoteId, tags)
                                                    var updated = noteController.getNote(window.selectedNoteId)
                                                    if (updated) window.currentNote = updated
                                                }
                                            }
                                        }
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        acceptedButtons: Qt.NoButton
                                        onEntered: parent.tagChipHovered = true
                                        onExited: parent.tagChipHovered = false
                                    }
                                }
                            }

                            // Add tag input
                            Rectangle {
                                id: tagInputBox
                                height: 20
                                width: tagInputField.activeFocus ? 90 : 20
                                radius: Metrics.radiusFull
                                color: tagInputField.activeFocus ? Colors.bgTertiary : (addTagMA.containsMouse ? Colors.bgTertiary : "transparent")
                                border.color: tagInputField.activeFocus ? Colors.primary300 : (addTagMA.containsMouse ? Colors.borderLight : "transparent")
                                border.width: 1
                                clip: true

                                Behavior on width { NumberAnimation { duration: 150 } }

                                TextInput {
                                    id: tagInputField
                                    anchors.fill: parent
                                    anchors.leftMargin: 6
                                    anchors.rightMargin: 6
                                    verticalAlignment: TextInput.AlignVCenter
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: 10
                                    color: Colors.textPrimary
                                    clip: true

                                    Text {
                                        anchors.fill: parent
                                        verticalAlignment: Text.AlignVCenter
                                        text: tagInputField.activeFocus ? "" : "+"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: tagInputField.activeFocus ? 0 : 13
                                        color: Colors.textTertiary
                                        visible: tagInputField.text === ""
                                    }

                                    Keys.onReturnPressed: {
                                        var raw = tagInputField.text.trim().replace(/^#/, "")
                                        if (raw && window.selectedNoteId && noteController) {
                                            var tags = (window.currentNote && window.currentNote.tags) ? window.currentNote.tags.slice() : []
                                            if (tags.indexOf(raw) < 0) tags.push(raw)
                                            noteController.updateNoteTags(window.selectedNoteId, tags)
                                            var updated = noteController.getNote(window.selectedNoteId)
                                            if (updated) window.currentNote = updated
                                        }
                                        tagInputField.text = ""
                                        tagInputField.focus = false
                                    }
                                    Keys.onEscapePressed: {
                                        tagInputField.text = ""
                                        tagInputField.focus = false
                                    }
                                }

                                MouseArea {
                                    id: addTagMA
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    visible: !tagInputField.activeFocus
                                    onClicked: tagInputField.forceActiveFocus()
                                }

                                ToolTip.visible: addTagMA.containsMouse && !tagInputField.activeFocus
                                ToolTip.text: "태그 추가"
                                ToolTip.delay: 600
                            }

                            Item { Layout.fillWidth: true }
                        }

                        // Bottom status bar
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.md

                            // Save status chip
                            SaveStatusChip {
                                status: noteController ? noteController.saveStatus : "saved"
                            }

                            // ── Zoom controls ──────────────────────────────────
                            RowLayout {
                                spacing: 2

                                // Zoom out
                                Rectangle {
                                    width: 22; height: 22
                                    radius: Metrics.radiusSm
                                    color: zoomOutMA.containsMouse ? Colors.bgTertiary : "transparent"
                                    border.color: zoomOutMA.containsMouse ? Colors.borderLight : "transparent"
                                    border.width: 1
                                    Text {
                                        anchors.centerIn: parent
                                        text: "−"
                                        font.pixelSize: 14
                                        color: Colors.textSecondary
                                    }
                                    MouseArea {
                                        id: zoomOutMA
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: window.editorZoom = Math.max(0.5, Math.round((window.editorZoom - 0.1) * 10) / 10)
                                    }
                                }

                                // Zoom label (click to reset)
                                Rectangle {
                                    width: 44; height: 22
                                    radius: Metrics.radiusSm
                                    color: zoomResetMA.containsMouse ? Colors.bgTertiary : "transparent"
                                    border.color: zoomResetMA.containsMouse ? Colors.borderLight : "transparent"
                                    border.width: 1
                                    Text {
                                        anchors.centerIn: parent
                                        text: Math.round(window.editorZoom * 100) + "%"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: 11
                                        color: window.editorZoom !== 1.0 ? Colors.primary600 : Colors.textTertiary
                                        font.weight: window.editorZoom !== 1.0 ? Typography.weightSemibold : Typography.weightRegular
                                    }
                                    MouseArea {
                                        id: zoomResetMA
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: window.editorZoom = 1.0
                                    }
                                    ToolTip.visible: zoomResetMA.containsMouse
                                    ToolTip.text: "원래 크기로 되돌리기"
                                    ToolTip.delay: 600
                                }

                                // Zoom in
                                Rectangle {
                                    width: 22; height: 22
                                    radius: Metrics.radiusSm
                                    color: zoomInMA.containsMouse ? Colors.bgTertiary : "transparent"
                                    border.color: zoomInMA.containsMouse ? Colors.borderLight : "transparent"
                                    border.width: 1
                                    Text {
                                        anchors.centerIn: parent
                                        text: "+"
                                        font.pixelSize: 14
                                        color: Colors.textSecondary
                                    }
                                    MouseArea {
                                        id: zoomInMA
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: window.editorZoom = Math.min(3.0, Math.round((window.editorZoom + 0.1) * 10) / 10)
                                    }
                                }
                            }

                            Item { Layout.fillWidth: true }

                            // Folder path + Note title
                            Text {
                                visible: window.selectedNoteId !== "" && !!noteController
                                text: {
                                    var path = noteController ? noteController.getFolderPathForNote(window.selectedNoteId) : ""
                                    var title = window.currentNote ? (window.currentNote.title || "제목 없음") : ""
                                    if (path && title) return path + "  ·  " + title
                                    return path || title
                                }
                                font.family: Typography.fontPrimary
                                font.weight: Typography.weightRegular
                                font.pixelSize: Typography.caption
                                color: Colors.textTertiary
                                elide: Text.ElideLeft
                                maximumLineCount: 1
                                Layout.maximumWidth: 280
                            }

                            // Editor mode toggle (WYSIWYG / Markdown)
                            RowLayout {
                                visible: window.selectedNoteId !== "" && !!noteController && !!window.currentNote
                                spacing: Metrics.xs

                                Rectangle {
                                    width: 60
                                    height: 24
                                    radius: Metrics.radiusSm
                                    color: "transparent"
                                    border.width: 1
                                    border.color: Colors.borderLight

                                    RowLayout {
                                        anchors.fill: parent
                                        spacing: 0

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            color: noteEditor.editorMode === "wysiwyg" ? Colors.primary200 : "transparent"
                                            radius: Metrics.radiusSm
                                            clip: true

                                            Image {
                                                anchors.centerIn: parent
                                                source: "assets/icons/editor_mode_visual.svg"
                                                sourceSize: Qt.size(16, 16)
                                                opacity: noteEditor.editorMode === "wysiwyg" ? 1.0 : 0.5
                                            }

                                            MouseArea {
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                ToolTip.text: "시각 편집 모드 (워드처럼 편집)"
                                                ToolTip.visible: containsMouse
                                                ToolTip.delay: 500
                                                onClicked: {
                                                    if (noteEditor.editorMode !== "wysiwyg") {
                                                        noteEditor.setEditorMode("wysiwyg")
                                                    }
                                                }
                                            }
                                        }

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            color: noteEditor.editorMode === "markdown" ? Colors.primary200 : "transparent"
                                            radius: Metrics.radiusSm
                                            clip: true

                                            Image {
                                                anchors.centerIn: parent
                                                source: "assets/icons/editor_mode_markdown.svg"
                                                sourceSize: Qt.size(16, 16)
                                                opacity: noteEditor.editorMode === "markdown" ? 1.0 : 0.5
                                            }

                                            MouseArea {
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                ToolTip.text: "텍스트 편집 모드 (문자로 편집)"
                                                ToolTip.visible: containsMouse
                                                ToolTip.delay: 500
                                                onClicked: {
                                                    if (noteEditor.editorMode !== "markdown") {
                                                        noteEditor.setEditorMode("markdown")
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
            }

            // AI Tab - visible only in work_ai_editor
            Rectangle {
                visible: typeof appVariant !== "undefined" && appVariant === "work_ai_editor"
                Layout.fillHeight: true
                Layout.preferredWidth: 32
                radius: Metrics.radiusLg
                color: Colors.surface
                border.color: Colors.borderLight
                border.width: 1

                Column {
                    anchors.centerIn: parent
                    spacing: -4
                    rotation: window.aiPanelOpen ? 0 : -90

                    Text {
                        text: window.aiPanelOpen ? "⟨" : "AI"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.caption
                        font.weight: Typography.weightBold
                        color: Colors.textSecondary
                    }

                    Text {
                        text: window.aiPanelOpen ? "접기" : "열기"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.caption
                        color: Colors.textTertiary
                        visible: window.aiPanelOpen
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: window.aiPanelOpen = !window.aiPanelOpen
                }
            }

            // AI Assistant Panel - visible only in work_ai_editor
            AIAssistantPanel {
                visible: typeof appVariant !== "undefined" && appVariant === "work_ai_editor" && window.aiPanelOpen
                Layout.fillHeight: true
                Layout.minimumWidth: 320
                Layout.preferredWidth: 360
                Layout.maximumWidth: 440
                z: 1000  // High z-order to ensure progress overlay renders on top
                noteEditorRef: noteEditor

                Behavior on Layout.preferredWidth {
                    NumberAnimation { duration: Metrics.durationNormal; easing.type: Easing.InOutQuart }
                }

                onOpenSettingsDialog: {
                    aiSettingsDialog.settingsMenuIndex = 0
                    aiSettingsDialog.visible = true
                }

                onOpenReferenceDocsSettings: {
                    aiSettingsDialog.settingsMenuIndex = 2
                    aiSettingsDialog.visible = true
                }
            }
        }

    }

    // ── Current Note Export Dialog ──────────────────────────────────────────
    Rectangle {
        id: currentNoteExportDialog
        visible: false
        anchors.centerIn: parent
        width: 460
        height: 360
        radius: Metrics.radiusXxl
        color: Colors.bgPrimary
        border.color: Colors.borderLight
        border.width: 1
        z: 9050

        Rectangle {
            anchors.fill: parent
            anchors.margins: -9999
            color: Qt.rgba(0, 0, 0, 0.35)
            z: -1
            MouseArea { anchors.fill: parent }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Metrics.cardPadding
            spacing: Metrics.md

            Text {
                text: window.folderExportMode ? "폴더 일괄 내보내기" : "현재 노트 내보내기"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightSemibold
                font.pixelSize: Typography.h4
                color: Colors.textPrimary
            }

            Text {
                Layout.fillWidth: true
                text: window.folderExportMode
                    ? ("범위: " + (window.folderExportLabel || "폴더")
                        + (window.folderExportScope === "folder" ? " (하위 폴더 포함)"
                            : window.folderExportScope === "favorites" ? " (즐겨 찾기 노트)"
                            : " (서재 전체)"))
                    : ("문서명: " + (window.exportDraftTitle || "무제"))
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.bodySmall
                color: Colors.textSecondary
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
            }

            Text {
                text: "포맷"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightMedium
                font.pixelSize: Typography.bodySmall
                color: Colors.textPrimary
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.xs

                Repeater {
                    model: window.folderExportMode
                        ? ["md", "txt", "hwpx", "docx"]
                        : ["md", "txt", "pdf", "hwpx", "docx"]
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        height: 34
                        radius: Metrics.radiusMd
                        color: window.exportFormat === modelData ? Colors.primary500 : Colors.bgSecondary
                        border.width: 1
                        border.color: window.exportFormat === modelData ? Colors.primary600 : Colors.borderLight

                        Text {
                            anchors.centerIn: parent
                            text: (modelData || "").toUpperCase()
                            font.family: Typography.fontPrimary
                            font.weight: Typography.weightSemibold
                            font.pixelSize: 12
                            color: window.exportFormat === modelData ? Colors.textInverse : Colors.textSecondary
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: window.exportFormat = modelData
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: (window.exportFormat || "").toLowerCase() === "hwpx"
                text: "HWPX는 현재 이미지/표 품질 보존을 위해 DOCX로 먼저 생성한 뒤, 필요 시 한글에서 HWPX로 저장하는 방식으로 내보냅니다."
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.caption
                color: Colors.textSecondary
                wrapMode: Text.Wrap
            }

            Text {
                text: "출력 폴더"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightMedium
                font.pixelSize: Typography.bodySmall
                color: Colors.textPrimary
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.xs

                Rectangle {
                    Layout.fillWidth: true
                    height: 34
                    radius: Metrics.radiusMd
                    color: Colors.bgSecondary
                    border.width: 1
                    border.color: Colors.borderLight

                    Text {
                        anchors.fill: parent
                        anchors.leftMargin: Metrics.sm
                        anchors.rightMargin: Metrics.sm
                        verticalAlignment: Text.AlignVCenter
                        text: window.exportOutputDir || "폴더를 선택하세요"
                        font.family: Typography.fontPrimary
                        font.pixelSize: 12
                        color: window.exportOutputDir ? Colors.textPrimary : Colors.textTertiary
                        elide: Text.ElideMiddle
                    }
                }

                Rectangle {
                    width: 84
                    height: 34
                    radius: Metrics.radiusMd
                    color: folderPickMA.containsMouse ? Colors.primary500 : Colors.primary400

                    Text {
                        anchors.centerIn: parent
                        text: "선택"
                        font.family: Typography.fontPrimary
                        font.pixelSize: 12
                        font.weight: Typography.weightSemibold
                        color: Colors.textInverse
                    }

                    MouseArea {
                        id: folderPickMA
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: currentExportFolderDialog.open()
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: window.exportStatusMessage.length > 0
                text: window.exportStatusMessage
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.caption
                color: window.exportStatusError ? Colors.accentRose : Colors.success
                wrapMode: Text.Wrap
            }

            Item { Layout.fillHeight: true }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.sm

                Item { Layout.fillWidth: true }

                Rectangle {
                    width: 90
                    height: 34
                    radius: Metrics.radiusMd
                    color: closeExportMA.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
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
                        id: closeExportMA
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            currentNoteExportDialog.visible = false
                            window.folderExportMode = false
                        }
                    }
                }

                Rectangle {
                    width: 90
                    height: 34
                    radius: Metrics.radiusMd
                    color: exportNowMA.containsMouse ? Colors.primary500 : Colors.primary400

                    Text {
                        anchors.centerIn: parent
                        text: "내보내기"
                        font.family: Typography.fontPrimary
                        font.pixelSize: 12
                        font.weight: Typography.weightSemibold
                        color: Colors.textInverse
                    }

                    MouseArea {
                        id: exportNowMA
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (window.folderExportMode) {
                                window.startFolderExport()
                            } else {
                                window.startCurrentNoteExport()
                            }
                        }
                    }
                }

                Rectangle {
                    visible: window.exportLastOutputPath.length > 0
                    width: 90
                    height: 34
                    radius: Metrics.radiusMd
                    color: openExportDirMA.containsMouse ? Colors.success : "#16A34A"

                    Text {
                        anchors.centerIn: parent
                        text: "폴더 열기"
                        font.family: Typography.fontPrimary
                        font.pixelSize: 12
                        font.weight: Typography.weightSemibold
                        color: "white"
                    }

                    MouseArea {
                        id: openExportDirMA
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (!currentExportController) return
                            var dir = window.exportLastOutputPath || window.exportOutputDir
                            // 단일 노트 모드일 때 exportLastOutputPath는 파일 경로일 수 있음 → 출력 폴더로 보정
                            if (!window.folderExportMode) {
                                dir = window.exportOutputDir
                            }
                            currentExportController.openDirectory(dir)
                        }
                    }
                }
            }
        }
    }

    FolderDialog {
        id: currentExportFolderDialog
        currentFolder: window.exportOutputDir ? ("file:///" + window.exportOutputDir.replace(/\\/g, "/")) : ""
        onAccepted: {
            var path = currentExportFolderDialog.currentFolder.toString()
            if (path.indexOf("file://") === 0) {
                path = path.substring(7)
                if (path.charAt(0) === '/') path = path.substring(1)
            }
            window.exportOutputDir = path
        }
    }

    Rectangle {
        id: templateManagerBackdrop
        visible: templateManagerDialog.visible
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.35)
        z: 20001
    }

    Rectangle {
        id: templateManagerDialog
        visible: false
        anchors.centerIn: parent
        width: 940
        height: 680
        radius: Metrics.radiusXxl
        color: Colors.bgPrimary
        border.color: Colors.borderLight
        border.width: 1
        z: 20002

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Metrics.md
            spacing: Metrics.sm

            RowLayout {
                Layout.fillWidth: true

                Text {
                    text: "폴더 설정"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.h4
                    font.weight: Typography.weightSemibold
                    color: Colors.textPrimary
                }

                Item { Layout.fillWidth: true }

                Rectangle {
                    width: 86
                    height: 34
                    radius: Metrics.radiusMd
                    color: closeFolderSettingsHeaderMA.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
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
                        id: closeFolderSettingsHeaderMA
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: templateManagerDialog.visible = false
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Metrics.md

                Rectangle {
                    Layout.preferredWidth: 220
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
                            Layout.fillWidth: true
                            text: templateDialogFolderId
                                ? ("현재 폴더: " + templateDialogFolderName)
                                : "현재 폴더를 선택해주세요"
                            font.family: Typography.fontPrimary
                            font.pixelSize: Typography.bodySmall
                            color: Colors.textPrimary
                            wrapMode: Text.Wrap
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Colors.borderLight
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 40
                            radius: Metrics.radiusMd
                            color: folderSettingsMenuIndex === 0 ? Colors.primary50 : (folderRenameMenuMA.containsMouse ? Colors.bgPrimary : "transparent")
                            border.width: 1
                            border.color: folderSettingsMenuIndex === 0 ? Colors.primary200 : Colors.borderLight

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: Metrics.md
                                text: "폴더 이름 변경"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: folderSettingsMenuIndex === 0 ? Typography.weightSemibold : Typography.weightRegular
                                color: folderSettingsMenuIndex === 0 ? Colors.primary700 : Colors.textSecondary
                            }

                            MouseArea {
                                id: folderRenameMenuMA
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: folderSettingsMenuIndex = 0
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 40
                            radius: Metrics.radiusMd
                            color: folderSettingsMenuIndex === 1 ? Colors.primary50 : (templateSettingsMenuMA.containsMouse ? Colors.bgPrimary : "transparent")
                            border.width: 1
                            border.color: folderSettingsMenuIndex === 1 ? Colors.primary200 : Colors.borderLight

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: Metrics.md
                                text: "템플릿 설정"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: folderSettingsMenuIndex === 1 ? Typography.weightSemibold : Typography.weightRegular
                                color: folderSettingsMenuIndex === 1 ? Colors.primary700 : Colors.textSecondary
                            }

                            MouseArea {
                                id: templateSettingsMenuMA
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: folderSettingsMenuIndex = 1
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 40
                            radius: Metrics.radiusMd
                            color: folderSettingsMenuIndex === 2 ? Colors.primary50 : (folderLocationMenuMA.containsMouse ? Colors.bgPrimary : "transparent")
                            border.width: 1
                            border.color: folderSettingsMenuIndex === 2 ? Colors.primary200 : Colors.borderLight

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: Metrics.md
                                text: "폴더 위치 변경"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: folderSettingsMenuIndex === 2 ? Typography.weightSemibold : Typography.weightRegular
                                color: folderSettingsMenuIndex === 2 ? Colors.primary700 : Colors.textSecondary
                            }

                            MouseArea {
                                id: folderLocationMenuMA
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    if (window.templateDialogFolderId && window.folderController) {
                                        window.refreshSelectableFolderItems()
                                        window.folderMoveSourceId = window.templateDialogFolderId
                                        window.folderMoveSourceName = window.templateDialogFolderName || ""
                                        window.folderMoveTargetId = ""
                                        window.folderMoveTargetName = "최상위"

                                        var items = [{ id: "", name: "최상위", depth: 0, color: Colors.primary400 }]
                                        for (var i = 0; i < window.selectableFolderItems.length; i++) {
                                            var item = window.selectableFolderItems[i]
                                            if (item && String(item.id || "") !== window.folderMoveSourceId) {
                                                items.push(item)
                                            }
                                        }
                                        window.folderMoveTargetItems = items
                                    }
                                    folderSettingsMenuIndex = 2
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 40
                            radius: Metrics.radiusMd
                            color: folderSettingsMenuIndex === 3 ? Colors.primary50 : (folderOrderMenuMA.containsMouse ? Colors.bgPrimary : "transparent")
                            border.width: 1
                            border.color: folderSettingsMenuIndex === 3 ? Colors.primary200 : Colors.borderLight

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: Metrics.md
                                text: "폴더 순서 변경"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: folderSettingsMenuIndex === 3 ? Typography.weightSemibold : Typography.weightRegular
                                color: folderSettingsMenuIndex === 3 ? Colors.primary700 : Colors.textSecondary
                            }

                            MouseArea {
                                id: folderOrderMenuMA
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    if (window.templateDialogFolderId && window.folderController) {
                                        window.setupFolderOrderData()
                                    }
                                    folderSettingsMenuIndex = 3
                                }
                            }
                        }

                        Item { Layout.fillHeight: true }
                    }
                }

                StackLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: folderSettingsMenuIndex

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
                            spacing: Metrics.md

                            Text {
                                text: "폴더 이름 변경"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.h5
                                font.weight: Typography.weightSemibold
                                color: Colors.textPrimary
                            }

                            Text {
                                Layout.fillWidth: true
                                text: "선택한 폴더의 이름을 변경합니다."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textSecondary
                            }

                            TextField {
                                Layout.fillWidth: true
                                placeholderText: "폴더 이름"
                                text: window.folderRenameEditName
                                onTextChanged: window.folderRenameEditName = text
                            }

                            RowLayout {
                                Layout.fillWidth: true

                                Item { Layout.fillWidth: true }

                                Rectangle {
                                    width: 120
                                    height: 34
                                    radius: Metrics.radiusMd
                                    color: renameFolderSaveMA.containsMouse ? Colors.primary500 : Colors.primary400

                                    Text {
                                        anchors.centerIn: parent
                                        text: "이름 저장"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: 12
                                        font.weight: Typography.weightSemibold
                                        color: Colors.textInverse
                                    }

                                    MouseArea {
                                        id: renameFolderSaveMA
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: window.saveFolderNameSetting()
                                    }
                                }
                            }

                            Text {
                                Layout.fillWidth: true
                                visible: window.templateStatusMessage.length > 0
                                text: window.templateStatusMessage
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.caption
                                color: window.templateStatusError ? Colors.accentRose : Colors.success
                                wrapMode: Text.Wrap
                            }

                            Item { Layout.fillHeight: true }
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
                            anchors.margins: Metrics.sm
                            spacing: Metrics.sm

                            Rectangle {
                                Layout.fillWidth: true
                                height: 64
                                radius: Metrics.radiusLg
                                color: Colors.bgPrimary
                                border.width: 1
                                border.color: Colors.borderLight

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: Metrics.sm
                                    spacing: Metrics.sm

                                    Text {
                                        text: templateDialogFolderPath ? ("이 폴더의 기본 템플릿: " + templateDialogFolderPath) : "이 폴더의 기본 템플릿"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: Typography.bodySmall
                                        color: Colors.textPrimary
                                        Layout.fillWidth: true
                                        wrapMode: Text.Wrap
                                    }

                                    ComboBox {
                                        id: defaultTemplateCombo
                                        Layout.preferredWidth: 240
                                        model: window.templateSelectionItems
                                        textRole: "name"
                                        currentIndex: window.indexOfTemplateSelection(window.templateSelectedDefaultId)
                                        onActivated: {
                                            if (currentIndex >= 0 && currentIndex < window.templateSelectionItems.length) {
                                                window.templateSelectedDefaultId = window.templateSelectionItems[currentIndex].id || ""
                                            }
                                        }
                                    }

                                    Rectangle {
                                        width: 108
                                        height: 34
                                        radius: Metrics.radiusMd
                                        color: applyDefaultTemplateMA.containsMouse ? Colors.primary500 : Colors.primary400

                                        Text {
                                            anchors.centerIn: parent
                                            text: "기본 적용"
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: 12
                                            font.weight: Typography.weightSemibold
                                            color: Colors.textInverse
                                        }

                                        MouseArea {
                                            id: applyDefaultTemplateMA
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            enabled: templateDialogFolderId.length > 0
                                            onClicked: window.applySelectedFolderTemplate()
                                        }
                                    }
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: Metrics.md

                                Rectangle {
                                    Layout.preferredWidth: 200
                                    Layout.fillHeight: true
                                    radius: Metrics.radiusMd
                                    color: Colors.bgPrimary
                                    border.width: 1
                                    border.color: Colors.borderLight

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: Metrics.sm
                                        spacing: Metrics.sm

                                        RowLayout {
                                            Layout.fillWidth: true

                                            Text {
                                                text: "템플릿 목록"
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: Typography.bodySmall
                                                font.weight: Typography.weightSemibold
                                                color: Colors.textPrimary
                                            }

                                            Item { Layout.fillWidth: true }

                                            Rectangle {
                                                width: 78
                                                height: 28
                                                radius: Metrics.radiusMd
                                                color: newTemplateMA.containsMouse ? Colors.primary100 : Colors.bgPrimary
                                                border.width: 1
                                                border.color: Colors.borderLight

                                                Text {
                                                    anchors.centerIn: parent
                                                    text: "새 템플릿"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: 11
                                                    color: Colors.textPrimary
                                                }

                                                MouseArea {
                                                    id: newTemplateMA
                                                    anchors.fill: parent
                                                    hoverEnabled: true
                                                    onClicked: {
                                                        window.clearTemplateEditor()
                                                        if (templateController) {
                                                            var example = templateController.getDefaultExampleTemplate()
                                                            if (example) {
                                                                window.templateEditContent = example.content || ""
                                                            }
                                                        }
                                                        window.templateStatusMessage = ""
                                                        window.templateStatusError = false
                                                    }
                                                }
                                            }
                                        }

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            radius: Metrics.radiusMd
                                            color: Colors.bgPrimary
                                            border.width: 1
                                            border.color: Colors.borderLight

                                            ListView {
                                                id: templateListView
                                                anchors.fill: parent
                                                anchors.margins: 6
                                                model: templateController ? templateController.templates : []
                                                clip: true
                                                spacing: 6

                                                delegate: Rectangle {
                                                    width: templateListView.width
                                                    height: 54
                                                    radius: Metrics.radiusMd
                                                    color: (window.templateEditId === (modelData ? modelData.id : ""))
                                                        ? Colors.primary50 : (templateDelegateArea.containsMouse ? Colors.bgSecondary : "transparent")
                                                    border.width: 1
                                                    border.color: (window.templateEditId === (modelData ? modelData.id : ""))
                                                        ? Colors.primary200 : Colors.borderLight

                                                    Column {
                                                        anchors.fill: parent
                                                        anchors.margins: 10
                                                        spacing: 4

                                                        Text {
                                                            width: parent.width
                                                            text: modelData ? (modelData.name || "이름 없는 템플릿") : ""
                                                            font.family: Typography.fontPrimary
                                                            font.pixelSize: 12
                                                            font.weight: Typography.weightSemibold
                                                            color: Colors.textPrimary
                                                            elide: Text.ElideRight
                                                        }

                                                        Text {
                                                            width: parent.width
                                                            text: modelData ? (modelData.title || "제목 없음") : ""
                                                            font.family: Typography.fontPrimary
                                                            font.pixelSize: 11
                                                            color: Colors.textSecondary
                                                            elide: Text.ElideRight
                                                        }
                                                    }

                                                    MouseArea {
                                                        id: templateDelegateArea
                                                        anchors.fill: parent
                                                        hoverEnabled: true
                                                        onClicked: window.loadTemplateEditor(modelData ? modelData.id : "")
                                                    }
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
                                    border.width: 1
                                    border.color: Colors.borderLight

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: Metrics.sm
                                        spacing: Metrics.sm

                                        Text {
                                            text: templateEditId ? "템플릿 편집" : "템플릿 만들기"
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: Typography.bodySmall
                                            font.weight: Typography.weightSemibold
                                            color: Colors.textPrimary
                                        }

                                        TextField {
                                            Layout.fillWidth: true
                                            placeholderText: "템플릿 이름"
                                            text: window.templateEditName
                                            onTextChanged: window.templateEditName = text
                                        }

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            radius: Metrics.radiusMd
                                            color: Colors.surface
                                            border.width: 1
                                            border.color: window.templateEditContent.length > 0 ? Colors.borderMedium : Colors.borderLight

                                            ScrollView {
                                                anchors.fill: parent
                                                anchors.margins: Metrics.sm
                                                clip: true

                                                TextArea {
                                                    width: parent.width
                                                    placeholderText: "템플릿 본문 (첫 줄이 노트 제목이 됩니다)"
                                                    text: window.templateEditContent
                                                    wrapMode: TextEdit.Wrap
                                                    onTextChanged: window.templateEditContent = text
                                                    background: Item {}
                                                }
                                            }
                                        }

                                        Text {
                                            Layout.fillWidth: true
                                            visible: window.templateStatusMessage.length > 0
                                            text: window.templateStatusMessage
                                            font.family: Typography.fontPrimary
                                            font.pixelSize: Typography.caption
                                            color: window.templateStatusError ? Colors.accentRose : Colors.success
                                            wrapMode: Text.Wrap
                                        }

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: Metrics.sm

                                            Rectangle {
                                                width: 86
                                                height: 34
                                                radius: Metrics.radiusMd
                                                color: clearTemplateMA.containsMouse ? Colors.bgTertiary : Colors.bgPrimary
                                                border.width: 1
                                                border.color: Colors.borderLight

                                                Text {
                                                    anchors.centerIn: parent
                                                    text: "초기화"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: 12
                                                    color: Colors.textSecondary
                                                }

                                                MouseArea {
                                                    id: clearTemplateMA
                                                    anchors.fill: parent
                                                    hoverEnabled: true
                                                    onClicked: window.clearTemplateEditor()
                                                }
                                            }

                                            Rectangle {
                                                width: 86
                                                height: 34
                                                radius: Metrics.radiusMd
                                                visible: window.templateEditId.length > 0
                                                color: deleteTemplateMA.containsMouse ? Colors.accentRose : Colors.accentRoseLight

                                                Text {
                                                    anchors.centerIn: parent
                                                    text: "삭제"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: 12
                                                    font.weight: Typography.weightSemibold
                                                    color: deleteTemplateMA.containsMouse ? "white" : Colors.accentRose
                                                }

                                                MouseArea {
                                                    id: deleteTemplateMA
                                                    anchors.fill: parent
                                                    hoverEnabled: true
                                                    onClicked: window.deleteCurrentTemplate()
                                                }
                                            }

                                            Item { Layout.fillWidth: true }

                                            Rectangle {
                                                width: 96
                                                height: 34
                                                radius: Metrics.radiusMd
                                                color: saveTemplateMA.containsMouse ? Colors.primary500 : Colors.primary400

                                                Text {
                                                    anchors.centerIn: parent
                                                    text: window.templateEditId ? "저장" : "생성"
                                                    font.family: Typography.fontPrimary
                                                    font.pixelSize: 12
                                                    font.weight: Typography.weightSemibold
                                                    color: Colors.textInverse
                                                }

                                                MouseArea {
                                                    id: saveTemplateMA
                                                    anchors.fill: parent
                                                    hoverEnabled: true
                                                    onClicked: window.saveTemplateEditor()
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
                            anchors.margins: Metrics.sm
                            spacing: Metrics.md

                            Text {
                                text: "폴더 위치 변경"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.h5
                                font.weight: Typography.weightSemibold
                                color: Colors.textPrimary
                            }

                            Text {
                                Layout.fillWidth: true
                                text: folderMoveSourceName ? ("'" + folderMoveSourceName + "' 폴더를 이동할 위치를 선택하세요.") : "이동할 위치를 선택하세요."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textSecondary
                                wrapMode: Text.Wrap
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.sm

                                Rectangle {
                                    width: 80
                                    height: 34
                                    radius: Metrics.radiusMd
                                    color: window.canPreviewFolderMove() ? (moveFolderPreviewMA.containsMouse ? Colors.primary500 : Colors.primary400) : Colors.bgTertiary

                                    Text {
                                        anchors.centerIn: parent
                                        text: "이동"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: 12
                                        font.weight: Typography.weightSemibold
                                        color: window.canPreviewFolderMove() ? Colors.textInverse : Colors.textTertiary
                                    }

                                    MouseArea {
                                        id: moveFolderPreviewMA
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        enabled: window.canPreviewFolderMove()
                                        onClicked: {
                                            window.moveFolderInDraftOnly(window.selectedMoveTargetId)
                                        }
                                    }
                                }

                                Rectangle {
                                    width: 80
                                    height: 34
                                    radius: Metrics.radiusMd
                                    color: window.hasFolderPlacementChanges() ? (moveFolderApplyMA.containsMouse ? Colors.primary500 : Colors.primary400) : Colors.bgTertiary

                                    Text {
                                        anchors.centerIn: parent
                                        text: "적용"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: 12
                                        font.weight: Typography.weightSemibold
                                        color: window.hasFolderPlacementChanges() ? Colors.textInverse : Colors.textTertiary
                                    }

                                    MouseArea {
                                        id: moveFolderApplyMA
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        enabled: window.hasFolderPlacementChanges()
                                        onClicked: {
                                            window.applyFolderPlacementChanges(false)
                                        }
                                    }
                                }

                                Item { Layout.fillWidth: true }

                                Text {
                                    text: window.folderPlacementStatusMessage.length > 0
                                        ? window.folderPlacementStatusMessage
                                        : ("선택 위치: " + (window.selectedMoveTargetName || "최상위"))
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: window.folderPlacementStatusError ? Colors.accentRose : (window.folderPlacementStatusMessage.length > 0 ? Colors.primary600 : Colors.textTertiary)
                                    elide: Text.ElideRight
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: Metrics.radiusLg
                                color: Colors.bgPrimary
                                border.width: 1
                                border.color: Colors.borderLight

                                ListView {
                                    id: folderMoveListViewIntegrated
                                    anchors.fill: parent
                                    anchors.margins: Metrics.sm
                                    clip: true
                                    ScrollBar.vertical: ScrollBar {
                                        policy: ScrollBar.AsNeeded
                                    }
                                    model: folderMovePreviewItems
                                    cacheBuffer: 0
                                    spacing: 4

                                    delegate: Rectangle {
                                        property var folderData: modelData
                                        property string targetId: folderData && folderData.id !== undefined ? String(folderData.id) : ""
                                        property bool isSelected: window.selectedMoveTargetId === targetId
                                        property bool isSourceFolder: targetId === window.folderMoveSourceId
                                        property bool isValidTarget: !isSourceFolder && window.isValidMoveTarget(targetId)

                                        width: folderMoveListViewIntegrated.width
                                        height: 38
                                        radius: Metrics.radiusMd
                                        color: isSourceFolder ? Colors.primary50 : (isSelected ? Colors.primary50 : (folderMoveHoverIntegrated.containsMouse && isValidTarget ? Colors.bgSecondary : "transparent"))
                                        border.width: 1
                                        border.color: isSourceFolder ? Colors.warning : (isSelected ? Colors.primary200 : Colors.borderLight)

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.leftMargin: Metrics.md + ((folderData && folderData.depth ? folderData.depth : 0) * 14)
                                            anchors.rightMargin: Metrics.md
                                            spacing: Metrics.sm

                                            Rectangle {
                                                width: 14
                                                height: 14
                                                radius: 3
                                                color: folderData && folderData.color ? folderData.color : Colors.primary400
                                            }

                                            Text {
                                                Layout.fillWidth: true
                                                text: folderData && folderData.name ? folderData.name : "폴더"
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: Typography.bodySmall
                                                font.weight: (isSelected || isSourceFolder) ? Typography.weightSemibold : Typography.weightRegular
                                                color: isSourceFolder ? Colors.warning : (isSelected ? Colors.primary700 : Colors.textPrimary)
                                                elide: Text.ElideRight
                                            }
                                        }

                                        MouseArea {
                                            id: folderMoveHoverIntegrated
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            enabled: isValidTarget
                                            onClicked: {
                                                folderMoveListViewIntegrated.currentIndex = index
                                                window.selectedMoveTargetId = targetId
                                                window.selectedMoveTargetName = folderData && folderData.name ? folderData.name : "최상위"
                                                window.folderPlacementChangeCounter++
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
                            anchors.margins: Metrics.sm
                            spacing: Metrics.md

                            Text {
                                text: "폴더 순서 변경"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.h5
                                font.weight: Typography.weightSemibold
                                color: Colors.textPrimary
                            }

                            Text {
                                Layout.fillWidth: true
                                text: templateDialogFolderName ? ("'" + templateDialogFolderName + "' 폴더와 동일 레벨의 폴더 순서를 변경합니다.") : "폴더 순서를 변경합니다."
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textSecondary
                                wrapMode: Text.Wrap
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.sm

                                Text {
                                    text: "순서 변경"
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textSecondary
                                }

                                Rectangle {
                                    width: 70
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: draftOrderItems.length > 1 ? (folderOrderUpMA.containsMouse ? Colors.primary500 : Colors.primary400) : Colors.bgTertiary
                                    border.width: 1
                                    border.color: Colors.borderLight

                                    Text {
                                        anchors.centerIn: parent
                                        text: "위로"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: 12
                                        color: draftOrderItems.length > 1 ? Colors.textInverse : Colors.textTertiary
                                    }

                                    MouseArea {
                                        id: folderOrderUpMA
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        enabled: draftOrderItems.length > 1
                                        onClicked: {
                                            window.reorderFolderInDraftOnly(-1)
                                        }
                                    }
                                }

                                Rectangle {
                                    width: 70
                                    height: 32
                                    radius: Metrics.radiusMd
                                    color: draftOrderItems.length > 1 ? (folderOrderDownMA.containsMouse ? Colors.primary500 : Colors.primary400) : Colors.bgTertiary
                                    border.width: 1
                                    border.color: Colors.borderLight

                                    Text {
                                        anchors.centerIn: parent
                                        text: "아래로"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: 12
                                        color: draftOrderItems.length > 1 ? Colors.textInverse : Colors.textTertiary
                                    }

                                    MouseArea {
                                        id: folderOrderDownMA
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        enabled: draftOrderItems.length > 1
                                        onClicked: {
                                            window.reorderFolderInDraftOnly(1)
                                        }
                                    }
                                }

                                Rectangle {
                                    width: 80
                                    height: 34
                                    radius: Metrics.radiusMd
                                    color: window.hasFolderPlacementChanges() ? (folderOrderApplyMA.containsMouse ? Colors.primary500 : Colors.primary400) : Colors.bgTertiary

                                    Text {
                                        anchors.centerIn: parent
                                        text: "적용"
                                        font.family: Typography.fontPrimary
                                        font.pixelSize: 12
                                        font.weight: Typography.weightSemibold
                                        color: window.hasFolderPlacementChanges() ? Colors.textInverse : Colors.textTertiary
                                    }

                                    MouseArea {
                                        id: folderOrderApplyMA
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        enabled: window.hasFolderPlacementChanges()
                                        onClicked: {
                                            window.applyFolderPlacementChanges(false)
                                        }
                                    }
                                }

                                Item { Layout.fillWidth: true }

                                Text {
                                    text: window.hasFolderPlacementChanges() ? "변경 예정" : ""
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.caption
                                    color: Colors.primary600
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: Metrics.radiusLg
                                color: Colors.bgPrimary
                                border.width: 1
                                border.color: Colors.borderLight

                                ListView {
                                    id: folderOrderListView
                                    anchors.fill: parent
                                    anchors.margins: Metrics.sm
                                    clip: true
                                    ScrollBar.vertical: ScrollBar {
                                        policy: ScrollBar.AsNeeded
                                    }
                                    model: draftOrderItems
                                    spacing: 4

                                    delegate: Rectangle {
                                        property var folderData: modelData
                                        property string folderId: folderData && folderData.id !== undefined ? String(folderData.id) : ""
                                        property bool isSourceFolder: folderId === window.folderMoveSourceId

                                        width: folderOrderListView.width
                                        height: 38
                                        radius: Metrics.radiusMd
                                        color: isSourceFolder ? Colors.primary50 : (folderOrderHover.containsMouse ? Colors.bgSecondary : "transparent")
                                        border.width: 1
                                        border.color: isSourceFolder ? Colors.warning : Colors.borderLight

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.leftMargin: Metrics.md + ((folderData && folderData.depth ? folderData.depth : 0) * 14)
                                            anchors.rightMargin: Metrics.md
                                            spacing: Metrics.sm

                                            Rectangle {
                                                width: 14
                                                height: 14
                                                radius: 3
                                                color: folderData && folderData.color ? folderData.color : Colors.primary400
                                            }

                                            Text {
                                                Layout.fillWidth: true
                                                text: folderData && folderData.name ? folderData.name : "폴더"
                                                font.family: Typography.fontPrimary
                                                font.pixelSize: Typography.bodySmall
                                                color: Colors.textPrimary
                                                elide: Text.ElideRight
                                            }
                                        }

                                        MouseArea {
                                            id: folderOrderHover
                                            anchors.fill: parent
                                            hoverEnabled: true
                                        }
                                    }
                                }

                                Text {
                                    anchors.centerIn: parent
                                    visible: draftOrderItems.length <= 1
                                    text: "동일 레벨에 다른 폴더가 없습니다."
                                    font.family: Typography.fontPrimary
                                    font.pixelSize: Typography.bodySmall
                                    color: Colors.textTertiary
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Timer {
        id: importStatusTimer
        interval: 5000
        repeat: false
        onTriggered: {
            if (!window.importBusy) {
                window.importStatusMessage = ""
                window.importStatusError = false
            }
        }
    }

    // ── Busy Indicator Overlay ───────────────────────────────────────────────
    Rectangle {
        id: busyOverlay
        visible: window.importBusy || window.exportBusy
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.35)
        z: 20000
        enabled: false

        Rectangle {
            anchors.centerIn: parent
            width: 120
            height: 120
            radius: Metrics.radiusXxl
            color: Colors.bgPrimary
            border.color: Colors.borderLight
            border.width: 1

            ColumnLayout {
                anchors.centerIn: parent
                spacing: Metrics.md

                BusyIndicator {
                    Layout.alignment: Qt.AlignHCenter
                    running: window.importBusy || window.exportBusy
                    implicitWidth: 48
                    implicitHeight: 48
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: window.importBusy ? "가져오는 중..." : "내보내는 중..."
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textSecondary
                }
            }
        }
    }

    Rectangle {
        id: importStatusBanner
        visible: window.importStatusMessage.length > 0
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 16
        z: 10000
        radius: Metrics.radiusMd
        color: window.importStatusError ? Colors.accentRose : Colors.success
        height: 40
        width: Math.min(parent.width - 64, Math.max(260, statusLabel.implicitWidth + 32))

        Text {
            id: statusLabel
            anchors.centerIn: parent
            anchors.margins: 16
            text: window.importStatusMessage
            color: "white"
            font.family: Typography.fontPrimary
            font.pixelSize: Typography.bodySmall
            font.weight: Typography.weightSemibold
            elide: Text.ElideRight
        }

        MouseArea {
            anchors.fill: parent
            onClicked: {
                window.importStatusMessage = ""
                window.importStatusError = false
            }
        }
    }

    // ── Progress overlay for import/export ───────────────────────────────────────
    Rectangle {
        id: progressOverlay
        visible: window.importBusy || window.exportBusy
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.45)
        z: 30000

        Rectangle {
            anchors.centerIn: parent
            width: 360
            height: 120
            radius: Metrics.radiusXxl
            color: Colors.bgPrimary
            border.color: Colors.borderLight
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Metrics.xl
                spacing: Metrics.md

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: window.importBusy ? "가져오는 중..." : "보내는 중..."
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.body
                    font.weight: Typography.weightSemibold
                    color: Colors.textPrimary
                }

                ProgressBar {
                    Layout.fillWidth: true
                    from: 0
                    to: Math.max(1, window.importBusy ? window.importProgressTotal : window.exportProgressTotal)
                    value: window.importBusy ? window.importProgressValue : window.exportProgressValue
                    indeterminate: (window.importBusy ? window.importProgressTotal : window.exportProgressTotal) <= 1
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: window.importBusy
                        ? (window.importProgressValue + "/" + window.importProgressTotal)
                        : (window.exportProgressValue + "/" + window.exportProgressTotal)
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.caption
                    color: Colors.textSecondary
                    visible: (window.importBusy ? window.importProgressTotal : window.exportProgressTotal) > 1
                }
            }
        }

        MouseArea {
            anchors.fill: parent
            // Block all clicks while progress overlay is visible
        }
    }

    FolderDialog {
        id: folderImportDialog
        title: "가져올 폴더 선택"
        onAccepted: {
            // Qt 6.3+: 선택 결과는 selectedFolder. 이전 버전 호환을 위해 currentFolder도 확인.
            var picked = ""
            try {
                if (folderImportDialog.selectedFolder !== undefined && folderImportDialog.selectedFolder !== null) {
                    picked = folderImportDialog.selectedFolder.toString()
                }
            } catch (e) { picked = "" }
            if (!picked || picked.length === 0) {
                picked = folderImportDialog.currentFolder ? folderImportDialog.currentFolder.toString() : ""
            }
            console.log("[import] picked URL=" + picked)

            var raw = picked
            if (raw.indexOf("file://") === 0) {
                raw = raw.substring(7)
                if (raw.charAt(0) === '/' && raw.length >= 3 && raw.charAt(2) === ':') {
                    // Strip leading '/' for Windows paths like "/E:/foo"
                    raw = raw.substring(1)
                }
            }
            // Decode percent-encoded chars (e.g. spaces, Korean folder names)
            try { raw = decodeURIComponent(raw) } catch (e) { /* leave raw as-is */ }
            console.log("[import] resolved path=" + raw)

            if (!raw) {
                window.importStatusError = true
                window.importStatusMessage = "선택된 폴더 경로를 읽지 못했습니다."
                importStatusTimer.restart()
                return
            }
            window.runFolderImport(raw, window.importIncludeSubfolders)
        }
    }

    // ── Import Options Dialog ───────────────────────────────────────────────────
    Rectangle {
        id: importOptionsDialog
        visible: false
        anchors.centerIn: parent
        width: 400
        height: 180
        radius: Metrics.radiusXxl
        color: Colors.bgPrimary
        border.color: Colors.borderLight
        border.width: 1
        z: 20001

        Rectangle {
            anchors.fill: parent
            color: Qt.rgba(0, 0, 0, 0.35)
            z: -1
        }

        ColumnLayout {
            anchors.centerIn: parent
            spacing: Metrics.lg
            width: parent.width - 40

            Text {
                text: "가져오기 옵션"
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.h4
                font.weight: Typography.weightSemibold
                color: Colors.textPrimary
                Layout.alignment: Qt.AlignHCenter
            }

            CheckBox {
                id: includeSubfoldersCheckbox
                text: "하위 폴더 구조 포함"
                checked: window.importIncludeSubfolders
                onCheckedChanged: {
                    window.importIncludeSubfolders = checked
                }
                Layout.alignment: Qt.AlignHCenter
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.body
                contentItem: Text {
                    text: includeSubfoldersCheckbox.text
                    font: includeSubfoldersCheckbox.font
                    color: Colors.textPrimary
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: includeSubfoldersCheckbox.indicator.width + 8
                }
            }

            RowLayout {
                spacing: Metrics.md
                Layout.alignment: Qt.AlignHCenter

                Rectangle {
                    width: 100
                    height: 36
                    radius: Metrics.radiusMd
                    color: Colors.borderLight

                    Text {
                        anchors.centerIn: parent
                        text: "취소"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.bodySmall
                        color: Colors.textSecondary
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            importOptionsDialog.visible = false
                        }
                    }
                }

                Rectangle {
                    width: 100
                    height: 36
                    radius: Metrics.radiusMd
                    color: Colors.primary400

                    Text {
                        anchors.centerIn: parent
                        text: "다음"
                        font.family: Typography.fontPrimary
                        font.pixelSize: Typography.bodySmall
                        font.weight: Typography.weightSemibold
                        color: Colors.textInverse
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            importOptionsDialog.visible = false
                            folderImportDialog.open()
                        }
                    }
                }
            }
        }
    }

    // ── UI Scale Dialog ───────────────────────────────────────────────────────
    Rectangle {
        visible: uiScaleDialog.visible
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.35)
        z: 9001

        MouseArea {
            anchors.fill: parent
            onClicked: uiScaleDialog.visible = false
        }
    }

    UiScaleDialog {
        id: uiScaleDialog
        visible: false
        z: 9002

        Component.onCompleted: {
            initialScale = typeof uiScale !== "undefined" ? uiScale : 1.0
            currentScale = initialScale
        }

        onApplyRequested: function(scale) {
            if (typeof settingsService !== "undefined") {
                settingsService.set_ui_scale(scale)
            }
            visible = false
        }

        onCancelled: {
            visible = false
        }
    }

    AISettingsDialog {
        id: aiSettingsDialog
        visible: false
        z: 9002

        onClosed: {
            visible = false
        }
    }

    // ── Batch Folder Picker Dialog ──────────────────────────────────────────────
    Rectangle {
        id: batchFolderPickerBackdrop
        visible: batchFolderPickerDialog.visible
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.35)
        z: 8998

        MouseArea {
            anchors.fill: parent
        }
    }

    Rectangle {
        id: batchFolderPickerDialog
        visible: false
        anchors.centerIn: parent
        width: 520
        height: 560
        radius: Metrics.radiusXxl
        color: Colors.bgPrimary
        border.color: Colors.borderLight
        border.width: 1
        z: 8999

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Metrics.md
            spacing: Metrics.sm

            RowLayout {
                Layout.fillWidth: true

                Text {
                    text: batchActionMode === "move" ? "폴더로 이동" : "폴더로 복사"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.h4
                    font.weight: Typography.weightSemibold
                    color: Colors.textPrimary
                }

                Item { Layout.fillWidth: true }

                Rectangle {
                    width: 72
                    height: 32
                    radius: Metrics.radiusMd
                    color: closeBatchFolderMA.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
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
                        id: closeBatchFolderMA
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            batchFolderPickerDialog.visible = false
                            batchActionMode = ""
                            batchTargetFolderId = ""
                            batchTargetFolderName = ""
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                text: batchFolderHintMessage
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.bodySmall
                color: Colors.textSecondary
                wrapMode: Text.Wrap
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: Metrics.radiusLg
                color: Colors.bgSecondary
                border.color: Colors.borderLight
                border.width: 1

                ListView {
                    id: batchFolderListView
                    anchors.fill: parent
                    anchors.margins: Metrics.sm
                    clip: true
                    model: selectableFolderItems
                    spacing: 4

                    delegate: Rectangle {
                        property var folderData: modelData
                        property string folderId: folderData && folderData.id ? folderData.id : ""
                        property bool isSelected: batchTargetFolderId === folderId

                        width: batchFolderListView.width
                        height: 40
                        radius: Metrics.radiusMd
                        color: isSelected ? Colors.primary50 : (batchFolderHover.containsMouse ? Colors.bgPrimary : "transparent")
                        border.width: 1
                        border.color: isSelected ? Colors.primary200 : Colors.borderLight

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: Metrics.md + ((folderData && folderData.depth ? folderData.depth : 0) * 14)
                            anchors.rightMargin: Metrics.md
                            spacing: Metrics.sm

                            Rectangle {
                                width: 14
                                height: 14
                                radius: 3
                                color: folderData && folderData.color ? folderData.color : Colors.primary400
                            }

                            Text {
                                Layout.fillWidth: true
                                text: folderData && folderData.name ? folderData.name : "폴더"
                                font.family: Typography.fontPrimary
                                font.pixelSize: Typography.bodySmall
                                font.weight: isSelected ? Typography.weightSemibold : Typography.weightRegular
                                color: isSelected ? Colors.primary700 : Colors.textPrimary
                                elide: Text.ElideRight
                            }
                        }

                        MouseArea {
                            id: batchFolderHover
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                batchTargetFolderId = folderId
                                batchTargetFolderName = folderData && folderData.name ? folderData.name : ""
                            }
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true

                Text {
                    text: batchTargetFolderName ? ("선택 폴더: " + batchTargetFolderName) : "선택된 폴더 없음"
                    font.family: Typography.fontPrimary
                    font.pixelSize: Typography.caption
                    color: Colors.textTertiary
                }

                Item { Layout.fillWidth: true }

                Rectangle {
                    width: 92
                    height: 34
                    radius: Metrics.radiusMd
                    color: cancelBatchFolderMA.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                    border.width: 1
                    border.color: Colors.borderLight

                    Text {
                        anchors.centerIn: parent
                        text: "취소"
                        font.family: Typography.fontPrimary
                        font.pixelSize: 12
                        color: Colors.textSecondary
                    }

                    MouseArea {
                        id: cancelBatchFolderMA
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            batchFolderPickerDialog.visible = false
                            batchActionMode = ""
                            batchTargetFolderId = ""
                            batchTargetFolderName = ""
                        }
                    }
                }

                Rectangle {
                    width: 92
                    height: 34
                    radius: Metrics.radiusMd
                    color: confirmBatchFolderMA.containsMouse ? Colors.primary500 : Colors.primary400
                    opacity: window.isBatchTargetFolderUsable(batchTargetFolderId) ? 1.0 : 0.6

                    Text {
                        anchors.centerIn: parent
                        text: batchActionMode === "move" ? "이동" : "복사"
                        font.family: Typography.fontPrimary
                        font.pixelSize: 12
                        font.weight: Typography.weightSemibold
                        color: Colors.textInverse
                    }

                    MouseArea {
                        id: confirmBatchFolderMA
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: window.isBatchTargetFolderUsable(batchTargetFolderId)
                        onClicked: {
                            if (window.applyBatchNoteAction()) {
                                batchFolderPickerDialog.visible = false
                            }
                        }
                    }
                }
            }
        }
    }

    // ── Batch Delete Confirmation Dialog ───────────────────────────────────────
    Rectangle {
        id: batchDeleteConfirmBackdrop
        visible: batchDeleteConfirmDialog.visible
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.35)
        z: 9000

        MouseArea {
            anchors.fill: parent
        }
    }

    Rectangle {
        id: batchDeleteConfirmDialog
        visible: false
        anchors.centerIn: parent
        width: 360
        height: 180
        radius: Metrics.radiusXxl
        color: Colors.bgPrimary
        border.color: Colors.borderLight
        border.width: 1
        z: 9001

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Metrics.cardPadding
            spacing: Metrics.md

            Text {
                text: "노트 삭제"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightSemibold
                font.pixelSize: Typography.h4
                color: Colors.textPrimary
            }

            Text {
                Layout.fillWidth: true
                text: selectedNoteCount() + "개의 노트를 삭제할까요?"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightRegular
                font.pixelSize: Typography.body
                color: Colors.textSecondary
                wrapMode: Text.Wrap
            }

            Item { Layout.fillHeight: true }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.sm

                Item { Layout.fillWidth: true }

                Rectangle {
                    width: 80
                    height: 34
                    radius: Metrics.radiusMd
                    color: cancelBatchDeleteMA.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                    border.color: Colors.borderLight
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "취소"
                        font.family: Typography.fontPrimary
                        font.pixelSize: 13
                        color: Colors.textSecondary
                    }

                    MouseArea {
                        id: cancelBatchDeleteMA
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: batchDeleteConfirmDialog.visible = false
                    }
                }

                Rectangle {
                    width: 80
                    height: 34
                    radius: Metrics.radiusMd
                    color: confirmBatchDeleteMA.containsMouse ? "#B91C1C" : "#DC2626"

                    Text {
                        anchors.centerIn: parent
                        text: "삭제"
                        font.family: Typography.fontPrimary
                        font.weight: Typography.weightSemibold
                        font.pixelSize: 13
                        color: "white"
                    }

                    MouseArea {
                        id: confirmBatchDeleteMA
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            var ids = window.collectSelectedNoteIds()
                            if (noteController && ids.length > 0) {
                                if (noteController.deleteNotes(ids)) {
                                    batchDeleteConfirmDialog.visible = false
                                    window.closeTabsForDeletedNotes(ids)
                                    window.clearNoteSelectionState()
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // ── Note Delete Confirmation Dialog ─────────────────────────────────────
    Rectangle {
        id: deleteConfirmDialog
        visible: false
        anchors.centerIn: parent
        width: 340
        height: 160
        radius: (typeof Metrics !== "undefined" && typeof Metrics.radiusXxl === "number") ? Metrics.radiusXxl : 24
        color: Colors.bgPrimary
        border.color: Colors.borderLight
        border.width: 1
        z: 9000

        property string targetNoteId: ""
        property string targetNoteTitle: ""

        // Backdrop
        Rectangle {
            anchors.fill: parent
            anchors.margins: -9999
            color: Qt.rgba(0, 0, 0, 0.35)
            z: -1
            MouseArea { anchors.fill: parent }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Metrics.cardPadding
            spacing: Metrics.md

            Text {
                text: "노트 삭제"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightSemibold
                font.pixelSize: Typography.h4
                color: Colors.textPrimary
            }

            Text {
                Layout.fillWidth: true
                text: "\"" + deleteConfirmDialog.targetNoteTitle + "\" 을(를) 삭제할까요?"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightRegular
                font.pixelSize: Typography.body
                color: Colors.textSecondary
                wrapMode: Text.Wrap
            }

            Item { Layout.fillHeight: true }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.sm

                Item { Layout.fillWidth: true }

                // Cancel
                Rectangle {
                    width: 80; height: 34
                    radius: Metrics.radiusMd
                    color: cancelMA.containsMouse ? Colors.bgTertiary : Colors.bgSecondary
                    border.color: Colors.borderLight
                    border.width: 1
                    Text {
                        anchors.centerIn: parent
                        text: "취소"
                        font.family: Typography.fontPrimary
                        font.pixelSize: 13
                        color: Colors.textSecondary
                    }
                    MouseArea {
                        id: cancelMA
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: deleteConfirmDialog.visible = false
                    }
                }

                // Delete confirm
                Rectangle {
                    width: 80; height: 34
                    radius: Metrics.radiusMd
                    color: confirmDeleteMA.containsMouse ? "#B91C1C" : "#DC2626"
                    Text {
                        anchors.centerIn: parent
                        text: "삭제"
                        font.family: Typography.fontPrimary
                        font.weight: Typography.weightSemibold
                        font.pixelSize: 13
                        color: "white"
                    }
                    MouseArea {
                        id: confirmDeleteMA
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            var noteId = deleteConfirmDialog.targetNoteId
                            deleteConfirmDialog.visible = false
                            if (noteId && noteController) {
                                if (window.selectedNoteId === noteId) {
                                    window.selectedNoteId = ""
                                    window.currentNote = null
                                }
                                window.closeTab(noteId)
                                noteController.deleteNote(noteId)
                            }
                        }
                    }
                }
            }
        }
    }

    // New Library Dialog (custom implementation)
    Rectangle {
        id: newLibraryDialog
        visible: false
        anchors.centerIn: parent
        width: 400
        height: 280
        radius: Metrics.radiusXxl
        color: "#F1F5F9"
        border.color: "#CBD5E1"
        border.width: 1
        z: 1000

        property string libraryName: ""
        property string libraryDescription: ""
        property bool isEditMode: false
        property string editingLibraryId: ""

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Metrics.xl
            spacing: Metrics.md

            // Title
            Text {
                text: newLibraryDialog.isEditMode ? "서재 수정" : "새 서재 만들기"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightSemibold
                font.pixelSize: Typography.h4
                color: Colors.textPrimary
            }

            // Name input
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Metrics.xs

                Text {
                    text: "서재 이름"
                    font.family: Typography.fontPrimary
                    font.weight: Typography.weightMedium
                    font.pixelSize: 14
                    color: Colors.textPrimary
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 40
                    radius: Metrics.radiusMd
                    color: Colors.bgTertiary
                    border.color: nameInput.activeFocus ? Colors.primary300 : "transparent"
                    border.width: 1

                    TextInput {
                        id: nameInput
                        anchors.fill: parent
                        anchors.margins: Metrics.md
                        font.family: Typography.fontPrimary
                        font.pixelSize: 14
                        color: Colors.textPrimary
                        verticalAlignment: TextInput.AlignVCenter
                        onTextChanged: newLibraryDialog.libraryName = text
                        KeyNavigation.tab: descInput
                    }
                }
            }

            // Description input
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Metrics.xs

                Text {
                    text: "설명 (선택사항)"
                    font.family: Typography.fontPrimary
                    font.weight: Typography.weightMedium
                    font.pixelSize: 14
                    color: Colors.textPrimary
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 40
                    radius: Metrics.radiusMd
                    color: Colors.bgTertiary
                    border.color: descInput.activeFocus ? Colors.primary300 : "transparent"
                    border.width: 1

                    TextInput {
                        id: descInput
                        anchors.fill: parent
                        anchors.margins: Metrics.md
                        font.family: Typography.fontPrimary
                        font.pixelSize: 14
                        color: Colors.textPrimary
                        verticalAlignment: TextInput.AlignVCenter
                        onTextChanged: newLibraryDialog.libraryDescription = text
                        KeyNavigation.tab: okBtnArea
                    }
                }
            }

            // Buttons
            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.md

                Item { Layout.fillWidth: true }

                Rectangle {
                    width: 80
                    height: 36
                    radius: Metrics.radiusMd
                    color: cancelBtnArea.containsMouse ? Colors.bgTertiary : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: "취소"
                        font.family: Typography.fontPrimary
                        font.weight: Typography.weightMedium
                        font.pixelSize: 14
                        color: Colors.textSecondary
                    }

                    MouseArea {
                        id: cancelBtnArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            newLibraryDialog.close()
                        }
                    }
                }

                Rectangle {
                    width: 80
                    height: 36
                    radius: Metrics.radiusMd
                    color: okBtnArea.containsMouse ? Colors.primary600 : Colors.primary500

                    Text {
                        anchors.centerIn: parent
                        text: newLibraryDialog.isEditMode ? "저장" : "만들기"
                        font.family: Typography.fontPrimary
                        font.weight: Typography.weightSemibold
                        font.pixelSize: 14
                        color: "white"
                    }

                    MouseArea {
                        id: okBtnArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (newLibraryDialog.libraryName.trim() !== "" && libraryService) {
                                if (newLibraryDialog.isEditMode) {
                                    libraryService.updateLibrary(
                                        newLibraryDialog.editingLibraryId,
                                        newLibraryDialog.libraryName.trim(),
                                        newLibraryDialog.libraryDescription.trim()
                                    )
                                } else {
                                    libraryService.createLibrary(newLibraryDialog.libraryName.trim(), newLibraryDialog.libraryDescription.trim())
                                }
                                newLibraryDialog.close()
                            }
                        }
                    }
                }
            }
        }

        function open() {
            visible = true
            isEditMode = false
            editingLibraryId = ""
            libraryName = ""
            libraryDescription = ""
            nameInput.text = ""
            descInput.text = ""
            nameInput.forceActiveFocus()
        }

        function openForEdit(libraryId, name, description) {
            visible = true
            isEditMode = true
            editingLibraryId = libraryId
            libraryName = name || ""
            libraryDescription = description || ""
            nameInput.text = libraryName
            descInput.text = libraryDescription
            nameInput.forceActiveFocus()
            nameInput.selectAll()
        }

        function close() {
            visible = false
        }

        Keys.onEscapePressed: close()
    }

    Rectangle {
        id: deleteLibraryDialog
        visible: false
        anchors.centerIn: parent
        width: 420
        height: 240
        radius: Metrics.radiusXxl
        color: "#F1F5F9"
        border.color: "#CBD5E1"
        border.width: 1
        z: 1001

        property string targetLibraryId: ""
        property string targetLibraryName: ""
        property int noteCount: 0

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Metrics.xl
            spacing: Metrics.md

            Text {
                text: "서재 삭제"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightSemibold
                font.pixelSize: Typography.h5
                color: Colors.textPrimary
            }

            Text {
                Layout.fillWidth: true
                text: "'" + deleteLibraryDialog.targetLibraryName + "' 서재를 삭제하시겠습니까?"
                wrapMode: Text.WordWrap
                font.family: Typography.fontPrimary
                font.pixelSize: 14
                color: Colors.textPrimary
            }

            Text {
                Layout.fillWidth: true
                text: deleteLibraryDialog.noteCount > 0
                      ? "삭제 불가: 이 서재에 노트 " + deleteLibraryDialog.noteCount + "개가 있습니다."
                      : "삭제 가능: 이 서재에는 노트가 없습니다."
                wrapMode: Text.WordWrap
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.caption
                color: deleteLibraryDialog.noteCount > 0 ? Colors.error : Colors.success
            }

            Item { Layout.fillHeight: true }

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.md

                Item { Layout.fillWidth: true }

                Rectangle {
                    width: 80
                    height: 36
                    radius: Metrics.radiusMd
                    color: cancelDeleteArea.containsMouse ? Colors.bgTertiary : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: "취소"
                        font.family: Typography.fontPrimary
                        font.weight: Typography.weightMedium
                        font.pixelSize: 14
                        color: Colors.textSecondary
                    }

                    MouseArea {
                        id: cancelDeleteArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: deleteLibraryDialog.close()
                    }
                }

                Rectangle {
                    width: 80
                    height: 36
                    radius: Metrics.radiusMd
                    color: confirmDeleteArea.containsMouse ? Colors.accentRose : Colors.accentRoseLight
                    opacity: deleteLibraryDialog.noteCount === 0 ? 1.0 : 0.5

                    Text {
                        anchors.centerIn: parent
                        text: "삭제"
                        font.family: Typography.fontPrimary
                        font.weight: Typography.weightSemibold
                        font.pixelSize: 14
                        color: "white"
                    }

                    MouseArea {
                        id: confirmDeleteArea
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: deleteLibraryDialog.noteCount === 0
                        onClicked: {
                            if (libraryService && deleteLibraryDialog.targetLibraryId) {
                                var ok = libraryService.deleteLibrary(deleteLibraryDialog.targetLibraryId)
                                if (ok) {
                                    deleteLibraryDialog.close()
                                }
                            }
                        }
                    }
                }
            }
        }

        function openForLibrary(libraryId, libraryName) {
            targetLibraryId = libraryId
            targetLibraryName = libraryName || ""
            noteCount = libraryService ? libraryService.getLibraryNoteCount(libraryId) : 0
            visible = true
        }

        function close() {
            visible = false
        }

        Keys.onEscapePressed: close()
    }

    // ── Folder Delete Failed Dialog ─────────────────────────────────────
    Rectangle {
        id: folderDeleteFailDialog
        visible: false
        anchors.centerIn: parent
        width: 340
        height: 180
        z: 9999
        color: Colors.bgPrimary
        radius: (typeof Metrics !== "undefined" && typeof Metrics.radiusXxl === "number") ? Metrics.radiusXxl : 24
        border.width: 1
        border.color: Colors.borderLight

        property string folderName: ""
        property string failReason: ""

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Metrics.lg
            spacing: Metrics.md

            Text {
                Layout.fillWidth: true
                text: "폴더 삭제 불가"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightSemibold
                font.pixelSize: Typography.h4
                color: Colors.textPrimary
            }

            Text {
                Layout.fillWidth: true
                text: "\"" + folderDeleteFailDialog.folderName + "\" " + folderDeleteFailDialog.failReason
                font.family: Typography.fontPrimary
                font.weight: Typography.weightRegular
                font.pixelSize: Typography.body
                color: Colors.textSecondary
                wrapMode: Text.WordWrap
            }

            Item { Layout.fillHeight: true }

            Rectangle {
                Layout.alignment: Qt.AlignRight
                width: 80
                height: 36
                radius: Metrics.radiusLg
                color: okFailArea.containsMouse ? Colors.primary600 : Colors.primary500

                Text {
                    anchors.centerIn: parent
                    text: "확인"
                    font.family: Typography.fontPrimary
                    font.weight: Typography.weightSemibold
                    font.pixelSize: 14
                    color: "white"
                }

                MouseArea {
                    id: okFailArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: folderDeleteFailDialog.visible = false
                }
            }
        }

        Keys.onEscapePressed: visible = false
    }

    // Connect folder delete failed signal
    Connections {
        target: folderController
        function onFolderDeleteFailed(folderName, reason) {
            folderDeleteFailDialog.folderName = folderName
            folderDeleteFailDialog.failReason = reason
            folderDeleteFailDialog.visible = true
        }
    }

    // Prompt delete confirmation dialog
    MessageDialog {
        id: promptDeleteDialog
        property string pendingPromptDocId: ""
        title: "프롬프트 삭제"
        buttons: MessageDialog.Ok | MessageDialog.Cancel
        onAccepted: {
            if (pendingPromptDocId) {
                console.log("[Main] Confirming prompt deletion:", pendingPromptDocId)
                promptDocumentController.deletePromptDocument(pendingPromptDocId)
                window.selectedAIPromptDocId = ""
                window.currentAIPromptDocument = null
            }
            pendingPromptDocId = ""
        }
        onRejected: {
            pendingPromptDocId = ""
        }
    }
}
