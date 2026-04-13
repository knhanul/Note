# Nuni Note

A premium desktop note-taking application built with PyQt6/QML.

## Design Philosophy

> **"Notion + iOS + Financial App"**

- **Trust**: Blue palette inspired by financial apps
- **Aesthetics**: iOS-level softness and refinement
- **Productivity**: Clear information architecture

## Features

- Glass morphism UI with blur effects
- Smooth hover/press animations
- iOS-inspired rounded corners (24px+)
- Soft, subtle shadows
- Three-pane layout (Sidebar → Note List → Editor)
- Blue gradient selection states
- Pill-style editor toolbar

## Screenshot

The UI features:
- Premium glass cards with backdrop blur
- Animated hover states with elevation
- Selected note items with blue gradient
- Soft, diffused shadows
- Generous whitespace and 24px+ corner radius

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Project Structure

```
.
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── qml/
│   ├── Main.qml         # Root window
│   ├── components/      # Reusable UI components
│   │   ├── GlassCard.qml
│   │   ├── AppHeader.qml
│   │   ├── SidebarSection.qml
│   │   ├── NotebookItem.qml
│   │   ├── NoteListItem.qml
│   │   ├── EditorToolbar.qml
│   │   └── TagChip.qml
│   └── theme/           # Design system
│       ├── Colors.qml
│       ├── Typography.qml
│       └── Metrics.qml
└── assets/              # Images and resources
```

## Design System

### Colors
- **Primary**: Blue family (#3B82F6, #2563EB) - Trust
- **Accent**: Orange/Rose (#F97316, #FB7185) - Highlights only
- **Background**: Cool grays (#FAFBFC, #F1F5F9)
- **Surface**: Semi-transparent white (70-90% opacity)

### Typography
- **Font**: Inter (system fallback: Segoe UI → Helvetica → Arial)
- **Weights**: 400 Regular, 500 Medium, 600 Semibold, 700 Bold
- **Sizes**: 12-28px scale

### Spacing & Radius
- **Spacing**: 4, 8, 12, 16, 24, 32, 48px scale
- **Radius**: Minimum 16px, major cards 24-30px
- **Shadows**: Low opacity (5-10%), high blur (8-24px)

### Animation
- **Duration**: 120-180ms for interactions
- **Easing**: Bezier curves for natural motion
- **Effects**: Scale on press, Y-translate on hover

## Requirements

- Python 3.10+
- PyQt6 6.5+
- Qt 6.5+ (included with PyQt6)

## License

MIT License - See LICENSE file for details.

---

Built with precision for desktop productivity.
