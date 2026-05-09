# Theme Contract

## Import style

QML files use:

```qml
import theme
```

The current QML import path is configured in `app_bootstrap.py` with:

```python
engine.addImportPath(str(config.qml_import_path))
```

`config.qml_import_path` points to the existing `qml/` directory. The `qml/theme/qmldir` module exposes the theme singleton files.

## Colors.qml

`Colors.qml` is a singleton `QtObject` containing color tokens:

- primary scale: `primary50` through `primary900`
- accents: `accentOrange`, `accentOrangeLight`, `accentRose`, `accentRoseLight`
- backgrounds: `bgPrimary`, `bgSecondary`, `bgTertiary`
- surfaces: `surface`, `surfaceHigh`, `surfaceMedium`, `surfaceLow`
- text: `textPrimary`, `textSecondary`, `textTertiary`, `textInverse`
- borders: `borderLight`, `borderMedium`
- status: `success`, `warning`, `error`
- gradients such as `primaryGradient`

Commonly referenced properties such as `Colors.bgPrimary`, `Colors.primary500`, `Colors.textPrimary`, and `Colors.borderLight` should be treated as stable API.

## Metrics.qml

`Metrics.qml` is a singleton `QtObject` containing UI sizing tokens:

- spacing: `xs`, `sm`, `md`, `lg`, `xl`, `xxl`, `xxxl`
- radius: `radiusSm`, `radiusMd`, `radiusLg`, `radiusXl`, `radiusXxl`, `radiusMax`, `radiusFull`
- component sizes: header/sidebar/item/button dimensions
- shadow tokens
- animation durations: `durationFast`, `durationNormal`, `durationSlow`, `durationSlower`

Changing these values changes the entire UI layout density and animation feel.

## Typography.qml

`Typography.qml` is a singleton `QtObject` containing text tokens:

- font families: `fontPrimary`, `fontMono`
- weights: `weightRegular`, `weightMedium`, `weightSemibold`, `weightBold`
- font sizes
- line heights
- letter spacing

Components commonly bind `font.family`, `font.pixelSize`, and `font.weight` to this singleton.

## Future app-specific overrides

A future app can override theme values by introducing an app-level theme module, but only after compatibility import paths are planned. Until then, keep `import theme` stable and avoid renaming tokens.

## Risk points

- Moving `qml/theme` without preserving `import theme` will break all components.
- Renaming singleton files or qmldir entries can break runtime loading.
- Removing commonly used properties such as `Colors.primary500`, `Metrics.radiusFull`, or `Typography.fontPrimary` will break many QML bindings.
- Theme values are used across `Main.qml` and component files, so visual regressions can be broad.
