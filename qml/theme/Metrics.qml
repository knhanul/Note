pragma Singleton
import QtQuick

QtObject {
    // Base unit
    property int base: 4

    // Spacing scale
    property int xs:   4
    property int sm:   8
    property int md:   12
    property int lg:   16
    property int xl:   24
    property int xxl:  32
    property int xxxl: 48

    // Corner radius (enforced minimum 16px)
    property int radiusSm:   8
    property int radiusMd:   12
    property int radiusLg:   16
    property int radiusXl:   20
    property int radiusXxl:  24
    property int radiusMax:  30
    property int radiusFull: 9999

    // Component sizes
    property int headerHeight: 56
    property int sidebarWidth: 260
    property int noteListWidth: 320
    property int toolbarHeight: 48

    // Card padding
    property int cardPadding: 20
    property int cardPaddingLg: 24

    // Shadows (elevation)
    property real shadowSmOpacity:   0.05
    property real shadowMdOpacity:   0.08
    property real shadowLgOpacity:   0.10
    property int shadowSmBlur:   8
    property int shadowMdBlur:   16
    property int shadowLgBlur:   24
    property int shadowSmY:      2
    property int shadowMdY:      4
    property int shadowLgY:      8

    // Animation durations
    property int durationFast:   120
    property int durationNormal: 180
    property int durationSlow:   250
    property int durationSlower: 350
}
