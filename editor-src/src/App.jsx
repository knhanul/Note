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

/* ============================================================================
 * WebNoteEditor (App.jsx) — 타이핑 무중단 · 포커스 안정 · 이벤트 기반 자동저장
 * ----------------------------------------------------------------------------
 * 설계 원칙 (절대 깨지면 안 되는 규칙)
 *   R1. 타이핑 시 절대 리렌더되면 안 된다.
 *       → 본문 텍스트는 Tiptap 내부 ProseMirror 상태에만 존재.
 *       → React state(useState)로 본문을 복사/관리하지 않는다.
 *   R2. 동일 noteId에서는 절대 setContent를 재호출하지 않는다.
 *       → 저장 후 상태 시그널이 돌아와도 에디터 DOM을 건드리지 않는다.
 *       → setContent는 오직 "다른 노트로 전환"될 때 단 한 번만 실행된다.
 *   R3. Enter 키 자체에는 저장을 매달지 않는다.
 *       → 평문 Enter = 단순 줄바꿈. 저장은 debounce 1.5s 또는 blur가 전담.
 *       → 예외: 새 노트(isNewNote)의 "첫 Enter"만 CREATE 트리거로 사용.
 *   R4. 모든 실시간 값(타이머, 에디터, 노트ID, 새노트플래그)은 useRef로만 관리.
 *       → 한 줄 입력마다 리렌더 0회가 목표.
 * ========================================================================= */

const SAVE_DEBOUNCE_MS = 1500

/**
 * 본문에서 제목으로 쓸 첫 줄을 안전하게 추출한다.
 * - 공백/빈 줄 무시
 * - 마크다운 헤더 기호(#, ##, ###) 및 강조 기호 제거
 * - 최대 100자로 잘라 너무 긴 제목 방지
 */
function extractFirstLineTitle(text) {
  if (!text) return ''
  const firstMeaningful = text
    .split(/\r?\n/)
    .map(l => l.trim())
    .find(l => l.length > 0) || ''

  return firstMeaningful
    .replace(/^#{1,6}\s*/, '')       // # 헤더 제거
    .replace(/^\*+\s*/, '')          // * 리스트 제거
    .replace(/^[-+]\s*/, '')         // - + 리스트 제거
    .replace(/[*_`~]/g, '')          // 강조 기호 제거
    .trim()
    .substring(0, 100)
}

export default function App() {
  // ── Refs: 모두 리렌더 유발 없이 값만 추적 ─────────────────────────
  const editorRef = useRef(null)           // Tiptap 에디터 인스턴스
  const debounceTimerRef = useRef(null)    // 1.5s 자동저장 타이머
  const currentNoteIdRef = useRef('')      // 현재 편집 중인 noteId (R2 판단용)
  const isNewNoteRef = useRef(false)       // 새 노트 여부 (첫 Enter CREATE 트리거용)
  const hasTypedRef = useRef(false)        // 새 노트에 실제 입력이 발생했는지

  // ── 타이머 유틸 ──────────────────────────────────────────────────
  const clearDebounce = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
      debounceTimerRef.current = null
    }
  }, [])

  /**
   * 에디터에서 최신 payload를 추출한다.
   * 저장 직전에 반드시 호출하여 debounce 중 쌓인 stale 스냅샷 문제를 회피한다.
   */
  const buildPayload = useCallback((ed) => {
    const json = JSON.stringify(ed.getJSON())
    const text = ed.getText()
    const title = extractFirstLineTitle(text)

    let markdown = ''
    try {
      markdown = ed.storage.markdown.getMarkdown()
    } catch (_) {
      markdown = text
    }

    return { markdown, json, title, text }
  }, [])

  /**
   * QML 브릿지로 payload를 내보낸다.
   * QML은 window.__editorLastPayload를 읽어 DB 저장에 사용한다.
   */
  const publishPayload = useCallback((ed) => {
    const payload = buildPayload(ed)
    window.__editorLastPayload = payload
    return payload
  }, [buildPayload])

  /**
   * 실제 저장 요청을 QML로 보낸다.
   * - 새 노트 + 최초 Enter → REQUEST_CREATE_NOTE (DB INSERT)
   * - 기존 노트 → REQUEST_SAVE (DB UPDATE)
   * 반드시 publish 후 호출해서 payload를 최신 상태로 맞춘다.
   */
  const flushSave = useCallback((ed, { create = false } = {}) => {
    if (!ed) return
    clearDebounce()
    publishPayload(ed)

    if (create) {
      console.log('REQUEST_CREATE_NOTE')
    } else {
      console.log('REQUEST_SAVE')
    }
  }, [clearDebounce, publishPayload])

  /**
   * 타이핑 중 호출되는 debounce 스케줄러.
   * 1.5초간 추가 입력이 없으면 조용히 백그라운드 저장.
   */
  const scheduleDebouncedSave = useCallback((ed) => {
    clearDebounce()
    debounceTimerRef.current = setTimeout(() => {
      debounceTimerRef.current = null
      // 새 노트인데 아직 CREATE 안 된 상태에서 debounce가 돌면
      // 사용자가 Enter 없이 blur했거나 자리를 떠난 상황.
      // → 1.5초 이상 타이핑 후 멈췄다면 CREATE로 승격.
      if (isNewNoteRef.current && hasTypedRef.current) {
        flushSave(ed, { create: true })
      } else {
        flushSave(ed, { create: false })
      }
    }, SAVE_DEBOUNCE_MS)
  }, [clearDebounce, flushSave])

  // ── Tiptap 에디터 초기화 ─────────────────────────────────────────
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
      /**
       * R3 구현 지점.
       * 평문 Enter는 에디터에 그대로 맡기고(return false) 커서 이동/줄바꿈이
       * ProseMirror에서 자연스럽게 일어나게 한다.
       * 단, "새 노트의 첫 Enter"만 CREATE 트리거로 활용한다.
       *  - IME 조합 중(Enter가 한글 확정용)일 때는 절대 개입하지 않는다.
       *  - Shift+Enter는 soft break이므로 무시.
       *  - setTimeout(0)으로 Tiptap이 줄바꿈을 먼저 반영한 뒤 payload를 뽑아
       *    "첫 줄이 잘리는" 레이스 컨디션을 원천 차단한다.
       */
      handleKeyDown(view, event) {
        // Ctrl+S (or Cmd+S) — immediate save, bypass debounce
        if ((event.ctrlKey || event.metaKey) && event.key === 's') {
          event.preventDefault()
          const ed = editorRef.current
          if (!ed) return true
          if (isNewNoteRef.current && hasTypedRef.current) {
            flushSave(ed, { create: true })
          } else if (!isNewNoteRef.current) {
            flushSave(ed, { create: false })
          }
          return true
        }

        if (event.key !== 'Enter' || event.shiftKey) return false
        if (event.isComposing || event.keyCode === 229) return false

        if (isNewNoteRef.current && hasTypedRef.current) {
          const ed = editorRef.current
          setTimeout(() => {
            if (!ed) return
            // CREATE 성공 후 QML이 setContent(noteId 변경)로 상태를 넘겨주면
            // isNewNoteRef는 setContent 경로에서 false로 전환된다.
            flushSave(ed, { create: true })
          }, 0)
        }
        // 중요: false 반환 → Tiptap 기본 Enter 동작(줄바꿈) 그대로 수행
        return false
      },
      handleDOMEvents: {
        /**
         * blur(포커스 상실) 시 즉시 flush.
         * debounce가 남아있어도 무시하고 지금 바로 최신 payload로 저장한다.
         */
        blur() {
          const ed = editorRef.current
          if (!ed) return false
          if (isNewNoteRef.current && hasTypedRef.current) {
            flushSave(ed, { create: true })
          } else if (!isNewNoteRef.current) {
            flushSave(ed, { create: false })
          }
          return false
        },
      },
    },
    /**
     * 타이핑마다 호출되지만 React state를 만지지 않으므로 리렌더 없음(R1).
     * 역할은 두 가지뿐이다: payload 최신화 + debounce 예약.
     */
    onUpdate: ({ editor: ed }) => {
      if (isNewNoteRef.current) hasTypedRef.current = true
      publishPayload(ed)
      scheduleDebouncedSave(ed)
    },
  })

  // ── 에디터 인스턴스 참조 고정 ────────────────────────────────────
  useEffect(() => {
    editorRef.current = editor || null
  }, [editor])

  // ── 언마운트 시 타이머 청소 ──────────────────────────────────────
  useEffect(() => {
    return () => clearDebounce()
  }, [clearDebounce])

  // ── QML 브릿지 (window.editorAPI) ───────────────────────────────
  useEffect(() => {
    if (!editor) return

    window.editorAPI = {
      /**
       * 노트 로드. QML이 노트 전환/초기화 시점에만 호출해야 한다.
       * 호출 시그니처: setContent(markdown, jsonStr, noteId, isNewNote)
       *
       * R2 핵심 구현:
       *   - 동일 noteId가 다시 들어오면 무시 (포커스 보존).
       *   - 새 노트 요청(isNewNote=true)은 빈 문서 + 플래그 ON으로 초기화.
       */
      setContent(markdown, jsonStr, noteId, isNewNote) {
        const incomingNoteId = noteId || ''
        const isNew = !!isNewNote

        // R2: 같은 노트면 절대 setContent 금지 → 커서/포커스/히스토리 보존
        if (incomingNoteId && incomingNoteId === currentNoteIdRef.current && !isNew) {
          return
        }

        clearDebounce()
        currentNoteIdRef.current = incomingNoteId
        isNewNoteRef.current = isNew
        hasTypedRef.current = false

        // 새 노트: 항상 빈 문서로 시작
        if (isNew) {
          editor.commands.setContent('', false)
          publishPayload(editor)
          // 새 노트 열자마자 포커스를 줘서 사용자가 바로 입력 가능하게
          requestAnimationFrame(() => editor.commands.focus('end'))
          return
        }

        // 기존 노트: JSON 우선, 실패 시 Markdown fallback
        try {
          if (jsonStr && jsonStr.trim() !== '') {
            const json = typeof jsonStr === 'string' ? JSON.parse(jsonStr) : jsonStr
            editor.commands.setContent(json, false)
            publishPayload(editor)
            return
          }
        } catch (_) { /* fallthrough */ }

        editor.commands.setContent(markdown || '', false)
        publishPayload(editor)
      },

      /**
       * QML이 CREATE 완료 후 호출. 현재 편집 세션을 "기존 노트"로 승격시킨다.
       * setContent를 호출하지 않으므로 에디터 DOM/포커스는 그대로 유지된다 (R2).
       */
      promoteToSaved(noteId) {
        if (!noteId) return
        currentNoteIdRef.current = noteId
        isNewNoteRef.current = false
        hasTypedRef.current = false
      },

      /** 하위 호환 */
      setMarkdown(markdown) {
        editor.commands.setContent(markdown || '', false)
        publishPayload(editor)
      },

      getMarkdown() { return editor.storage.markdown.getMarkdown() },
      getJSON()     { return JSON.stringify(editor.getJSON()) },
      getTitle()    { return extractFirstLineTitle(editor.getText()) },
      getPayload()  { return buildPayload(editor) },

      insertImage(src)                 { editor.chain().focus().setImage({ src }).run() },
      insertMarkdownAtCursor(markdown) { editor.chain().focus().insertContent(markdown).run() },
      focus()                          { editor.commands.focus() },

      /** QML에서 강제 flush가 필요할 때 (예: 앱 종료, 노트 전환 직전) */
      flushNow() {
        const ed = editorRef.current
        if (!ed) return
        if (isNewNoteRef.current && hasTypedRef.current) {
          flushSave(ed, { create: true })
        } else if (!isNewNoteRef.current) {
          flushSave(ed, { create: false })
        }
      },

      // Toolbar 호환 헬퍼
      formatBold:         () => editor.chain().focus().toggleBold().run(),
      formatItalic:       () => editor.chain().focus().toggleItalic().run(),
      formatHeading:      () => editor.chain().focus().toggleHeading({ level: 1 }).run(),
      formatCode:         () => editor.chain().focus().toggleCode().run(),
      insertTable:        () => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run(),
      insertBulletList:   () => editor.chain().focus().toggleBulletList().run(),
      insertNumberedList: () => editor.chain().focus().toggleOrderedList().run(),
      insertHorizontalRule: () => editor.chain().focus().setHorizontalRule().run(),
      insertQuote:        () => editor.chain().focus().toggleBlockquote().run(),
      insertLink() { /* React modal에서 처리 */ },
    }

    // QML이 첫 진입 시 읽을 수 있도록 초기 payload 한 번 발행
    publishPayload(editor)
  }, [editor, clearDebounce, publishPayload, flushSave, buildPayload])

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
