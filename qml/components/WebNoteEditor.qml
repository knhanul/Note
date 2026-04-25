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
    property string content: ""     // Markdown content
    property string contentJson: "" // TipTap JSON (for perfect restore)
    property string saveStatus: "saved"
    property bool isDirty: false
    property real editorZoom: 1.0   // 0.5 ~ 3.0

    // Signals
    signal titleEdited(string newTitle)
    signal contentEdited(string newContent)
    signal contentUpdated(string newTitle, string newMarkdown, string newJson)
    signal requestSave()        // retained for backward compat (no longer fired by Enter)
    signal requestAutosave()    // fires after debounce window following user input
    signal requestFlush()       // fires on focusout to flush pending save
    signal requestExportCurrentNote(string title, string markdown, string contentJson)
    signal pdfExportFinished(string filePath, bool success)
    signal requestImagePaste()
    signal imagePasted(string dataUrl)

    // Internal: suppress content re-injection while editing the same note
    property bool _editorReady: false
    property string _loadedNoteId: ""
    property bool _pdfChromeHidden: false

    // Debounced autosave timer (user-stop detection)
    Timer {
        id: autosaveTimer
        interval: 1200
        repeat: false
        onTriggered: {
            console.log("[WebNoteEditor] autosaveTimer triggered -> requestAutosave")
            root.requestAutosave()
        }
    }
    
    // File dialog for selecting local images
    FileDialog {
        id: imageFileDialog
        title: "이미지 파일 선택"
        nameFilters: ["이미지 파일 (*.png *.jpg *.jpeg *.gif *.bmp *.webp)", "모든 파일 (*)"]
        onAccepted: {
            var filePath = imageFileDialog.currentFile.toString()

            // Remove file:// prefix (Windows: file:///C:/..., Unix: file:///...)
            if (filePath.indexOf("file://") === 0) {
                filePath = filePath.substring(7)
                if (filePath.charAt(0) === '/')
                    filePath = filePath.substring(1)
            }

            if (noteController && root.noteId && filePath) {
                var dataUrl = noteController.saveLocalImage(root.noteId, filePath)
                if (dataUrl) {
                    // Store data URL in window var to avoid size/escaping issues
                    webView.runJavaScript(
                        "window.__imgDataUrl = " + JSON.stringify(dataUrl) + ";" +
                        "if (window.editorAPI) { window.editorAPI.insertImage(window.__imgDataUrl); }"
                    )
                }
            }
        }
    }

    spacing: 0

    // Web-based WYSIWYG Editor (TipTap - toolbar built into React component)
    Rectangle {
        Layout.fillWidth: true
        Layout.fillHeight: true
        color: "transparent"
        clip: true
        
        WebEngineView {
            id: webView
            anchors.fill: parent
            zoomFactor: root.editorZoom
            
            // Load local HTML file from application directory
            // Qt.application.directory doesn't exist, use standard path
            url: Qt.resolvedUrl("../../assets/editor/index.html")
            
            // Enable JavaScript
            settings.javascriptEnabled: true
            settings.localContentCanAccessFileUrls: true
            settings.localContentCanAccessRemoteUrls: true
            
            // Inject content when loaded
            onLoadProgressChanged: {
                if (loadProgress === 100) {
                    setContentTimer.start()
                }
            }

            // Handle console messages for bridge communication
            onJavaScriptConsoleMessage: (level, message, lineNumber, sourceID) => {
                var msg = message.toString()
                if (msg === "EDITOR_CONTENT_CHANGED:__PAYLOAD_READY__") {
                    // Retrieve the full payload via runJavaScript (avoids console.log size limits)
                    webView.runJavaScript(
                        "JSON.stringify(window.__editorLastPayload || {})",
                        function(result) {
                            try {
                                var payload = JSON.parse(result || "{}")
                                console.log("[WebNoteEditor] payload ready mdLen=" + (payload.markdown ? payload.markdown.length : 0)
                                            + " jsonLen=" + (payload.json ? payload.json.length : 0))
                                root.contentUpdated(payload.title || "", payload.markdown || "", payload.json || "")
                                autosaveTimer.restart()
                            } catch (e) {
                                console.log("[WebNoteEditor] payload parse error: " + e)
                            }
                        }
                    )
                } else if (msg === "REQUEST_IMAGE_DIALOG") {
                    imageFileDialog.open()
                } else if (msg.indexOf("EDITOR_IMAGE_PASTED:") === 0) {
                    root.imagePasted(msg.substring(20))
                } else if (msg === "REQUEST_SAVE") {
                    // React editor emits REQUEST_SAVE on every content change (including Enter),
                    // after an internal debounce. We must grab the payload and restart our
                    // own autosave timer so the flush happens after the user stops typing.
                    webView.runJavaScript(
                        "JSON.stringify(window.__editorLastPayload || {})",
                        function(result) {
                            try {
                                var payload = JSON.parse(result || "{}")
                                root.contentUpdated(payload.title || "", payload.markdown || "", payload.json || "")
                                autosaveTimer.restart()
                            } catch (e) {}
                        }
                    )
                    return
                } else if (msg === "REQUEST_FLUSH") {
                    // Triggered by QML-injected focusout hook.
                    // Fetch fresh payload, then emit flush so caller can save immediately.
                    webView.runJavaScript(
                        "(function(){" +
                        "try { if (window.editorAPI && window.editorAPI.onContentChanged) { window.editorAPI.onContentChanged(); } } catch (_) {}" +
                        "return JSON.stringify(window.__editorLastPayload || {});" +
                        "})()",
                        function(result) {
                            try {
                                var payload = JSON.parse(result || "{}")
                                var hasPayload = payload && (
                                    payload.title !== undefined ||
                                    payload.markdown !== undefined ||
                                    payload.json !== undefined)
                                if (hasPayload) {
                                    root.contentUpdated(payload.title || "", payload.markdown || "", payload.json || "")
                                }
                            } catch (e) {}
                            autosaveTimer.stop()
                            root.requestFlush()
                        }
                    )
                } else if (msg === "REQUEST_EXPORT_CURRENT_NOTE") {
                    webView.runJavaScript(
                        "JSON.stringify(window.__editorLastPayload || {})",
                        function(result) {
                            try {
                                var payload = JSON.parse(result || "{}")
                                root.requestExportCurrentNote(
                                    payload.title || "",
                                    payload.markdown || "",
                                    payload.json || ""
                                )
                            } catch (e) {
                                root.requestExportCurrentNote(root.title || "", root.content || "", root.contentJson || "")
                            }
                        }
                    )
                }
            }

            onPdfPrintingFinished: (filePath, success) => {
                root.restoreAfterPdf()
                root.pdfExportFinished(filePath, success)
            }

            // Inject event listeners for Enter key and focus out after load
            onLoadingChanged: {
                if (loadProgress === 100) {
                    webView.runJavaScript(`
                        (function() {
                            function requestSave() {
                                var now = Date.now();
                                if (window.__nuniLastSaveReq && (now - window.__nuniLastSaveReq) < 250) {
                                    return;
                                }
                                window.__nuniLastSaveReq = now;
                                console.log('REQUEST_SAVE');
                            }

                            function attachHooks() {
                                var editorContent = document.querySelector('.ProseMirror') ||
                                                   document.querySelector('[contenteditable="true"]');
                                if (!editorContent) return false;
                                if (window.__nuniSaveHookAttached) return true;

                                window.__nuniSaveHookAttached = true;

                                // Fallback hooks:
                                // React(App.jsx) is primary save trigger, but keep QML-side fallback
                                // to guarantee REQUEST_SAVE delivery on some WebEngine timing cases.
                                // Enter save is handled by React editor to avoid duplicate/racy requests.

                                document.addEventListener('focusout', function(e) {
                                    if (!editorContent.contains(e.target)) return;
                                    setTimeout(function() {
                                        var active = document.activeElement;
                                        var stillInEditor = active && (active === editorContent || editorContent.contains(active));
                                        if (!stillInEditor) console.log('REQUEST_FLUSH');
                                    }, 0);
                                }, true);

                                return true;
                            }

                            if (attachHooks()) return 'attached';

                            var tries = 0;
                            var timer = setInterval(function() {
                                tries += 1;
                                if (attachHooks()) {
                                    clearInterval(timer);
                                    console.log('EDITOR_LISTENERS_ATTACHED');
                                } else if (tries >= 20) {
                                    clearInterval(timer);
                                    console.log('EDITOR_LISTENERS_ATTACH_TIMEOUT');
                                }
                            }, 150);

                            return 'pending';
                        })();
                    `, function(result) {
                        if (result === 'attached' || result === 'pending') {
                            console.log('[QML] Editor listeners attached successfully');
                        } else {
                            console.log('[QML] Editor listeners status:', result);
                        }
                    });
                }
            }
        }
        
        Timer {
            id: setContentTimer
            interval: 150
            repeat: false
            onTriggered: {
                setEditorContent(root.content, root.contentJson)
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
    
    // Set content: store data in window vars first, then call setContent
    // This avoids string-escaping and size issues with runJavaScript
    function setEditorContent(md, json) {
        var setMd = "window.__loadMd = " + JSON.stringify(md || "") + ";"
        var setJson = "window.__loadJson = " + JSON.stringify(json || "") + ";"
        var setNoteId = "window.__loadNoteId = " + JSON.stringify(root.noteId || "") + ";"
        webView.runJavaScript(setMd + setJson +
            setNoteId +
            "if (window.editorAPI) { window.editorAPI.setContent(window.__loadMd, window.__loadJson, window.__loadNoteId); }")
    }

    // Backward-compatible alias
    function setMarkdownContent(md) {
        setEditorContent(md, "")
    }
    
    // Get markdown content from editor
    function getMarkdown(callback) {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.getMarkdown(); }", callback)
    }

    function getCurrentHtml(callback) {
        webView.runJavaScript("if (window.editorAPI) { window.editorAPI.getHTML(); } else { ''; }", callback)
    }

    function exportCurrentPdf(outputPath) {
        if (!outputPath || outputPath.length === 0) return
        prepareForPdf()
        webView.printToPdf(outputPath)
    }

    function prepareForPdf() {
        if (root._pdfChromeHidden) return
        root._pdfChromeHidden = true
        webView.runJavaScript(`
            (function() {
                var ids = ['editorToolbarWrap', 'editorBubbleMenuWrap'];
                ids.forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) {
                        el.dataset.nuniPrevDisplay = el.style.display || '';
                        el.style.display = 'none';
                    }
                });
                return true;
            })();
        `)
    }

    function restoreAfterPdf() {
        if (!root._pdfChromeHidden) return
        root._pdfChromeHidden = false
        webView.runJavaScript(`
            (function() {
                var ids = ['editorToolbarWrap', 'editorBubbleMenuWrap'];
                ids.forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) {
                        var prev = (el.dataset && el.dataset.nuniPrevDisplay !== undefined)
                            ? el.dataset.nuniPrevDisplay : '';
                        el.style.display = prev;
                    }
                });
                return true;
            })();
        `)
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
        focusContent()
    }

    Timer {
        id: focusTimer
        interval: 200
        onTriggered: {
            webView.forceActiveFocus()
            webView.runJavaScript("if (window.editorAPI) { window.editorAPI.focus(); }")
        }
    }

    function focusContent() {
        // Delay focus to ensure editor is ready after visibility change
        focusTimer.start()
    }

    // Reset editor content without overriding bound properties
    function resetEditor() {
        if (webView.loadProgress === 100) {
            webView.runJavaScript("if (window.editorAPI) { window.editorAPI.setContent('', ''); }")
        }
    }

    onContentChanged: {
        // Only re-inject when a different note is loaded, not during user typing.
        if (webView.loadProgress === 100 && root.noteId !== root._loadedNoteId) {
            setContentTimer.restart()
        }
    }

    onNoteIdChanged: {
        // Reset debounce so pending autosave for previous note doesn't fire against new one
        autosaveTimer.stop()
        if (webView.loadProgress === 100) {
            root._loadedNoteId = root.noteId
            setContentTimer.restart()
        }
    }

    onContentJsonChanged: {
        if (webView.loadProgress === 100 && root.noteId !== root._loadedNoteId) {
            setContentTimer.restart()
        }
    }
}
