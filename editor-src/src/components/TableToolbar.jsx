export default function TableToolbar({ editor }) {
  if (!editor || !editor.isActive('table')) return null

  const btn = (label, action, danger = false) => (
    <button
      onMouseDown={(e) => { e.preventDefault(); action() }}
      className={[
        'px-2 py-1 text-xs rounded transition-colors select-none',
        danger
          ? 'text-red-600 hover:bg-red-50'
          : 'text-primary-700 hover:bg-primary-50',
      ].join(' ')}
    >
      {label}
    </button>
  )

  const sep = () => <div className="w-px h-4 bg-slate-200 mx-0.5 shrink-0" />

  return (
    <div className="flex items-center flex-wrap gap-0.5 px-3 py-1.5 bg-primary-50 border-b border-primary-100 text-sm">
      <span className="text-primary-600 font-semibold text-xs mr-1.5">표</span>

      {btn('열 앞 추가', () => editor.chain().focus().addColumnBefore().run())}
      {btn('열 뒤 추가', () => editor.chain().focus().addColumnAfter().run())}
      {btn('열 삭제',   () => editor.chain().focus().deleteColumn().run(), true)}

      {sep()}

      {btn('행 앞 추가', () => editor.chain().focus().addRowBefore().run())}
      {btn('행 뒤 추가', () => editor.chain().focus().addRowAfter().run())}
      {btn('행 삭제',   () => editor.chain().focus().deleteRow().run(), true)}

      {sep()}

      {btn('셀 병합', () => editor.chain().focus().mergeCells().run())}
      {btn('셀 분리', () => editor.chain().focus().splitCell().run())}
      {btn('헤더 전환', () => editor.chain().focus().toggleHeaderCell().run())}

      {sep()}

      {btn('표 삭제', () => editor.chain().focus().deleteTable().run(), true)}
    </div>
  )
}
