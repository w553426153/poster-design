<template>
  <div
    :id="`${params.uuid}`"
    ref="widget"
    v-loading="state.loading"
    :class="['w-text', { editing: state.editable, 'layer-lock': params.lock }, params.uuid]"
    :style="{
      position: 'absolute',
      left: params.left - parent.left + 'px',
      top: params.top - parent.top + 'px',
      width: params.width + 'px',
      minWidth: params.fontSize + 'px',
      minHeight: params.fontSize * params.lineHeight + 'px',
      height: params.height + 'px',
      lineHeight: params.fontSize * params.lineHeight + 'px',
      letterSpacing: (params.fontSize * params.letterSpacing) / 100 + 'px',
      fontSize: params.fontSize + 'px',
      color: params.color,
      textAlign: params.textAlign,
      textAlignLast: params.textAlignLast,
      fontWeight: params.fontWeight,
      fontStyle: params.fontStyle,
      textDecoration: params.textDecoration,
      opacity: params.opacity,
      backgroundColor: params.backgroundColor,
      writingMode: params.writingMode,
      fontFamily: `'${params.fontClass.value}'`,
    }"
    @dblclick="(e) => dblclickText(e)"
  >
    <template v-if="params.textEffects && !state.editable">
      <div
        v-for="(ef, efi) in params.textEffects"
        :key="efi + 'effect'"
        :style="{
          fontFamily: `'${params.fontClass.value}'`,
          color: ef.filling && ef.filling.enable && ef.filling.type === 0 ? ef.filling.color : 'transparent',
          WebkitTextStroke: ef.stroke && ef.stroke.enable ? `${ef.stroke.width}px ${ef.stroke.color}` : undefined,
          textShadow: ef.shadow && ef.shadow.enable ? `${ef.shadow.offsetX}px ${ef.shadow.offsetY}px ${ef.shadow.blur}px ${ef.shadow.color}` : undefined,
          backgroundImage: ef.filling && ef.filling.enable ? (ef.filling.type === 0 ? undefined : getGradientOrImg(ef)) : undefined,
          WebkitBackgroundClip: ef.filling && ef.filling.enable ? (ef.filling.type === 0 ? undefined : 'text') : undefined,
          transform: ef.offset && ef.offset.enable ? `translate(${ef.offset.x}px, ${ef.offset.y}px)` : undefined,
        }"
        class="edit-text effect-text"
        spellcheck="false"
        v-html="params.text"
      ></div>
    </template>
    <div ref="editWrap" :style="{ fontFamily: `'${params.fontClass.value}'` }" class="edit-text" spellcheck="false" :contenteditable="state.editable ? 'plaintext-only' : false" @input="writingText($event)" @blur="writeDone($event)" v-html="params.text"></div>
  </div>
</template>

<script lang="ts" setup>
// 文本组件
// const NAME = 'w-text'

import { reactive, toRefs, computed, onUpdated, watch, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { fontMinWithDraw } from '@/utils/widgets/loadFontRule'
import { getBuiltinFontByValue } from '@/common/methods/fonts'
import getGradientOrImg from './getGradientOrImg'
import { wTextSetting } from './wTextSetting'
import { useForceStore, useHistoryStore, useWidgetStore } from '@/store'

export type TwTextParams = {
  rotate?: number
  lock?: boolean
  width?: number
  height?: number
} & typeof wTextSetting

type TProps = {
  params: TwTextParams
  parent: {
    left: number
    top: number
  }
}

const props = defineProps<TProps>()
const widgetStore = useWidgetStore()
const forceStore = useForceStore()
const historyStore = useHistoryStore()
const route = useRoute()
const state = reactive({
  loading: false,
  editable: false,
  loadFontDone: '',
})
const widget = ref<HTMLElement | null>(null)
const editWrap = ref<HTMLElement | null>(null)

const dActiveElement = computed(() => widgetStore.dActiveElement)
const isDraw = computed(() => route.name === 'Draw')

onUpdated(() => {
  updateRecord()
})

onMounted(() => {
  updateRecord()

  if (!widget.value) return
  props.params.transform && (widget.value.style.transform = props.params.transform)
  props.params.rotate && (widget.value.style.transform += `translate(0px, 0px) rotate(${props.params.rotate}) scale(1, 1)`)
  // store.commit('updateRect')
})

watch(
  () => props.params,
  async (nval) => {
    updateText()
    if (state.loading) {
      return
    }
    let font = nval.fontClass as any

    // 兼容老数据 / 服务端模板中没有 url 的情况：
    // 如果当前字体没有 url，但 value 能在内置字体中找到，则自动补全 url 等信息，
    // 这样就能触发本地 /art 下字体的加载。
    if (font && !font.url && font.value) {
      const builtin = getBuiltinFontByValue(font.value)
      if (builtin) {
        font.url = builtin.url
        font.alias = font.alias || builtin.alias
        font.id = font.id || builtin.id
        font.oid = font.oid ?? builtin.oid
      }
    }

    const isDone = font.value === state.loadFontDone

    if (font.url && !isDone) {
      // 如果开启了服务端子集提取，这里不再二次加载
      if (fontMinWithDraw) {
        state.loading = false
        return
      }

      state.loading = !isDraw.value
      try {
        // 为避免特殊字符导致的 CSS 解析问题，这里对 url 做显式引号包裹
        const src = `url("${font.url}")`
        const loadFont = new window.FontFace(font.value, src)
        await loadFont.load()
        document.fonts.add(loadFont)
        state.loadFontDone = font.value
      } catch (e) {
        console.error('字体加载失败:', font.value, font.url, e)
      } finally {
        state.loading = false
      }
    } else {
      state.loading = false
    }
  },
  { immediate: true, deep: true },
)

watch(
  () => state.editable,
  (value) => {
    widgetStore.updateWidgetData({
      uuid: String(props.params.uuid),
      key: 'editable',
      value,
    })
  },
)

function updateRecord() {
  if (!widget.value) return
  if (dActiveElement.value && dActiveElement.value.uuid === String(props.params.uuid)) {
    let record = dActiveElement.value.record
    record.width = widget.value.offsetWidth
    record.height = widget.value.offsetHeight
    record.minWidth = props.params.fontSize
    record.minHeight = props.params.fontSize * props.params.lineHeight
    writingText()
  }
}

function updateText(e?: Event) {
  const value = e && e.target ? (e.target as HTMLElement).innerHTML : props.params.text //.replace(/\n/g, '<br/>')
  if (value !== props.params.text) {
    widgetStore.updateWidgetData({
      uuid: String(props.params.uuid),
      key: 'text',
      value,
    })
  }
}

function writingText(e?: Event) {
  // updateText(e)
  // TODO: 修正文字选框高度
  const el = editWrap.value || widget.value
  if (!el) return
  widgetStore.updateWidgetData({
    uuid: String(props.params.uuid),
    key: 'height',
    value: el.offsetHeight,
  })
  forceStore.setUpdateRect()
  // store.commit('updateRect')
}

function writeDone(e: Event) {
  state.editable = false
  updateText(e)
}

function dblclickText(_: MouseEvent) {
  if (state.editable) return
  state.editable = true
  const el = editWrap.value || widget.value
  setTimeout(() => {
    if (!el) return
    el.focus()
    if (document.selection) {
      const range = document.body.createTextRange()
      range.moveToElementText(el)
      range.select()
    } else {
      const range = document.createRange()
      range.selectNodeContents(el)
      window.getSelection()?.removeAllRanges()
      window.getSelection()?.addRange(range)
    }
  }, 100)
}

defineExpose({
  getGradientOrImg,
  updateRecord,
  writingText,
  updateText,
  writeDone,
  dblclickText,
  widget,
  editWrap,
})
</script>

<style lang="less" scoped>
.w-text {
  // cursor: pointer;
  user-select: none;
}
.w-text.editing {
  cursor: text;
  user-select: text;
}
.edit-text {
  outline: none;
  word-break: break-word;
  white-space: pre-wrap;
  margin: 0;
}
.effect-text {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
</style>
