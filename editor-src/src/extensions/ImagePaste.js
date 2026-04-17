import { Extension } from '@tiptap/core'
import { Plugin } from '@tiptap/pm/state'

export const ImagePaste = Extension.create({
  name: 'imagePaste',

  addProseMirrorPlugins() {
    return [
      new Plugin({
        props: {
          handlePaste(view, event) {
            const items = event.clipboardData?.items
            if (!items) return false

            for (const item of Array.from(items)) {
              if (item.type.startsWith('image/')) {
                event.preventDefault()
                const file = item.getAsFile()
                const reader = new FileReader()
                reader.onload = (e) => {
                  const { schema, tr, selection } = view.state
                  const node = schema.nodes.image.create({ src: e.target.result })
                  view.dispatch(tr.replaceSelectionWith(node))
                }
                reader.readAsDataURL(file)
                return true
              }
            }
            return false
          },
        },
      }),
    ]
  },
})
