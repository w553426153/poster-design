/*
 * @Author: ShawnPhang
 * @Date: 2022-01-08 09:43:37
 * @Description: 字体处理
 * @LastEditors: ShawnPhang <https://m.palxp.cn>
 * @LastEditTime: 2024-08-12 10:33:36
 */
// import { isSupportFontFamily, blob2Base64 } from './utils'
import { TGetFontItemData, getFonts } from '@/api/material'

const nowVersion = '4' // 当前字体文件版本更新，将刷新前端缓存

// 统一维护前端内置字体（放在 public/art 下）
// 文件命名规则：
//   - 预览图：{name}.png
//   - 字体文件：{name}.woff2 或 {name}.otf
// 其中 name 就是下面 FONT_BASE_NAMES 中的字符串
const FONT_BASE_NAMES = [
  'Aa剑豪体-JT237',
  'Vetka-YW190',
  'Vlashu-YW192',
  '三极泼墨体-JT269',
  '云峰飞云体-JT279',
  '优设标题黑-JT85',
  '千图厚黑体-JT54',
  '字由文艺黑-JT171',
  '字由芳华体-JT110',
  '斗鱼追光体-JT32',
  '新愚公装甲宋B-JT235',
  '演示佛系体-FT277',
  '演示悠然小楷-JT276',
  '王漢宗印篆體-免費商用-FT86',
  '白无常可可体细-JT07',
  '胡晓波真帅体2.0-JT37',
  '荆南缘默体-JT46',
  '逐浪萌芽字-JT108',
  '钟齐流江毛笔草体（输简出繁）-FT290',
  '鸿雷拙书简体-正式版-JT332',
  '鸿雷板书简体-正式版-JT245',
  '龚帆免费体-JT244',
] as const

// 只有 otf 没有 woff2 的字体（其它默认使用 woff2）
const FONT_OTF_SET = new Set<string>([
  'Gfsignacio-YW122',
  'Great Sejagad-YW382',
  'Hyped-YW290',
  'Kilauea German Di Ciccio-YW142',
  'Sociumfree Regular-YW179',
  'Solidemirage Etroit-YW65',
  'Vetka-YW190',
])

// 将文件名转换为业务所需的字体结构
const builtinFonts: TFontItemData[] = FONT_BASE_NAMES.map((name, index) => {
  // 名称中包含中文则认为是中文字体
  const isZh = /[\u4e00-\u9fff]/.test(name)
  const lang = isZh ? 'zh' : 'en'
  const ext = FONT_OTF_SET.has(name) ? 'otf' : 'woff2'

  return {
    id: index + 1,
    oid: '0', // 本地内置字体，后端 oid 统一设为 0
    alias: name, // 侧边栏展示用
    value: name, // font-family，和别名保持一致
    preview: `/art/${name}.png`, // 预览图
    url: `/art/${name}.${ext}`, // 字体文件地址
    lang,
  }
})

// 方便根据当前代码中的内置字体集合做过滤
const builtinFontValueSet = new Set(builtinFonts.map((f) => f.value))

// 通过字体 value（font-family）获取内置字体配置
export const getBuiltinFontByValue = (value: string) => {
  return builtinFonts.find((f) => f.value === value)
}

/** 字体item类型 */
export type TFontItemData = { url: string } & Omit<TGetFontItemData, 'woff'>

const fontList: TFontItemData[] = []
// const download: any = {}
export const useFontStore = {
  list: fontList,
  // download,
  async init() {
    this.list = []
    localStorage.getItem('FONTS_VERSION') !== nowVersion && localStorage.removeItem('FONTS')
    const localFonts: TFontItemData[] = localStorage.getItem('FONTS') ? JSON.parse(localStorage.getItem('FONTS') || '') : []

    if (localFonts.length > 0) {
      // 只保留当前代码中仍存在的字体，彻底清理掉已经从 FONT_BASE_NAMES 中删除的旧字体
      const filtered = localFonts.filter((f) => builtinFontValueSet.has(f.value))
      this.list.push(...filtered)

      // 如果有被过滤掉的旧数据，顺便更新一下本地缓存
      if (filtered.length !== localFonts.length) {
        localStorage.setItem('FONTS', JSON.stringify(this.list))
        localStorage.setItem('FONTS_VERSION', nowVersion)
      }
    }

    if (this.list.length === 0) {
      // 使用前端内置字体（public/art 下维护）
      this.list.unshift(...builtinFonts)
      localStorage.setItem('FONTS', JSON.stringify(this.list))
      localStorage.setItem('FONTS_VERSION', nowVersion)
    }
    // store.dispatch('setFonts', this.list)
  },
}

// export const useFontStore = () => {
//   return {
//     list: fontList,
//     download,
//     async init() {
//       this.list = []
//       const localFonts: any = localStorage.getItem('FONTS') ? JSON.parse(localStorage.getItem('FONTS') || '') : []
//       if (localFonts.length > 0) {
//         this.list.push(...localFonts)
//       }

//       if (this.list.length === 0) {
//         const res = await getFonts({ pageSize: 400 })
//         this.list.unshift(
//           ...res.map((x: any) => {
//             const { content, id, name, preview } = x
//             return { id, name, preview: preview.url, alias: content.alias, family: content.family, lang: content.lang, ttf: content.ttf, url: content.woff }
//           }),
//         )
//         localStorage.setItem('FONTS', JSON.stringify(this.list))
//       }
//       console.log(this.list)
//     },
//     getList() {
//       return fontList
//     },
//   }
// }

// export const useFontStore = () => {
//   return {
//     list: fontList,
//     download,
//     async init() {
//       this.list = []
//       const localFonts: any = localStorage.getItem('FONTS') ? JSON.parse(localStorage.getItem('FONTS') || '') : []
//       if (localFonts.length > 0) {
//         this.list.push(...localFonts)
//       }

//       if (this.list.length === 0) {
//         for (let i = 1; i < 99; i += 1) {
//           const res = await getFonts(i)
//           this.list.unshift(
//             ...res.map((x: any) => {
//               const { content, id, name, preview } = x
//               return { id, name, preview: preview.url, alias: content.alias, family: content.family, lang: content.lang, ttf: content.ttf, url: content.woff }
//             }),
//           )
//           if (res.length < 100) break
//         }
//         localStorage.setItem('FONTS', JSON.stringify(this.list))
//       }
//     },
//     async addFont2Style(name: string, url: string) {
//       // if (this.download[name]) return;
//       if (isSupportFontFamily(name)) return

//       const response = await fetch(url, { headers: { responseType: 'blob' } })
//       const blob = await response.blob()
//       const ff = new FontFace(name, `url(${URL.createObjectURL(blob)})`)
//       const f = await ff.load()
//       ;(document.fonts as FontFaceSet).add(f)

//       const b64 = await blob2Base64(blob)
//       // 使用 base64 是为了方便将 DOM 生成图片
//       this.download[name] = b64
//       // document.head.appendChild(generateFontStyle(name, b64));
//     },
//   }
// }
