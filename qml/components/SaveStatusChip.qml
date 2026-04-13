import QtQuick
import QtQuick.Layouts
import theme

Rectangle {
    id: root
    
    // Public properties
    property string status: "saved"  // saved, saving, dirty
    property string lastSavedText: ""
    
    // Computed properties
    readonly property var statusConfig: {
        "saved": {
            "text": "자동 저장됨",
            "icon": "✓",
            "bgColor": Colors.bgSecondary,
            "textColor": Colors.success,
            "dotColor": Colors.success
        },
        "saving": {
            "text": "저장 중...",
            "icon": "",
            "bgColor": Colors.primary100,
            "textColor": Colors.primary600,
            "dotColor": Colors.primary500
        },
        "dirty": {
            "text": "변경 사항 있음",
            "icon": "",
            "bgColor": Colors.accentRoseLight,
            "textColor": Colors.accentRose,
            "dotColor": Colors.accentRose
        }
    }
    
    width: row.width + 16
    height: 28
    radius: Metrics.radiusFull
    color: {
        if (!status || !statusConfig[status]) return Colors.bgTertiary
        return statusConfig[status].bgColor
    }
    
    // Animation for status change
    Behavior on color {
        ColorAnimation { duration: Metrics.durationFast }
    }
    
    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 6
        
        // Status dot
        Rectangle {
            width: 6
            height: 6
            radius: 3
            color: {
                if (!status || !statusConfig[status]) return Colors.textTertiary
                return statusConfig[status].dotColor
            }
            
            // Pulse animation for saving state
            SequentialAnimation on scale {
                running: root.status === "saving"
                loops: Animation.Infinite
                NumberAnimation { from: 1; to: 1.3; duration: 400 }
                NumberAnimation { from: 1.3; to: 1; duration: 400 }
            }
            
            Behavior on scale {
                NumberAnimation { duration: Metrics.durationFast }
            }
        }
        
        // Status text
        Text {
            text: {
                if (!status || !statusConfig[status]) return ""
                return statusConfig[status].text
            }
            font.family: Typography.fontPrimary
            font.weight: Typography.weightMedium
            font.pixelSize: Typography.caption
            color: {
                if (!status || !statusConfig[status]) return Colors.textTertiary
                return statusConfig[status].textColor
            }
        }
        
        // Last saved time (only when saved)
        Text {
            visible: root.status === "saved" && root.lastSavedText !== ""
            text: "· " + root.lastSavedText
            font.family: Typography.fontPrimary
            font.weight: Typography.weightRegular
            font.pixelSize: Typography.caption
            color: Colors.textTertiary
        }
    }
}
