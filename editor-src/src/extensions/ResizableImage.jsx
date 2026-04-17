import { Image } from '@tiptap/extension-image'
import { ReactNodeViewRenderer, NodeViewWrapper } from '@tiptap/react'
import { useRef, useCallback } from 'react'

function ResizableImageView({ node, updateAttributes, selected }) {
  const { src, alt, width, height } = node.attrs
  const imgRef = useRef(null)

  const onResizeStart = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()

    const startX = e.clientX
    const startW = imgRef.current.offsetWidth
    const startH = imgRef.current.offsetHeight
    const aspect = startW / (startH || 1)

    const onMove = (mv) => {
      const newW = Math.max(40, startW + (mv.clientX - startX))
      const newH = Math.round(newW / aspect)
      imgRef.current.style.width  = newW + 'px'
      imgRef.current.style.height = newH + 'px'
    }

    const onUp = () => {
      const finalW = imgRef.current.offsetWidth
      const finalH = imgRef.current.offsetHeight
      updateAttributes({ width: finalW, height: finalH })
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }

    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }, [updateAttributes])

  return (
    <NodeViewWrapper
      as="span"
      data-drag-handle
      style={{ display: 'inline-block', lineHeight: 0, margin: '8px 0' }}
    >
      <div className="image-resizer" style={{ display: 'inline-block', position: 'relative' }}>
        <img
          ref={imgRef}
          src={src}
          alt={alt || ''}
          draggable={false}
          style={{
            width:   width  ? `${width}px`  : 'auto',
            height:  height ? `${height}px` : 'auto',
            maxWidth: '100%',
            display: 'block',
            borderRadius: '6px',
            outline: selected ? '2px solid #3b82f6' : 'none',
            outlineOffset: '2px',
          }}
        />
        {selected && (
          <div className="resize-trigger" onMouseDown={onResizeStart} />
        )}
      </div>
    </NodeViewWrapper>
  )
}

export const ResizableImage = Image.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      width: {
        default: null,
        parseHTML: (el) =>
          parseInt(el.getAttribute('width') || el.style.width) || null,
        renderHTML: (attrs) =>
          attrs.width ? { width: attrs.width, style: `width:${attrs.width}px` } : {},
      },
      height: {
        default: null,
        parseHTML: (el) =>
          parseInt(el.getAttribute('height') || el.style.height) || null,
        renderHTML: (attrs) =>
          attrs.height ? { height: attrs.height } : {},
      },
    }
  },

  addNodeView() {
    return ReactNodeViewRenderer(ResizableImageView)
  },
})
