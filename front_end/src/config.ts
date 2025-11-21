/*
 * @Author: ShawnPhang
 * @Date: 2024-04-05 07:31:45
 * @Description:  
 * @LastEditors: ShawnPhang <https://m.palxp.cn>
 * @LastEditTime: 2024-08-12 05:30:15
 */
const viteEnv = import.meta.env
const isDev = viteEnv.DEV
import { version } from '../package.json'

const defaultApiBase = isDev ? 'http://localhost:8000/api' : '/api'
const defaultScreenBase = isDev ? 'http://localhost:8000/api' : '/api'

const API_URL = (viteEnv.VITE_API_BASE_URL as string | undefined) || defaultApiBase
const SCREEN_URL = (viteEnv.VITE_SCREEN_BASE_URL as string | undefined) || defaultScreenBase

export default {
  isDev,
  BASE_URL: isDev ? '/' : './',
  VERSION: version,

  COPYRIGHT: 'ShawnPhang - Design.pPalxp.cn',
  // API 网关前缀（统一从 /api 进入后端）
  // - 开发环境默认: http://localhost:8000/api
  // - 生产环境默认: /api （通过 Nginx 反向代理到后端容器）
  API_URL,
  // 截图等服务前缀，默认与 API_URL 一致，如需拆分可通过环境变量覆盖
  SCREEN_URL,
  IMG_URL: 'https://store.palxp.cn/', // 七牛云资源地址
  // ICONFONT_URL: '//at.alicdn.com/t/font_3223711_74mlzj4jdue.css',
  ICONFONT_URL: '//at.alicdn.com/t/font_2717063_ypy8vprc3b.css?display=swap',
  ICONFONT_EXTRA: '//at.alicdn.com/t/c/font_3228074_xojoer6zhp.css',
  QINIUYUN_PLUGIN: 'https://lf26-cdn-tos.bytecdntp.com/cdn/expire-1-M/qiniu-js/2.5.5/qiniu.min.js',
  supportSubFont: false, // 是否开启服务端字体压缩
}

export const LocalStorageKey = {
  tokenKey: "xp_token"
}
