import { useState } from 'react'
import {
  Bold, Italic, Underline, Strikethrough, Code, Link2,
  Heading1, Heading2, Heading3,
  List, ListOrdered, ListChecks, Quote, Minus,
  ImageIcon, TableIcon, Undo2, Redo2,
  AlignLeft, AlignCenter, AlignRight,
  Highlighter, X, Save,
} from 'lucide-react'

function Btn({ onClick, active, title, disabled, children }) {
  return (
    <button
      onMouseDown={(e) => { e.preventDefault(); onClick?.() }}
      disabled={disabled}
      title={title}
      className={[
        'p-1.5 rounded transition-colors select-none',
        active
          ? 'bg-primary-100 text-primary-600'
          : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800',
        disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer',
      ].join(' ')}
    >
      {children}
    </button>
  )
}

function Sep() {
  return <div className="w-px h-5 bg-slate-200 mx-1 shrink-0" />
}

export default function Toolbar({ editor }) {
  if (!editor) return null

  const [showLinkModal, setShowLinkModal] = useState(false)
  const [linkUrl, setLinkUrl] = useState('')
  const [showImageModal, setShowImageModal] = useState(false)
  const [imageUrl, setImageUrl] = useState('')

  const handleLink = () => {
    const prev = editor.getAttributes('link').href || ''
    setLinkUrl(prev)
    setShowLinkModal(true)
  }

  const applyLink = () => {
    if (linkUrl.trim()) {
      editor.chain().focus().setLink({ href: linkUrl.trim(), target: '_blank' }).run()
    } else {
      editor.chain().focus().unsetLink().run()
    }
    setShowLinkModal(false)
  }

  const handleImage = () => {
    setImageUrl('')
    setShowImageModal(true)
  }

  const applyImage = () => {
    if (imageUrl.trim()) {
      editor.chain().focus().setImage({ src: imageUrl.trim() }).run()
    }
    setShowImageModal(false)
  }

  const handleTable = () => {
    editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
  }

  return (
    <div className="flex items-center flex-wrap gap-0.5 px-3 py-2 bg-white">
      {/* History */}
      <Btn onClick={() => editor.chain().focus().undo().run()} title="실행 취소 (Ctrl+Z)" disabled={!editor.can().undo()}>
        <Undo2 size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().redo().run()} title="다시 실행 (Ctrl+Y)" disabled={!editor.can().redo()}>
        <Redo2 size={16} />
      </Btn>

      <Sep />

      {/* Headings */}
      <Btn onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()} active={editor.isActive('heading', { level: 1 })} title="제목 1">
        <Heading1 size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} active={editor.isActive('heading', { level: 2 })} title="제목 2">
        <Heading2 size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()} active={editor.isActive('heading', { level: 3 })} title="제목 3">
        <Heading3 size={16} />
      </Btn>

      <Sep />

      {/* Inline formatting */}
      <Btn onClick={() => editor.chain().focus().toggleBold().run()} active={editor.isActive('bold')} title="굵게 (Ctrl+B)">
        <Bold size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().toggleItalic().run()} active={editor.isActive('italic')} title="기울임 (Ctrl+I)">
        <Italic size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().toggleUnderline().run()} active={editor.isActive('underline')} title="밑줄 (Ctrl+U)">
        <Underline size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().toggleStrike().run()} active={editor.isActive('strike')} title="취소선">
        <Strikethrough size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().toggleCode().run()} active={editor.isActive('code')} title="인라인 코드">
        <Code size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().toggleHighlight().run()} active={editor.isActive('highlight')} title="형광펜">
        <Highlighter size={16} />
      </Btn>
      <Btn onClick={handleLink} active={editor.isActive('link')} title="링크 삽입">
        <Link2 size={16} />
      </Btn>

      <Sep />

      {/* Alignment */}
      <Btn onClick={() => editor.chain().focus().setTextAlign('left').run()} active={editor.isActive({ textAlign: 'left' })} title="왼쪽 정렬">
        <AlignLeft size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().setTextAlign('center').run()} active={editor.isActive({ textAlign: 'center' })} title="가운데 정렬">
        <AlignCenter size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().setTextAlign('right').run()} active={editor.isActive({ textAlign: 'right' })} title="오른쪽 정렬">
        <AlignRight size={16} />
      </Btn>

      <Sep />

      {/* Lists */}
      <Btn onClick={() => editor.chain().focus().toggleBulletList().run()} active={editor.isActive('bulletList')} title="글머리 기호">
        <List size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().toggleOrderedList().run()} active={editor.isActive('orderedList')} title="번호 목록">
        <ListOrdered size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().toggleTaskList().run()} active={editor.isActive('taskList')} title="체크리스트">
        <ListChecks size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().toggleBlockquote().run()} active={editor.isActive('blockquote')} title="인용">
        <Quote size={16} />
      </Btn>
      <Btn onClick={() => editor.chain().focus().setHorizontalRule().run()} title="수평선">
        <Minus size={16} />
      </Btn>

      <Sep />

      {/* Insert */}
      <Btn onClick={handleImage} title="이미지 삽입 (URL)">
        <ImageIcon size={16} />
      </Btn>
      <Btn onClick={handleTable} title="표 삽입">
        <TableIcon size={16} />
      </Btn>

      <Sep />

      {/* Save Now — triggers immediate save via QML bridge */}
      <Btn
        onClick={() => {
          if (window.editorAPI && window.editorAPI.flushNow) {
            window.editorAPI.flushNow()
          }
        }}
        title="지금 저장 (Ctrl+S)"
      >
        <Save size={16} />
      </Btn>

      {/* Link Modal */}
      {showLinkModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={() => setShowLinkModal(false)}>
          <div className="bg-white rounded-lg shadow-xl p-4 w-80" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <span className="font-medium text-slate-700">링크 삽입</span>
              <button onClick={() => setShowLinkModal(false)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>
            <input
              type="text"
              value={linkUrl}
              onChange={e => setLinkUrl(e.target.value)}
              placeholder="https://..."
              className="w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              onKeyDown={e => { if (e.key === 'Enter') applyLink() }}
              autoFocus
            />
            <div className="flex justify-end gap-2 mt-3">
              <button onClick={() => setShowLinkModal(false)} className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded">취소</button>
              <button onClick={applyLink} className="px-3 py-1.5 text-sm bg-primary-600 text-white hover:bg-primary-700 rounded">확인</button>
            </div>
          </div>
        </div>
      )}

      {/* Image Modal */}
      {showImageModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={() => setShowImageModal(false)}>
          <div className="bg-white rounded-lg shadow-xl p-4 w-80" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <span className="font-medium text-slate-700">이미지 삽입</span>
              <button onClick={() => setShowImageModal(false)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>
            <input
              type="text"
              value={imageUrl}
              onChange={e => setImageUrl(e.target.value)}
              placeholder="https://... 또는 data:image/..."
              className="w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              onKeyDown={e => { if (e.key === 'Enter') applyImage() }}
              autoFocus
            />
            <div className="flex justify-end gap-2 mt-3">
              <button onClick={() => setShowImageModal(false)} className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded">취소</button>
              <button onClick={applyImage} className="px-3 py-1.5 text-sm bg-primary-600 text-white hover:bg-primary-700 rounded">확인</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
