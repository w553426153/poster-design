<!--
 * @Author: ShawnPhang
 * @Date: 2022-03-16 09:15:52
 * @Description:  
 * @LastEditors: ShawnPhang <https://m.palxp.cn>
 * @Date: 2024-03-04 18:50:00
-->
<template>
  <div ref="qrCodeDom" class="qrcode__wrap"></div>
</template>

<script lang="ts" setup>
import { onMounted, ref, watch, nextTick } from 'vue'
import QRCodeStyling, { Options } from 'qr-code-styling'
import { debounce } from 'throttle-debounce'
import { generateOption } from './method'

export type TQrcodeProps = {
  width?: number
  height?: number
  image?: string
  value?: string
  dotsOptions: Options['dotsOptions']
}

const props = withDefaults(defineProps<TQrcodeProps>(), {
  width: 300,
  height: 300,
  dotsOptions: () => ({
    color: '#41b583',
    type: 'rounded',
  })
})

let options: Options = {}
watch(
  () => [props.width, props.height, props.dotsOptions, props.value, props.image],
  () => {
    render()
  },
)

const render = debounce(300, async () => {
  options = generateOption(props)
  if (props.value) {
    options && qrCode.update(options)
    await nextTick()
    if (!qrCodeDom?.value?.firstChild) return
    (qrCodeDom.value.firstChild as HTMLElement).setAttribute('style', "width: 100%;") // 强制其适应缩放
  }
})

const qrCode = new QRCodeStyling(options)
const qrCodeDom = ref<HTMLElement>()

onMounted(async () => {
  // 先挂载，再更新配置，避免首次 update 时容器未追加导致样式未设置
  qrCode.append(qrCodeDom.value)
  await nextTick()
  render()
})

</script>
