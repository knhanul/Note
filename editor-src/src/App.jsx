import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import Highlight from '@tiptap/extension-highlight'
import { TextStyle } from '@tiptap/extension-text-style'
import { Color } from '@tiptap/extension-color'
import Link from '@tiptap/extension-link'
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableHeader from '@tiptap/extension-table-header'
import TableCell from '@tiptap/extension-table-cell'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import { Markdown } from 'tiptap-markdown'
import { useEffect, useRef, useCallback } from 'react'

import Toolbar from './components/Toolbar'
import BubbleMenuBar from './components/BubbleMenuBar'
import TableToolbar from './components/TableToolbar'
import { ResizableImage } from './extensions/ResizableImage'
import { ImagePaste } from './extensions/ImagePaste'

export default function App() {
  const debounceRef = useRef(null)

  const editor = useEditor({
    extensions: [
      StarterKit.configure({ heading: { levels: [1, 2, 3] } }),
      Underline,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Highlight,
      TextStyle,
      Color,
      Link.configure({ openOnClick: false, autolink: true }),
      ResizableImage.configure({ inline: true, allowBase64: true }),
      ImagePaste,
      Table.configure({ resizable: true }),
      TableRow,
      TableHeader,
      TableCell,
      TaskList,
      TaskItem.configure({ nested: true }),
      Markdown.configure({ html: true, transformPastedText: true }),
    ],
    content: '',
    editorProps: {
      attributes: {
        class: 'prose max-w-none p-6 min-h-full focus:outline-none',
        'data-placeholder': '내용을 입력하세요...',
      },
    },
    onUpdate: ({ editor }) => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      debounceRef.current = setTimeout(() => notifyChanged(editor), 600)
    },
  })

  // ─── Bridge helpers ────────────────────────────────────────────
  const notifyChanged = useCallback((ed) => {
    try {
      const json  = JSON.stringify(ed.getJSON())
      const text  = ed.getText()
      const title = (text.split('\n').find(l => l.trim()) || '').substring(0, 100)

      let markdown = ''
      try {
        markdown = ed.storage.markdown.getMarkdown()
      } catch (_) {
        markdown = text
      }

      // Store full data in window so QML can retrieve it without size limits
      window.__editorLastPayload = { markdown, json, title }

      // Notify QML via console (only sends a small signal, not the full data)
      console.log('EDITOR_CONTENT_CHANGED:__PAYLOAD_READY__')
    } catch (_) {}
  }, [])

  // ─── window.editorAPI (PyQt bridge) ────────────────────────────
  useEffect(() => {
    if (!editor) return

    window.editorAPI = {
      /**
       * Load content — JSON-first, Markdown fallback.
       * Called by QML: editorAPI.setContent(markdown, jsonStr)
       */
      setContent(markdown, jsonStr) {
        if (debounceRef.current) { clearTimeout(debounceRef.current); debounceRef.current = null }
        try {
          if (jsonStr && jsonStr.trim() !== '') {
            const json = typeof jsonStr === 'string' ? JSON.parse(jsonStr) : jsonStr
            editor.commands.setContent(json, false)
            return
          }
        } catch (_) { /* fallthrough */ }
        editor.commands.setContent(markdown || '', false)
      },

      /** Backward-compatible alias */
      setMarkdown(markdown) {
        editor.commands.setContent(markdown || '', false)
      },

      getMarkdown() {
        return editor.storage.markdown.getMarkdown()
      },

      getJSON() {
        return JSON.stringify(editor.getJSON())
      },

      /** Insert a local-image URL / data URL at cursor */
      insertImage(src) {
        editor.chain().focus().setImage({ src }).run()
      },

      insertMarkdownAtCursor(markdown) {
        editor.chain().focus().insertContent(markdown).run()
      },

      onContentChanged() {
        notifyChanged(editor)
      },

      focus() {
        editor.commands.focus()
      },

      // Format helpers (kept for QML toolbar compatibility)
      formatBold:    () => editor.chain().focus().toggleBold().run(),
      formatItalic:  () => editor.chain().focus().toggleItalic().run(),
      formatHeading: () => editor.chain().focus().toggleHeading({ level: 1 }).run(),
      formatCode:    () => editor.chain().focus().toggleCode().run(),
      insertTable:   () => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run(),
      insertBulletList:   () => editor.chain().focus().toggleBulletList().run(),
      insertNumberedList: () => editor.chain().focus().toggleOrderedList().run(),
      insertHorizontalRule: () => editor.chain().focus().setHorizontalRule().run(),
      insertQuote:   () => editor.chain().focus().toggleBlockquote().run(),
      insertLink() {
        // Handled internally by Toolbar component (React modal)
      },
    }

    // ── PyWebView example bridge (future use) ────────────────────
    // window.pywebview?.api?.onEditorReady?.()
  }, [editor, notifyChanged])

  return (
    <div className="flex flex-col bg-white text-slate-900 font-sans" style={{ height: '100vh' }}>
      {/* Toolbar area: both toolbars in one stable container */}
      <div className="flex-none border-b border-slate-200">
        <Toolbar editor={editor} />
        <TableToolbar editor={editor} />
      </div>
      <BubbleMenuBar editor={editor} />
      <div className="flex-1 overflow-auto min-h-0">
        <EditorContent editor={editor} className="h-full" />
      </div>
    </div>
  )
}
