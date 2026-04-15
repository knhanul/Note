import QtQuick
import QtQuick.Layouts
import theme

Rectangle {
    id: root

    // Public properties
    property string folderId: ""
    property string folderName: ""
    property color folderColor: Colors.primary400
    property int noteCount: 0
    property bool isSelected: false
    property bool isEditing: false
    property int depth: 0  // Hierarchy depth (0 = root, 1 = child, etc.)
    property bool hasChildren: false  // Whether this folder has child folders
    property bool isExpanded: true  // Whether children are visible (only valid if hasChildren)
    property bool isSmart: false

    onIsEditingChanged: {
        if (isEditing) {
            Qt.callLater(function() {
                editInput.forceActiveFocus()
                editInput.selectAll()
            })
        }
    }

    // Signals
    signal clicked()
    signal renameRequested(string newName)
    signal deleteRequested()
    signal toggleExpanded()  // Request to toggle expand/collapse state

    // Layout
    height: 40
    radius: Metrics.radiusXl
    color: {
        if (isSelected) return Colors.primary50
        if (hoverArea.containsMouse) return Colors.bgSecondary
        return "transparent"
    }
    border.width: isSelected ? 1 : 0
    border.color: Colors.primary200

    // Animations
    Behavior on color {
        ColorAnimation { duration: Metrics.durationFast }
    }

    Behavior on scale {
        NumberAnimation { duration: Metrics.durationFast }
    }

    Behavior on opacity {
        NumberAnimation { duration: Metrics.durationFast }
    }

    // Selection indicator
    Rectangle {
        visible: root.isSelected
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 3
        radius: Metrics.radiusFull
        color: root.folderColor
        anchors.leftMargin: 8
        anchors.topMargin: 10
        anchors.bottomMargin: 10
    }

    // Content row
    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Metrics.md + (root.depth * 12)  // Indent based on depth
        anchors.rightMargin: Metrics.lg
        spacing: Metrics.sm

        // Expand/collapse button (only visible if has children)
        Rectangle {
            visible: root.hasChildren && !root.isSmart
            width: 16
            height: 16
            radius: Metrics.radiusFull
            color: expandArea.containsMouse ? Colors.primary100 : "transparent"

            Text {
                anchors.centerIn: parent
                text: root.isExpanded ? "▼" : "▶"
                font.pixelSize: 10
                color: Colors.textTertiary
            }

            MouseArea {
                id: expandArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: root.toggleExpanded()
            }
        }

        // Spacer for alignment when no expand button
        Item {
            visible: !root.hasChildren || root.isSmart
            width: 16
            height: 16
        }

        // Color indicator (folder icon)
        Rectangle {
            width: 16
            height: 12
            radius: 2
            color: root.folderColor

            Rectangle {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: 4
                radius: 2
                color: "white"
                opacity: 0.2
            }
        }

        // Name display or edit field
        StackLayout {
            Layout.fillWidth: true
            currentIndex: root.isEditing ? 1 : 0

            // Display mode
            Text {
                text: root.folderName
                font.family: Typography.fontPrimary
                font.weight: root.isSelected ? Typography.weightMedium : Typography.weightRegular
                font.pixelSize: Typography.bodySmall
                color: root.isSelected ? Colors.primary700 : Colors.textSecondary
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }

            // Edit mode
            Rectangle {
                height: 28
                color: "white"
                border.width: 1
                border.color: Colors.primary300
                radius: Metrics.radiusMd

                TextInput {
                    id: editInput
                    anchors.fill: parent
                    anchors.margins: 4
                    text: root.folderName
                    font.family: Typography.fontPrimary
                    font.weight: Typography.weightRegular
                    font.pixelSize: Typography.bodySmall
                    color: Colors.textPrimary
                    verticalAlignment: TextInput.AlignVCenter
                    selectByMouse: true

                    onAccepted: {
                        if (text.trim() !== "") {
                            root.renameRequested(text.trim())
                        }
                        root.isEditing = false
                    }

                    onActiveFocusChanged: {
                        if (!activeFocus && root.isEditing) {
                            if (text.trim() !== "") {
                                root.renameRequested(text.trim())
                            }
                            root.isEditing = false
                        }
                    }

                    Keys.onEscapePressed: {
                        root.isEditing = false
                    }

                }
            }
        }

        // Note count badge
        Rectangle {
            visible: root.noteCount > 0 && !root.isEditing
            height: 18
            width: countText.width + 12
            radius: Metrics.radiusFull
            color: root.isSelected ? root.folderColor : Colors.bgTertiary

            Behavior on color {
                ColorAnimation { duration: Metrics.durationFast }
            }

            Text {
                id: countText
                anchors.centerIn: parent
                text: root.noteCount
                font.family: Typography.fontPrimary
                font.weight: Typography.weightMedium
                font.pixelSize: 10
                color: root.isSelected ? Colors.textInverse : Colors.textTertiary
            }
        }

        // Delete button (shown on hover when selected)
        Rectangle {
            visible: (root.isSelected || hoverArea.containsMouse) && !root.isEditing && !root.isSmart
            width: 20
            height: 20
            radius: Metrics.radiusFull
            color: deleteArea.containsMouse ? Colors.accentRoseLight : "transparent"
            z: 2

            Text {
                anchors.centerIn: parent
                text: "x"
                font.family: Typography.fontPrimary
                font.weight: Typography.weightSemibold
                font.pixelSize: 10
                color: deleteArea.containsMouse ? Colors.accentRose : Colors.textTertiary
            }

            MouseArea {
                id: deleteArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: (mouse) => {
                    mouse.accepted = true
                    root.deleteRequested()
                }
            }
        }
    }

    // Main interaction area
    MouseArea {
        id: hoverArea
        anchors.fill: parent
        z: -1
        hoverEnabled: true
        enabled: !root.isEditing
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onClicked: (mouse) => {
            if (mouse.button === Qt.RightButton) {
                // Right click starts edit mode for regular folders only
                if (!root.isSmart) {
                    root.isEditing = true
                }
            } else {
                // Left click selects
                root.clicked()
            }
        }

        onDoubleClicked: {
            // Double click also starts edit mode for regular folders only
            if (!root.isSmart) {
                root.isEditing = true
            }
        }

        onPressed: root.scale = 0.98
        onReleased: root.scale = 1.0
    }

}
