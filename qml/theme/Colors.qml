pragma Singleton
import QtQuick

QtObject {
    // Primary - Trust (Blue family only)
    property color primary50:  "#EFF6FF"
    property color primary100: "#DBEAFE"
    property color primary200: "#BFDBFE"
    property color primary300: "#93C5FD"
    property color primary400: "#60A5FA"
    property color primary500: "#3B82F6"
    property color primary600: "#2563EB"
    property color primary700: "#1D4ED8"
    property color primary800: "#1E40AF"
    property color primary900: "#1E3A8A"

    // Accent - Orange/Rose (for emphasis only)
    property color accentOrange: "#F97316"
    property color accentOrangeLight: "#FDBA74"
    property color accentRose: "#FB7185"
    property color accentRoseLight: "#FDA4AF"

    // Background
    property color bgPrimary:   "#FAFBFC"
    property color bgSecondary: "#F1F5F9"
    property color bgTertiary:  "#E2E8F0"

    // Surface (Glass effect base)
    property color surface:          "#FFFFFF"
    property color surfaceHigh:      "#FFFFFF"
    property color surfaceMedium:    Qt.rgba(1, 1, 1, 0.85)
    property color surfaceLow:       Qt.rgba(1, 1, 1, 0.70)

    // Text
    property color textPrimary:   "#0F172A"
    property color textSecondary: "#475569"
    property color textTertiary:  "#94A3B8"
    property color textInverse:   "#FFFFFF"

    // Border
    property color borderLight:   Qt.rgba(226/255, 232/255, 240/255, 0.8)
    property color borderMedium: "#CBD5E1"

    // Status
    property color success: "#22C55E"
    property color warning: "#F59E0B"
    property color error:   "#EF4444"

    // Gradients
    property var primaryGradient: [primary500, primary600]
    property var selectedGradient: [primary400, primary500]
}
