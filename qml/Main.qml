import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import theme
import components

Window {
    id: window

    visible: true
    width: 1400
    height: 900
    minimumWidth: 900
    minimumHeight: 600
    title: "Nuni Note"
    color: Colors.bgPrimary

    // Properties for note selection
    property string selectedNoteId: ""
    property var currentNote: null
    
    // Library change handling - force refresh
    Connections {
        target: folderController
        function onLibraryChanged() {
            console.log("[QML] Library changed, refreshing folders...")
            // Force folders ListView to refresh
            foldersListView.model = null
            foldersListView.model = folderController ? folderController.folders : []
        }
    }

    Connections {
        target: noteController
        function onLibraryChanged() {
            console.log("[QML] Library changed, refreshing notes...")
            // Force notes ListView to refresh
            notesListView.model = null
            notesListView.model = noteController ? noteController.filteredNotes : []
            // Clear selection
            window.selectedNoteId = ""
        }
    }

    Connections {
        target: libraryService
        function onLibrariesChanged() {
            console.log("[QML] Libraries list changed, refreshing dropdown...")
            // Force library dropdown Repeater to refresh
            if (libraryRepeater) {
                var currentModel = libraryRepeater.model
                libraryRepeater.model = null
                libraryRepeater.model = currentModel
            }
        }
    }
    
    // Load note data when selection changes
    onSelectedNoteIdChanged: {
        if (selectedNoteId && noteController) {
            currentNote = noteController.getNote(selectedNoteId)
        } else {
            currentNote = null
        }
    }
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        AppHeader {
            id: appHeader
            Layout.fillWidth: true
            onToggleSidebar: sidebar.visible = !sidebar.visible
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Metrics.lg

            Rectangle {
                id: sidebar
                Layout.preferredWidth: Metrics.sidebarWidth
                Layout.fillHeight: true
                color: "transparent"

                GlassCard {
                    anchors.fill: parent
                    anchors.margins: Metrics.md
                    anchors.leftMargin: Metrics.lg
                    radius: Metrics.radiusXxl
                    baseOpacity: 0.9

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Metrics.cardPadding
                        spacing: Metrics.lg

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
                                    property var libraries: libraryService ? libraryService.getAllLibraries() : []
                                    property int libraryCount: libraries.length
                                    property int totalHeight: {
                                        var h = 2 * Metrics.sm; // top/bottom margins
                                        for (var i = 0; i < libraryCount; i++) {
                                            h += (libraries[i].description ? 48 : 32);
                                            if (i < libraryCount - 1) h += Metrics.xs; // spacing between items
                                        }
                                        return h;
                                    }
                                    height: totalHeight
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

                                    ColumnLayout {
                                        id: libraryMenuContent
                                        anchors.fill: parent
                                        anchors.margins: Metrics.sm
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

                        // Divider
                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: Colors.borderLight
                            z: 0
                        }

                        // Header for Folders section with Add button
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.leftMargin: Metrics.lg
                            Layout.rightMargin: Metrics.lg

                            Text {
                                text: "폴더"
                                font.family: Typography.fontPrimary
                                font.weight: Typography.weightSemibold
                                font.pixelSize: Typography.caption
                                color: Colors.textTertiary
                                font.letterSpacing: Typography.letterSpacingWide
                            }

                            Item { Layout.fillWidth: true }

                            // Add folder button
                            Rectangle {
                                width: 20
                                height: 20
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
                                    onClicked: {
                                        // Create new folder with default name
                                        if (folderController) {
                                            var newId = folderController.createFolder("새 폴더", Colors.primary500)
                                        }
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
                            }
                        }

                        // Folders list from controller
                        ListView {
                            id: foldersListView
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            z: 0
                            model: folderController ? folderController.folders : []
                            spacing: Metrics.xs
                            clip: true

                            delegate: FolderItem {
                                width: ListView.view.width
                                folderId: modelData ? modelData.id : ""
                                folderName: modelData ? modelData.name : ""
                                folderColor: modelData ? modelData.color : Colors.primary500
                                noteCount: modelData ? modelData.note_count : 0
                                isSelected: folderController && modelData && folderController.currentFolderId === modelData.id

                                onClicked: {
                                    if (folderController && modelData) folderController.selectFolder(modelData.id)
                                }

                                onRenameRequested: (newName) => {
                                    if (folderController && modelData) folderController.renameFolder(modelData.id, newName)
                                }

                                onDeleteRequested: {
                                    if (folderController && modelData) folderController.deleteFolder(modelData.id)
                                }
                            }
                        }

                        Item { Layout.fillHeight: true }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 80
                            radius: Metrics.radiusLg
                            color: Colors.bgSecondary
                            border.width: 1
                            border.color: Colors.borderLight

                            Text {
                                anchors.centerIn: parent
                                text: "No tags"
                                font.family: Typography.fontPrimary
                                font.weight: Typography.weightRegular
                                font.pixelSize: Typography.bodySmall
                                color: Colors.textTertiary
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

                GlassCard {
                    anchors.fill: parent
                    anchors.margins: Metrics.md
                    anchors.rightMargin: Metrics.sm
                    radius: Metrics.radiusXxl
                    baseOpacity: 0.9

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Metrics.cardPadding
                        spacing: Metrics.md

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
                                        // Create new note in current folder
                                        if (noteController && folderController) {
                                            var newId = noteController.createNote("새 노트", "", folderController.currentFolderId)
                                            window.selectedNoteId = newId
                                            // Focus the editor title after creation
                                            if (noteEditor) {
                                                noteEditor.focusTitle()
                                            }
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
                        }

                        // Notes list from controller - filtered by current folder
                        ListView {
                            id: notesListView
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: Metrics.sm
                            clip: true

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
                                width: ListView.view.width
                                title: modelData ? modelData.title || "" : ""
                                preview: modelData && modelData.content ? (modelData.content.substring(0, 80) + (modelData.content.length > 80 ? "..." : "")) : ""
                                date: modelData && modelData.updated_at ? noteController.formatDate(modelData.updated_at) : ""
                                tags: modelData && modelData.tags ? modelData.tags : []
                                isPinned: modelData ? modelData.is_pinned || false : false
                                isSelected: window.selectedNoteId === (modelData ? modelData.id : "")

                                onClicked: {
                                    if (modelData && modelData.id) {
                                        // Select note through controller
                                        if (noteController) {
                                            noteController.selectNote(modelData.id)
                                        }
                                        window.selectedNoteId = modelData.id
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
                    anchors.leftMargin: Metrics.sm
                    radius: Metrics.radiusXxl
                    baseOpacity: 0.95

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: Metrics.cardPaddingLg
                        spacing: Metrics.lg

                        // Empty state - only visible when no note selected
                        Rectangle {
                            visible: !window.selectedNoteId
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
                                            if (noteController && folderController) {
                                                var newId = noteController.createNote("새 노트", "", folderController.currentFolderId)
                                                window.selectedNoteId = newId
                                                if (noteEditor) {
                                                    noteEditor.focusTitle()
                                                }
                                            }
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
                            visible: window.selectedNoteId !== ""

                            noteId: window.selectedNoteId
                            title: window.currentNote ? (window.currentNote.title || "") : ""
                            content: window.currentNote ? (window.currentNote.content || "") : ""
                            saveStatus: noteController ? noteController.saveStatus : "saved"

                            onTitleEdited: (newTitle) => {
                                if (window.selectedNoteId && noteController) {
                                    noteController.updateNote(window.selectedNoteId, newTitle, window.currentNote ? window.currentNote.content : "")
                                }
                            }

                            onContentEdited: (newContent) => {
                                if (window.selectedNoteId && noteController) {
                                    noteController.updateNote(window.selectedNoteId, noteEditor.title, newContent)
                                }
                            }

                            onRequestSave: {
                                if (noteController) {
                                    noteController.saveCurrentNote()
                                }
                            }

                            onImagePasted: (dataUrl) => {
                                // Normalize image data for DB storage
                                if (noteController && window.selectedNoteId && dataUrl) {
                                    // Keep as data URL so note content stores image in DB
                                    var storedDataUrl = noteController.saveBase64Image(window.selectedNoteId, dataUrl)
                                    if (storedDataUrl) {
                                        console.log("Image stored in DB content (data URL)")
                                    }
                                }
                            }
                        }

                        // Bottom status bar
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.md

                            // Save status chip
                            SaveStatusChip {
                                status: noteController ? noteController.saveStatus : "saved"
                            }

                            Item { Layout.fillWidth: true }

                            // Current note metadata
                            Text {
                                visible: window.selectedNoteId && noteController && window.currentNote
                                text: {
                                    if (!window.currentNote || !window.currentNote.updated_at) return ""
                                    return "수정됨: " + noteController.formatDate(window.currentNote.updated_at)
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
}
