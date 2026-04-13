pragma Singleton
import QtQuick

QtObject {
    // Font families
    property string fontPrimary: "Inter"
    property string fontMono:    "JetBrains Mono"

    // Font weights
    property int weightRegular: 400
    property int weightMedium:  500
    property int weightSemibold: 600
    property int weightBold:    700

    // Header sizes
    property int h1: 28
    property int h2: 24
    property int h3: 20
    property int h4: 18
    property int h5: 16
    property int h6: 14

    // Body sizes
    property int bodyLarge:   16
    property int bodyRegular: 14
    property int bodySmall:   13
    property int caption:     12

    // Line heights
    property real lineHeightTight:  1.25
    property real lineHeightNormal: 1.5
    property real lineHeightRelaxed: 1.75

    // Letter spacing
    property real letterSpacingTight: -0.02
    property real letterSpacingNormal: 0
    property real letterSpacingWide: 0.02
}
