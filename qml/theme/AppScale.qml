pragma Singleton
import QtQuick

QtObject {
    property real factor: 1.0

    function setFactor(v: real) {
        factor = v
    }
}
