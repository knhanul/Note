import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Controls
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
        function onFoldersChanged() {
            console.log("[QML] Folders changed, refreshing list...")
            // Refresh folders ListView when folders are created/deleted/renamed
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
        function onFilteredNotesChanged() {
            console.log("[QML] Filtered notes changed, selection=" + window.selectedNoteId)
            // Don't clear selection when folder changes
            // The ListView will refresh but keep the selection
        }
    }

    Connections {
        target: libraryService
        function onLibrariesChanged() {
            console.log("[QML] Libraries list changed, refreshing dropdown...")
            // Force library dropdown Repeater to refresh with new data
            if (libraryRepeater && libraryService) {
                libraryRepeater.model = libraryService.getAllLibraries()
            }
        }
        function onLibraryAdded(libraryId) {
            console.log("[QML] Library added:", libraryId, "- refreshing list...")
            // Refresh the repeater model when a new library is added
            if (libraryRepeater && libraryService) {
                libraryRepeater.model = libraryService.getAllLibraries()
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
            sidebarHidden: sidebar.Layout.preferredWidth === 0
            noteListHidden: noteList.Layout.preferredWidth === 0
            onToggleSidebar: {
                sidebar.Layout.preferredWidth = (sidebar.Layout.preferredWidth === 0) ? Metrics.sidebarWidth : 0
            }
            onToggleNoteList: {
                noteList.Layout.preferredWidth = (noteList.Layout.preferredWidth === 0) ? Metrics.noteListWidth : 0
            }
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
                z: 3000
                clip: true

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
                                    // Calculate height dynamically based on actual Repeater content
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
                                        return h;
                                    }
                                    height: Math.min(totalHeight, 400) // cap at 400px, scroll if more
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

                        // Header for Folders section with Add button
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.leftMargin: Metrics.lg
                            Layout.rightMargin: Metrics.lg
                            z: 2100

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
                                id: addFolderButton
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
                                    parent: sidebar
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
                                    z: 5000  // Very high to render above everything including note list

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
                                        var p = addFolderArea.mapToItem(sidebar, mouseX, mouseY)
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
                            Layout.fillHeight: true
                            z: 0
                            model: folderController ? folderController.folders : []
                            spacing: Metrics.xs
                            clip: true
                            ScrollBar.vertical: ScrollBar {
                                policy: ScrollBar.AsNeeded
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

                        Item { Layout.preferredHeight: Metrics.sm }

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
                clip: true

                Behavior on Layout.preferredWidth {
                    NumberAnimation { duration: Metrics.durationNormal; easing.type: Easing.InOutQuart }
                }

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
                            reuseItems: false  // Prevent delegate recycling issues

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
                                date: modelRef && modelRef.updated_at ? noteController.formatDate(modelRef.updated_at) : ""
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
