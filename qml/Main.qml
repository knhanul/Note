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

    // Manual save shortcut (Ctrl+S)
    Shortcut {
        sequence: "Ctrl+S"
        onActivated: window.flushSaveIfDirty()
    }

    // Autosave flush helper: called by WebNoteEditor's debounced autosave and focusout flush.
    // Persists draft (if applicable) and triggers async save. Title is auto-derived only when
    // the user has not manually touched the title field and it is currently blank.
    function flushSaveIfDirty() {
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
            exportStatusError = false
            exportStatusMessage = "PDF 생성 중..."
            exportLastOutputPath = ""
            noteEditor.exportCurrentPdf(pdfPath)
            return
        }

        if (!currentExportController) {
            exportStatusError = true
            exportStatusMessage = "내보내기 컨트롤러를 찾을 수 없습니다."
            return
        }

        flushSaveIfDirty()
        var result = currentExportController.exportCurrentNote(
            exportDraftTitle || "무제",
            exportDraftMarkdown || "",
            exportDraftJson || "",
            fmt,
            exportOutputDir
        )

        if (result && result.ok) {
            exportStatusError = false
            exportStatusMessage = result.message || "내보내기 완료"
            exportLastOutputPath = result.outputPath || ""
        } else {
            exportStatusError = true
            exportStatusMessage = (result && result.message) ? result.message : "내보내기에 실패했습니다."
            exportLastOutputPath = ""
        }
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
        draftFolderId = folderController ? folderController.currentFolderId : ""
        selectedNoteId = ""
        titleTouchedByUser = false
        currentNote = { title: "", content: "", content_json: "" }
        if (noteEditor) {
            noteEditor.resetEditor()
            noteEditor.focusTitle()
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
        }
        function onFoldersChanged() {
            foldersListView.model = null
            foldersListView.model = folderController ? folderController.folders : []
        }
    }

    Connections {
        target: noteController
        function onLibraryChanged() {
            notesListView.model = null
            notesListView.model = noteController ? noteController.filteredNotes : []
            window.selectedNoteId = ""
        }
        function onFilteredNotesChanged() {
            // ListView will refresh but keep the selection
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

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        AppHeader {
            id: appHeader
            Layout.fillWidth: true
            syncIconSource: "../assets/icons/sync.svg"
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
            onSyncClicked: {
                console.log("동기화 실행 중...")
            }
            onImportClicked: {
                console.log("가져오기 실행 중...")
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
                console.log("내보내기 실행 중...")
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
                                    onClicked: sidebar.sidebarTabIdx = 1
                                }
                            }

                            Item { Layout.fillWidth: true }

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
                            visible: sidebar.sidebarTabIdx === 0
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
                                isExpanded: folderController && modelData ? !folderController.isFolderCollapsed(modelData.id) : true
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
                                text: noteController ? noteController.currentFolderName : "노트"
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

                            Item { Layout.fillWidth: true }

                            Rectangle {
                                width: 28
                                height: 28
                                radius: Metrics.radiusFull
                                color: addNoteArea.containsMouse ? Colors.primary100 : Colors.bgSecondary
                                border.width: 1
                                border.color: addNoteArea.containsMouse ? Colors.primary200 : Colors.borderLight

                                Behavior on color {
                                    ColorAnimation { duration: Metrics.durationFast }
                                }

                                MouseArea {
                                    id: addNoteArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: {
                                        window.startDraftNote()
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
                            reuseItems: false  // Prevent delegate recycling issues
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

                            // Use filtered notes from noteController
                            model: noteController ? noteController.filteredNotes : []

                            // Transition animations for list changes
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

                            delegate: NoteListItem {
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
                                isSelected: {
                                    var selected = window.selectedNoteId === noteItem.noteId
                                    console.log("[QML] isSelected check: selectedNoteId=" + window.selectedNoteId + ", noteId=" + noteItem.noteId + ", result=" + selected)
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

                                onClicked: {
                                    if (noteItem.noteId) {
                                        console.log("[QML] Note clicked:", noteItem.noteId)
                                        if (noteController) {
                                            noteController.selectNote(noteItem.noteId)
                                        }
                                        window.selectedNoteId = noteItem.noteId
                                    }
                                }

                                onPinClicked: {
                                    console.log("[QML] Pin clicked for note:", noteItem.noteId, "model id:", modelRef ? modelRef.id : "null")
                                    if (noteItem.noteId) {
                                        // Select the note first so it's highlighted
                                        window.selectedNoteId = noteItem.noteId
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
                            visible: !window.selectedNoteId && !window.isDraftNewNote
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "transparent"

                            ColumnLayout {
                                anchors.centerIn: parent
                                spacing: Metrics.md

                                Text {
                                    Layout.alignment: Qt.AlignHCenter
                                    text: "📝"
                                    font.pixelSize: 48
                                }

                                Text {
                                    Layout.alignment: Qt.AlignHCenter
                                    text: "노트를 선택하거나 새로 만들어보세요"
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightMedium
                                    font.pixelSize: 14
                                    color: Colors.textSecondary
                                }

                                Rectangle {
                                    Layout.alignment: Qt.AlignHCenter
                                    width: 140
                                    height: 36
                                    radius: Metrics.radiusLg
                                    color: createNoteBtnArea.containsMouse ? Colors.primary500 : Colors.primary400

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
                            }
                        }

                        // Web-based WYSIWYG Editor - only visible when note selected
                        WebNoteEditor {
                            id: noteEditor
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            visible: window.selectedNoteId !== "" || window.isDraftNewNote

                            noteId: window.selectedNoteId
                            title: window.currentNote ? (window.currentNote.title || "") : ""
                            content: window.currentNote ? (window.currentNote.content || "") : ""
                            contentJson: window.currentNote ? (window.currentNote.content_json || "") : ""
                            saveStatus: noteController ? noteController.saveStatus : "saved"
                            editorZoom: window.editorZoom

                            // Primary handler: receives title + markdown + JSON in one shot
                            // Updates in-memory state only; persistence is driven by the debounced autosave.
                            onContentUpdated: (newTitle, newMarkdown, newJson) => {
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
                                delegate: Rectangle {
                                    property bool tagChipHovered: false
                                    height: 20
                                    width: chipRow.implicitWidth + 12
                                    radius: Metrics.radiusFull
                                    color: tagChipHovered ? Colors.primary100 : Colors.bgTertiary
                                    border.color: tagChipHovered ? Colors.primary300 : Colors.borderLight
                                    border.width: 1
                                    Behavior on color { ColorAnimation { duration: Metrics.durationFast } }

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
                                        Text {
                                            text: "×"
                                            font.pixelSize: 9
                                            color: tagChipHovered ? "#DC2626" : Colors.textTertiary
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onEntered: parent.tagChipHovered = true
                                        onExited: parent.tagChipHovered = false
                                        onClicked: {
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

                            // Current note metadata (created + updated)
                            Text {
                                visible: window.selectedNoteId !== "" && !!noteController && !!window.currentNote
                                text: {
                                    if (!window.currentNote) return ""
                                    var created = window.currentNote.created_at ? noteController.formatDate(window.currentNote.created_at) : ""
                                    var updated = window.currentNote.updated_at ? noteController.formatDate(window.currentNote.updated_at) : ""
                                    if (created && updated && created !== updated) {
                                        return "생성: " + created + "  ·  수정: " + updated
                                    } else if (created) {
                                        return "생성: " + created
                                    } else if (updated) {
                                        return "수정: " + updated
                                    }
                                    return ""
                                }
                                font.family: Typography.fontPrimary
                                font.weight: Typography.weightRegular
                                font.pixelSize: Typography.caption
                                color: Colors.textTertiary
                            }
                        }
                    }
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
                text: "현재 노트 내보내기"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightSemibold
                font.pixelSize: Typography.h4
                color: Colors.textPrimary
            }

            Text {
                Layout.fillWidth: true
                text: "문서명: " + (window.exportDraftTitle || "무제")
                font.family: Typography.fontPrimary
                font.pixelSize: Typography.bodySmall
                color: Colors.textSecondary
                elide: Text.ElideRight
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
                    model: ["md", "txt", "pdf", "hwpx", "docx"]
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
                        onClicked: currentNoteExportDialog.visible = false
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
                        onClicked: window.startCurrentNoteExport()
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
                            if (currentExportController) {
                                currentExportController.openDirectory(window.exportOutputDir)
                            }
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
}
