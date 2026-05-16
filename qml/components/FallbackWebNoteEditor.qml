import QtQuick
import QtQuick.Layouts
import theme
import components

ColumnLayout {
    id: root

    property string noteId: ""
    property string title: ""
    property string content: ""
    property string contentJson: ""
    property string saveStatus: "saved"
    property bool isDirty: false
    property real editorZoom: 1.0
    property string editorMode: "markdown"
    property bool readOnly: false

    signal titleEdited(string newTitle)
    signal contentEdited(string newContent)
    signal contentUpdated(string newTitle, string newMarkdown, string newJson)
    signal requestSave()
    signal requestAutosave()
    signal requestFlush()
    signal requestExportCurrentNote(string title, string markdown, string contentJson)
    signal pdfExportFinished(string filePath, bool success)
    signal requestImagePaste()
    signal imagePasted(string dataUrl)

    property bool _suppressSignals: false

    function resetEditor(markdown, json) {
        _suppressSignals = true
        titleInput.text = root.title || ""
        contentEditor.text = markdown || ""
        contentJson = json || ""
        _suppressSignals = false
    }

    function focusContent() {
        contentEditor.forceActiveFocus()
    }

    function setEditorMode(mode) {
        if (mode === "markdown" || mode === "wysiwyg") {
            root.editorMode = "markdown"
        }
    }

    function exportCurrentPdf(outputPath) {
        root.pdfExportFinished(outputPath || "", false)
    }

    function syncFromInputs() {
        if (_suppressSignals)
            return
        root.title = titleInput.text
        root.content = contentEditor.text
        root.contentUpdated(root.title, root.content, root.contentJson || "")
        root.requestAutosave()
    }

    spacing: Metrics.md

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 44
        color: "transparent"

        TextInput {
            id: titleInput
            anchors.fill: parent
            text: root.title
            enabled: !root.readOnly
            font.family: Typography.fontPrimary
            font.weight: Typography.weightSemibold
            font.pixelSize: 24
            color: Colors.textPrimary
            selectByMouse: true
            verticalAlignment: TextInput.AlignVCenter
            onTextChanged: {
                if (!_suppressSignals && text !== root.title) {
                    root.titleEdited(text)
                    root.title = text
                }
            }
        }

        Text {
            visible: titleInput.text === "" && !titleInput.activeFocus
            anchors.fill: parent
            text: "제목 없는 노트"
            font.family: Typography.fontPrimary
            font.weight: Typography.weightSemibold
            font.pixelSize: 24
            color: Colors.textTertiary
            verticalAlignment: Text.AlignVCenter
        }
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: Colors.borderLight
    }

    Flickable {
        id: flickable
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        contentWidth: width
        contentHeight: contentEditor.height

        TextEdit {
            id: contentEditor
            width: flickable.width
            height: implicitHeight
            text: root.content
            readOnly: root.readOnly
            wrapMode: TextEdit.WordWrap
            selectByMouse: true
            font.family: Typography.fontPrimary
            font.weight: Typography.weightRegular
            font.pixelSize: 14
            color: Colors.textPrimary
            onTextChanged: {
                if (!_suppressSignals && text !== root.content) {
                    root.contentEdited(text)
                    root.content = text
                    root.requestAutosave()
                }
            }
        }
    }
}
