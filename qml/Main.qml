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
                                            editorNoteTitle.text = "새 노트"
                                            editorContent.text = ""
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
                                title: modelData.title
                                preview: modelData.content.substring(0, 100) + (modelData.content.length > 100 ? "..." : "")
                                date: modelData.updated_at ? modelData.updated_at.substring(0, 10) : ""
                                tags: modelData.tags || []
                                isPinned: modelData.is_pinned || false
                                isSelected: window.selectedNoteId === modelData.id

                                onClicked: {
                                    window.selectedNoteId = modelData.id
                                    editorNoteTitle.text = modelData.title
                                    editorContent.text = modelData.content
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

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Metrics.sm

                            Rectangle {
                                Layout.fillWidth: true
                                height: editorNoteTitle.height
                                color: "transparent"

                                TextInput {
                                    id: editorNoteTitle
                                    anchors.fill: parent
                                    text: "아침 루틴 정리"
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightBold
                                    font.pixelSize: Typography.h2
                                    color: Colors.textPrimary
                                    selectByMouse: true
                                    verticalAlignment: TextInput.AlignVCenter
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Metrics.md

                                Text {
                                    text: "2026년 4월 13일 오전 8:39"
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightRegular
                                    font.pixelSize: Typography.caption
                                    color: Colors.textTertiary
                                }

                                Row {
                                    spacing: Metrics.sm

                                    Rectangle {
                                        width: 60
                                        height: 24
                                        radius: Metrics.radiusMd
                                        color: saveArea.containsMouse ? Colors.primary100 : Colors.bgSecondary
                                        border.width: 1
                                        border.color: Colors.borderLight

                                        MouseArea {
                                            id: saveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                        }

                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            font.family: Typography.fontPrimary
                                            font.weight: Typography.weightMedium
                                            font.pixelSize: Typography.caption
                                            color: saveArea.containsMouse ? Colors.primary600 : Colors.textSecondary
                                        }
                                    }

                                    Rectangle {
                                        width: 60
                                        height: 24
                                        radius: Metrics.radiusMd
                                        color: exportArea.containsMouse ? Colors.primary100 : Colors.bgSecondary
                                        border.width: 1
                                        border.color: Colors.borderLight

                                        MouseArea {
                                            id: exportArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                        }

                                        Text {
                                            anchors.centerIn: parent
                                            text: "Export"
                                            font.family: Typography.fontPrimary
                                            font.weight: Typography.weightMedium
                                            font.pixelSize: Typography.caption
                                            color: exportArea.containsMouse ? Colors.primary600 : Colors.textSecondary
                                        }
                                    }

                                    Rectangle {
                                        width: 60
                                        height: 24
                                        radius: Metrics.radiusMd
                                        color: stickyArea.containsMouse ? Colors.accentOrangeLight : Colors.bgSecondary
                                        border.width: 1
                                        border.color: stickyArea.containsMouse ? Colors.accentOrange : Colors.borderLight

                                        MouseArea {
                                            id: stickyArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                        }

                                        Text {
                                            anchors.centerIn: parent
                                            text: "Sticky"
                                            font.family: Typography.fontPrimary
                                            font.weight: Typography.weightMedium
                                            font.pixelSize: Typography.caption
                                            color: stickyArea.containsMouse ? Colors.accentOrange : Colors.textSecondary
                                        }
                                    }
                                }
                            }
                        }

                        EditorToolbar {
                            Layout.alignment: Qt.AlignLeft
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "transparent"
                            clip: true

                            Flickable {
                                id: editorFlickable
                                anchors.fill: parent
                                contentWidth: width
                                contentHeight: editorContent.height
                                clip: true

                                TextEdit {
                                    id: editorContent
                                    width: parent.width
                                    height: implicitHeight
                                    text: "매일 아침 6시에 일어나서 물 한 잔 마시기.\n스트레칭 10분 하고 명상하기.\n\n아침 식사는 단백질 중심으로 챙기기.\n\n이렇게 하면 하루가 훨씬 생산적으로 시작된다."
                                    font.family: Typography.fontPrimary
                                    font.weight: Typography.weightRegular
                                    font.pixelSize: Typography.bodyLarge
                                    color: Colors.textPrimary
                                    wrapMode: TextEdit.WordWrap
                                    selectByMouse: true
                                }
                            }
                        }

                        Text {
                            Layout.alignment: Qt.AlignRight
                            text: "Markdown editor with toolbar ready."
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
