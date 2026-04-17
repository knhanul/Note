import QtQuick
import QtQuick.Layouts
import theme
import components

ColumnLayout {
    id: root
    
    // Public properties
    property string noteId: ""
    property string title: ""
    property string content: ""
    property string saveStatus: "saved"  // saved, saving, dirty
    property bool isDirty: false
    property var getImageData: null  // Function callback for getting image data URL
    
    // Signals
    signal titleEdited(string newTitle)
    signal contentEdited(string newContent)
    signal requestSave()
    signal requestImagePaste()
    
    spacing: Metrics.md
    
    // Editor toolbar at top
    EditorToolbar {
        Layout.alignment: Qt.AlignLeft
        onPasteImage: {
            root.requestImagePaste()
        }
    }
    
    // Title input
    Rectangle {
        id: titleContainer
        Layout.fillWidth: true
        Layout.preferredHeight: 48
        color: "transparent"
        
        TextInput {
            id: titleInput
            anchors.fill: parent
            anchors.verticalCenter: parent.verticalCenter
            
            text: root.title
            
            font.family: Typography.fontPrimary
            font.weight: Typography.weightSemibold
            font.pixelSize: 24  // Typography.h4
            color: Colors.textPrimary
            selectByMouse: true
            verticalAlignment: TextInput.AlignVCenter
            
            onTextChanged: {
                if (text !== root.title) {
                    root.titleEdited(text)
                }
            }
            
            onActiveFocusChanged: {
                if (!activeFocus && text !== root.title) {
                    root.requestSave()
                }
            }
            
            // Select all on first focus
            onFocusChanged: {
                if (focus) {
                    selectAll()
                }
            }
        }
        
        // Placeholder text
        Text {
            visible: titleInput.text === "" && !titleInput.activeFocus
            anchors.fill: parent
            anchors.verticalCenter: parent.verticalCenter
            text: "제목 없는 노트"
            font.family: Typography.fontPrimary
            font.weight: Typography.weightSemibold
            font.pixelSize: 24  // Typography.h4
            color: Colors.textTertiary
            verticalAlignment: Text.AlignVCenter
        }
    }
    
    // Divider
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: Colors.borderLight
    }
    
    // Content editor
    Flickable {
        id: editorFlickable
        Layout.fillWidth: true
        Layout.fillHeight: true
        
        contentWidth: width
        contentHeight: contentEditor.height
        clip: true
        
        TextEdit {
            id: contentEditor
            width: editorFlickable.width
            height: implicitHeight
            
            text: root.content
            wrapMode: TextEdit.WordWrap
            selectByMouse: true
            
            font.family: Typography.fontPrimary
            font.weight: Typography.weightRegular
            font.pixelSize: 14  // Typography.body
            color: Colors.textPrimary
            
            onTextChanged: {
                if (text !== root.content) {
                    root.contentEdited(text)
                }
            }
            
            onActiveFocusChanged: {
                if (!activeFocus && text !== root.content) {
                    root.requestSave()
                }
            }
            
            // Handle paste for images
            Keys.onPressed: (event) => {
                if ((event.modifiers & Qt.ControlModifier) && event.key === Qt.Key_V) {
                    // Let QML handle the paste first, then check for image
                    root.requestImagePaste()
                }
            }
        }
        
        // Placeholder text
        Text {
            visible: contentEditor.text === "" && !contentEditor.activeFocus
            anchors.top: parent.top
            anchors.left: parent.left
            text: "여기에 내용을 입력하세요..."
            font.family: Typography.fontPrimary
            font.weight: Typography.weightRegular
            font.pixelSize: 14  // Typography.body
            color: Colors.textTertiary
        }
    }
    
    // Image preview area - shows images embedded in content
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: imagePreviewColumn.height + 20
        visible: contentEditor.text.match(/!\[.*?\]\(.*?\)/) !== null
        color: "transparent"
        border.width: 1
        border.color: Colors.borderLight
        radius: Metrics.radiusMd
        
        ColumnLayout {
            id: imagePreviewColumn
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: 10
            spacing: 10
            
            Text {
                text: "📎 첨부된 이미지"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightMedium
                font.pixelSize: 12
                color: Colors.textSecondary
            }
            
            // Parse and display markdown images
            Repeater {
                model: {
                    var matches = []
                    var regex = /!\[.*?\]\((.*?)\)/g
                    var text = contentEditor.text
                    var match
                    while ((match = regex.exec(text)) !== null) {
                        matches.push(match[1])
                    }
                    return matches
                }
                
                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 200
                    color: Colors.bgSecondary
                    radius: Metrics.radiusMd
                    clip: true
                    
                    Image {
                        id: previewImage
                        anchors.fill: parent
                        anchors.margins: 5
                        fillMode: Image.PreserveAspectFit
                        source: {
                            if (!modelData || !root.getImageData) return ""
                            var dataUrl = root.getImageData(modelData)
                            return dataUrl ? dataUrl : ""
                        }
                        smooth: true
                        
                        onStatusChanged: {
                            // Error handling for image load failure
                        }
                    }
                    
                    // Loading indicator
                    Rectangle {
                        visible: previewImage.status === Image.Loading
                        anchors.centerIn: parent
                        width: 40
                        height: 40
                        color: Colors.bgTertiary
                        radius: Metrics.radiusFull
                        
                        Text {
                            anchors.centerIn: parent
                            text: "⏳"
                            font.pixelSize: 20
                        }
                    }
                    
                    // Error indicator
                    Rectangle {
                        visible: previewImage.status === Image.Error
                        anchors.centerIn: parent
                        width: 120
                        height: 30
                        color: Colors.accentRoseLight
                        radius: Metrics.radiusMd
                        
                        Text {
                            anchors.centerIn: parent
                            text: "이미지 로드 실패"
                            font.family: Typography.fontPrimary
                            font.pixelSize: 12
                            color: Colors.accentRose
                        }
                    }
                }
            }
        }
    }
    
    // Update bindings when properties change
    onTitleChanged: {
        if (root.title !== titleInput.text) {
            titleInput.text = root.title
        }
    }
    
    onContentChanged: {
        if (root.content !== contentEditor.text) {
            contentEditor.text = root.content
        }
    }
    
    // Focus management
    function focusTitle() {
        titleInput.forceActiveFocus()
        titleInput.selectAll()
    }
    
    function focusContent() {
        contentEditor.forceActiveFocus()
    }
}
