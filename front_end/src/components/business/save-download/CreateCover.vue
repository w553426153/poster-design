<!--
 * @Author: ShawnPhang
 * @Date: 2021-08-01 11:12:17
 * @Description: 前端出图 - 用于封面
 * @LastEditors: ShawnPhang <https://m.palxp.cn>
 * @Date: 2024-03-04 18:50:00
-->
<template>
  <div id="cover-wrap"></div>
</template>

<script lang="ts" setup>
import html2canvas from 'html2canvas'
import Qiniu from '@/common/methods/QiNiu'
// import { useSetupMapGetters } from '@/common/hooks/mapGetters'
import { useCanvasStore, useWidgetStore } from '@/store'
import FontFaceObserver from 'fontfaceobserver'
import appConfig from '@/config'

// const { dZoom } = useSetupMapGetters(['dZoom'])

const canvasStore = useCanvasStore()
const widgetStore = useWidgetStore()

// 统一构建后端地址，用于 html2canvas 跨域图片代理
const apiHost =
  appConfig.API_URL && appConfig.API_URL.trim().length
    ? appConfig.API_URL
    : typeof window !== 'undefined'
      ? window.location.origin
      : ''
const apiBase = apiHost.replace(/\/$/, '')
const html2canvasProxy = `${apiBase}/files/proxy`

// props: ['modelValue'],
// emits: ['update:modelValue'],

async function createCover(cb: any) {
  // 取消选中元素
  widgetStore.selectWidget({
    uuid: '-1',
  })
  // store.dispatch('selectWidget', {
  //   uuid: '-1',
  // })

  const opts = {
    // 使用后端代理跨域图片，避免直接走 CORS 导致图片被拦截
    proxy: html2canvasProxy,
    useCORS: false,
    allowTaint: false,
    scale: 0.2,
  }
  setTimeout(async () => {
    const clonePage = document.getElementById('page-design-canvas')?.cloneNode(true) as HTMLElement
    if (!clonePage) return
    clonePage.setAttribute('id', 'clone-page')
    document.body.appendChild(clonePage)
    // 同步二维码画布和矢量图形，避免导出时丢失
    syncQRCodeCanvas(clonePage)
    syncSvgElements(clonePage)
    html2canvas(clonePage, opts).then((canvas) => {
      canvas.toBlob(
        async (blobObj) => {
          if (blobObj) {
            const result = await Qiniu.upload(blobObj, { bucket: 'xp-design', prePath: 'cover/user' })
            cb(result)
          }
        },
        'image/jpeg',
        0.15,
      )
      clonePage.remove()
    })
  }, 10)
}

async function createPoster() {
  await checkFonts() // 等待字体加载完成
  const fonts = document.fonts

  const opts = {
    backgroundColor: null, // 关闭背景以支持透明图片生成
    // 通过后端代理远程图片，避免 CORS 限制导致图片丢失
    proxy: html2canvasProxy,
    useCORS: false,
    allowTaint: false,
    // scale 设为 1，导出的图片尺寸与画布设置尺寸保持一致
    scale: 1,
    logging: false, // 调试时设为 true
    onclone: (document: any) => {
      fonts.forEach((font) => document.fonts.add(font))
      // 确保克隆文档中的设计画布按照 100% 缩放导出，而不受当前视图缩放(dZoom)影响
      const designCanvas = document.getElementById('page-design-canvas') as HTMLElement | null
      if (designCanvas) {
        // 强制覆盖掉原本由 dZoom 生成的 transform
        designCanvas.style.transform = 'scale(1)'
        designCanvas.style.transformOrigin = 'center top'
      }
    },
  }
  
  return new Promise((resolve) => {
    const clonePage = document.getElementById('page-design-canvas')?.cloneNode(true) as HTMLElement
    if (!clonePage) return
    clonePage.setAttribute('id', 'clone-page')
    document.body.appendChild(clonePage)
    syncQRCodeCanvas(clonePage)
    // 将设计中的矢量图形同步为可被 html2canvas 正确渲染的元素
    syncSvgElements(clonePage)
    html2canvas(clonePage, opts).then((canvas) => {
      canvas.toBlob(async (blob) => {
        resolve({ blob })
      }, `image/png`)
      clonePage.remove()
    })
  })
}

function syncQRCodeCanvas(cloneRoot: HTMLElement) {
  const originalCanvases = window.document.querySelectorAll('.qrcode__wrap canvas')
  const cloneCanvases = cloneRoot.querySelectorAll('.qrcode__wrap canvas')
  if (!originalCanvases.length || !cloneCanvases.length) return
  const cloneDoc = cloneRoot.ownerDocument || window.document
  cloneCanvases.forEach((cloneCanvas, index) => {
    const sourceCanvas = originalCanvases[index] as HTMLCanvasElement | undefined
    if (!sourceCanvas) return
    if (!(cloneCanvas instanceof HTMLCanvasElement)) return
    try {
      const dataUrl = sourceCanvas.toDataURL('image/png')
      const img = cloneDoc.createElement('img')
      img.src = dataUrl
      img.style.width = cloneCanvas.style.width || '100%'
      img.style.height = cloneCanvas.style.height || '100%'
      img.style.display = 'block'
      cloneCanvas.replaceWith(img)
    } catch (error) {
      cloneCanvas.width = sourceCanvas.width
      cloneCanvas.height = sourceCanvas.height
      const ctx = cloneCanvas.getContext('2d')
      ctx && ctx.drawImage(sourceCanvas, 0, 0)
    }
  })
}

// 将编辑区中的 w-svg 矢量图转换为克隆节点中的 <img>，提高 html2canvas 兼容性
function syncSvgElements(cloneRoot: HTMLElement) {
  // 原始文档中的矢量图容器
  const originalSvgWrappers = window.document.querySelectorAll('.w-svg')
  // 克隆文档中的矢量图容器
  const cloneSvgWrappers = cloneRoot.querySelectorAll('.w-svg')
  if (!originalSvgWrappers.length || !cloneSvgWrappers.length) return

  const cloneDoc = cloneRoot.ownerDocument || window.document

  cloneSvgWrappers.forEach((cloneWrapper, index) => {
    const originalWrapper = originalSvgWrappers[index] as HTMLElement | undefined
    if (!originalWrapper) return

    const svg = originalWrapper.querySelector('svg')
    if (!svg) return

    try {
      // 克隆一份 SVG，补齐宽高，避免在某些环境下渲染为 0
      const svgClone = svg.cloneNode(true) as SVGElement
      const width =
        svg.clientWidth ||
        parseInt(svg.getAttribute('width') || '0', 10) ||
        originalWrapper.clientWidth ||
        0
      const height =
        svg.clientHeight ||
        parseInt(svg.getAttribute('height') || '0', 10) ||
        originalWrapper.clientHeight ||
        0

      if (width > 0 && height > 0) {
        svgClone.setAttribute('width', String(width))
        svgClone.setAttribute('height', String(height))
      }

      const serialized = new XMLSerializer().serializeToString(svgClone)
      const encoded = encodeURIComponent(serialized)
        .replace(/'/g, '%27')
        .replace(/"/g, '%22')
      const dataUrl = `data:image/svg+xml,${encoded}`

      const img = cloneDoc.createElement('img')
      img.src = dataUrl
      img.style.width = '100%'
      img.style.height = '100%'
      img.style.display = 'block'

      // 用图片替换克隆节点中的 SVG，使 html2canvas 按图片方式渲染
      ;(cloneWrapper as HTMLElement).innerHTML = ''
      cloneWrapper.appendChild(img)
    } catch (error) {
      // 任何异常都不影响整体导出流程
      console.error('syncSvgElements error:', error)
    }
  })
}

// 检查字体是否加载完成
async function checkFonts() {
  const widgets = widgetStore.getWidgets()
  const fontLoaders: Promise<void>[] = []
  widgets.forEach((item: any) => {
    if (item.fontClass && item.fontClass.value) {
      const loader = new FontFaceObserver(item.fontClass.value)
      fontLoaders.push(loader.load(null, 120000)) // 延长超时让检测不会丢失字体
    }
  })
  await Promise.all(fontLoaders)
}

defineExpose({
  createCover,
  createPoster,
})
</script>

<style lang="less">
#clone-page {
  position: absolute;
  z-index: 99999;
  left: -99999px;
}
</style>
