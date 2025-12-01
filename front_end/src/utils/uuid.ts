// 简单的 UUID 生成工具，优先使用 crypto.randomUUID，降级到时间戳+随机数
export function genId(): string {
  try {
    if (typeof crypto !== 'undefined' && typeof (crypto as any).randomUUID === 'function') {
      return (crypto as any).randomUUID()
    }
  } catch {
    // ignore and fall back
  }

  // 在不支持 Web Crypto 的环境下使用简单的随机字符串作为兜底
  return (
    Date.now().toString(36) +
    '-' +
    Math.random().toString(36).slice(2, 10)
  )
}

