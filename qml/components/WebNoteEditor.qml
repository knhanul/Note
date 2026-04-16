import QtQuick
import QtQuick.Layouts
import QtWebEngine
import QtQuick.Dialogs
import theme
import components

ColumnLayout {
    id: root
    
    // Public properties
    property string noteId: ""
    property string title: ""
    property string content: ""  // Markdown content
    property string saveStatus: "saved"
    property bool isDirty: false
    
    // Signals
    signal titleEdited(string newTitle)
    signal contentEdited(string newContent)
    signal requestSave()
    signal requestImagePaste()
    signal imagePasted(string dataUrl)
    
    // File dialog for selecting local images
    FileDialog {
        id: imageFileDialog
        title: "이미지 파일 선택"
        nameFilters: ["이미지 파일 (*.png *.jpg *.jpeg *.gif *.bmp *.webp)", "모든 파일 (*)"]
        onAccepted: {
            var filePath = imageFileDialog.currentFile.toString()
            console.log("[WebNoteEditor] Selected file: " + filePath)
            
            // Remove file:// prefix (Windows: file:///C:/..., Unix: file:///...)
            if (filePath.indexOf("file://") === 0) {
                filePath = filePath.substring(7) // Remove file://
                if (filePath.charAt(0) === '/') {
                    filePath = filePath.substring(1) // Remove leading slash on Windows
                }
            }
            console.log("[WebNoteEditor] Cleaned path: " + filePath)
            console.log("[WebNoteEditor] noteId: " + root.noteId)
            console.log("[WebNoteEditor] noteController: " + (noteController ? "available" : "not available"))
            
            if (noteController && root.noteId && filePath) {
                // Convert image to data URL (stored in note content / DB)
                var savedPath = noteController.saveLocalImage(root.noteId, filePath)
                console.log("[WebNoteEditor] Saved path: " + savedPath)
                
                if (savedPath) {
                    // Insert markdown image link
                    var markdown = "\n![이미지](" + savedPath + ")\n"
                    console.log("[WebNoteEditor] Inserting markdown: " + markdown)
                    
                    // Use encodeURIComponent to safely pass markdown
                    // Build JS code that decodes and inserts
                    var encoded = encodeURIComponent(markdown)
                    var jsCode = "if (window.editorAPI) { window.editorAPI.insertMarkdownAtCursor(decodeURIComponent('" + encoded + "')); window.editorAPI.onContentChanged(); } else { console.log('editorAPI not found'); }"
                    console.log("[WebNoteEditor] JS code: " + jsCode.substring(0, 100) + "...")
                    
                    webView.runJavaScript(jsCode, function(result) {
                        console.log("[WebNoteEditor] JavaScript executed: " + result)
                    })
                }
            } else {
                console.log("[WebNoteEditor] Cannot save image - missing noteId or controller")
            }
        }
    }
    
    spacing: Metrics.md
    
    // Editor toolbar with Markdown formatting
    EditorToolbar {
        Layout.alignment: Qt.AlignLeft
        
        onFormatBold: {
            noteEditor.formatBold()
        }
        
        onFormatItalic: {
            noteEditor.formatItalic()
        }
        
        onFormatHeading: {
            noteEditor.formatHeading()
        }
        
        onFormatCode: {
            noteEditor.formatCode()
        }
        
        onInsertLink: {
            noteEditor.insertLink()
        }
        
        onInsertImage: {
            // Open file dialog for local image selection
            imageFileDialog.open()
        }
        
        onInsertTable: {
            noteEditor.insertTable()
        }
        
        onInsertBulletList: {
            noteEditor.insertBulletList()
        }
        
        onInsertNumberedList: {
            noteEditor.insertNumberedList()
        }
        
        onInsertQuote: {
            noteEditor.insertQuote()
        }
    }
    
    // Title is now extracted from first line of content
    // No separate title input field
    
    
    // Web-based WYSIWYG Editor
    Rectangle {
        Layout.fillWidth: true
        Layout.fillHeight: true
        color: "transparent"
        clip: true
        
        WebEngineView {
            id: webView
            anchors.fill: parent
            
            // Load local HTML file from application directory
            // Qt.application.directory doesn't exist, use standard path
            url: "file:///E:/Pjt/Note2/assets/editor.html"
            
            // Enable JavaScript
            settings.javascriptEnabled: true
            settings.localContentCanAccessFileUrls: true
            settings.localContentCanAccessRemoteUrls: true
            
            // Inject content when loaded
            onLoadProgressChanged: {
                if (loadProgress === 100 && root.content) {
                    // Small delay to ensure JS is ready
                    setContentTimer.start()
                }
            }
            
            // Handle console messages for communication
            onJavaScriptConsoleMessage: (level, message, lineNumber, sourceID) => {
                var msg = message.toString()
                if (msg.indexOf("EDITOR_CONTENT_CHANGED:") === 0) {
                    var content = msg.substring(23)
                    root.contentEdited(content)
                    // Extract first line as title
                    var firstLine = extractFirstLine(content)
                    if (firstLine !== root.title) {
                        root.titleEdited(firstLine)
                    }
                } else if (msg.indexOf("EDITOR_IMAGE_PASTED:") === 0) {
                    var dataUrl = msg.substring(20)
                    root.imagePasted(dataUrl)
                }
            }
        }
        
        Timer {
            id: setContentTimer
            interval: 100
            onTriggered: {
                setMarkdownContent(root.content)
            }
        }
    }
    
    // Escape string for JavaScript
    function escapeJsString(str) {
        if (!str) return ""
        return str.replace(/\\/g, "\\\\")
                  .replace(/'/g, "\\'")
                  .replace(/"/g, "\\\"")
                  .replace(/\n/g, "\\n")
                  .replace(/\r/g, "\\r")
    }
    
    // Set markdown content in editor
    function setMarkdownContent(md) {
        var escaped = escapeJsString(md || "")
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.setMarkdown('" + escaped + "'); }")
    }
    
    // Get markdown content from editor
    function getMarkdown(callback) {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.getMarkdown(); }", callback)
    }
    
    // Format functions (called from toolbar)
    function formatBold() {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.formatBold(); }")
    }
    
    function formatItalic() {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.formatItalic(); }")
    }
    
    function formatHeading() {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.formatHeading(); }")
    }
    
    function formatCode() {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.formatCode(); }")
    }
    
    function insertLink() {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.insertLink(); }")
    }
    
    function insertImage(url) {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.insertImage('" + url + "'); }")
    }
    
    function insertTable() {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.insertTable(); }")
    }
    
    function insertBulletList() {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.insertBulletList(); }")
    }
    
    function insertNumberedList() {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.insertNumberedList(); }")
    }
    
    function insertHorizontalRule() {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.insertHorizontalRule(); }")
    }
    
    function insertQuote() {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.insertQuote(); }")
    }
    
    // Extract first line from markdown content as title
    function extractFirstLine(content) {
        if (!content || content.trim() === "") {
            return "제목 없는 노트"
        }
        // Split by newline and get first non-empty line
        var lines = content.split('\n')
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim()
            // Skip markdown headings and empty lines
            if (line !== "" && !line.match(/^#{1,6}\s/)) {
                // Remove markdown formatting
                line = line.replace(/\*\*/g, '').replace(/\*/g, '').replace(/`/g, '').replace(/\[|\]/g, '').replace(/\(|\)/g, '')
                // Limit to 50 characters
                if (line.length > 50) {
                    line = line.substring(0, 50) + "..."
                }
                return line
            }
        }
        return "제목 없는 노트"
    }
    
    // Focus management
    function focusTitle() {
        // Title is now extracted from content, focus content editor instead
        focusContent()
    }
    
    function focusContent() {
        webView.forceActiveFocus()
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.focus(); }")
    }
    
    onContentChanged: {
        // Update editor when content changes externally
        if (webView.loadProgress === 100) {
            setMarkdownContent(content)
        }
    }
}
