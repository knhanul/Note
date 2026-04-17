import { BubbleMenu } from '@tiptap/react'
import { Bold, Italic, Underline, Strikethrough, Code, Link2, Highlighter } from 'lucide-react'

function BBtn({ onClick, active, title, children }) {
  return (
    <button
      onMouseDown={(e) => { e.preventDefault(); onClick?.() }}
      title={title}
      className={[
        'p-1.5 rounded transition-colors select-none',
        active
          ? 'bg-primary-100 text-primary-600'
          : 'text-slate-600 hover:bg-slate-100',
      ].join(' ')}
    >
      {children}
    </button>
  )
}

export default function BubbleMenuBar({ editor }) {
  if (!editor) return null

  const handleLink = () => {
    const prev = editor.getAttributes('link').href || ''
    const url = window.prompt('링크 URL:', prev)
    if (url === null) return
    if (url === '') editor.chain().focus().unsetLink().run()
    else editor.chain().focus().setLink({ href: url, target: '_blank' }).run()
  }

  return (
    <BubbleMenu
      editor={editor}
      tippyOptions={{ duration: 150, placement: 'top' }}
      className="flex items-center gap-0.5 bg-white border border-slate-200 rounded-lg shadow-lg px-1.5 py-1"
    >
      <BBtn onClick={() => editor.chain().focus().toggleBold().run()}      active={editor.isActive('bold')}      title="굵게"><Bold        size={14} /></BBtn>
      <BBtn onClick={() => editor.chain().focus().toggleItalic().run()}    active={editor.isActive('italic')}    title="기울임"><Italic      size={14} /></BBtn>
      <BBtn onClick={() => editor.chain().focus().toggleUnderline().run()} active={editor.isActive('underline')} title="밑줄"><Underline   size={14} /></BBtn>
      <BBtn onClick={() => editor.chain().focus().toggleStrike().run()}    active={editor.isActive('strike')}    title="취소선"><Strikethrough size={14} /></BBtn>
      <BBtn onClick={() => editor.chain().focus().toggleCode().run()}      active={editor.isActive('code')}      title="코드"><Code         size={14} /></BBtn>
      <BBtn onClick={() => editor.chain().focus().toggleHighlight().run()} active={editor.isActive('highlight')} title="형광펜"><Highlighter  size={14} /></BBtn>
      <div className="w-px h-4 bg-slate-200 mx-0.5" />
      <BBtn onClick={handleLink} active={editor.isActive('link')} title="링크"><Link2 size={14} /></BBtn>
    </BubbleMenu>
  )
}
