/*
 * Script de vérification (développement uniquement, non utilisé par le site).
 * Vérifie via le protocole Chrome DevTools qu'aucune page n'a de débordement
 * horizontal et que le contenu est rendu.
 *
 * Usage : node scripts/cdp-check.mjs <port> <viewportW> <url...>
 */
const [, , port = '9222', widthArg = '375', ...urls] = process.argv

const VIEWPORTS = [
  { width: Number(widthArg), height: 812, mobile: true },
  { width: 1440, height: 900, mobile: false },
]

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function check(url, viewport) {
  const endpoint = `http://127.0.0.1:${port}/json/new?${encodeURIComponent(url)}`
  const response = await fetch(endpoint, { method: 'PUT' })
  if (!response.ok) throw new Error(`Impossible d'ouvrir l'onglet: ${response.status}`)
  const target = await response.json()

  const socket = new WebSocket(target.webSocketDebuggerUrl)
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true })
    socket.addEventListener('error', reject, { once: true })
  })

  let id = 0
  const pending = new Map()
  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data)
    if (message.id && pending.has(message.id)) {
      pending.get(message.id)(message)
      pending.delete(message.id)
    }
  })

  const send = (method, params = {}) =>
    new Promise((resolve) => {
      id += 1
      pending.set(id, resolve)
      socket.send(JSON.stringify({ id, method, params }))
    })

  await send('Page.enable')
  await send('Runtime.enable')
  await send('Emulation.setDeviceMetricsOverride', {
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: 1,
    mobile: viewport.mobile,
  })

  await send('Page.navigate', { url })
  await sleep(1500)

  const result = await send('Runtime.evaluate', {
    returnByValue: true,
    expression: `(() => {
      const de = document.documentElement;
      const clientWidth = de.clientWidth;
      const offenders = [...document.querySelectorAll('body *')]
        .filter((el) => el.getBoundingClientRect().right > clientWidth + 1)
        .slice(0, 6)
        .map((el) => (typeof el.className === 'string' && el.className ? el.className : el.tagName));
      return JSON.stringify({
        scrollWidth: de.scrollWidth,
        clientWidth,
        overflow: de.scrollWidth > clientWidth + 1,
        offenders,
        h1: document.querySelector('h1')?.textContent || null,
        links: document.querySelectorAll('a').length,
      });
    })()`,
  })

  socket.close()
  await fetch(`http://127.0.0.1:${port}/json/close/${target.id}`)

  const value = JSON.parse(result.result.result.value)
  const status = value.overflow ? 'OVERFLOW' : 'ok'
  console.log(
    `[${status}] ${viewport.width}px ${url} → ${value.scrollWidth}/${value.clientWidth}` +
      ` h1="${value.h1}" liens=${value.links}` +
      (value.offenders.length ? ` débordants: ${value.offenders.join(', ')}` : ''),
  )
  return !value.overflow
}

let allOk = true
for (const url of urls) {
  for (const viewport of VIEWPORTS) {
    try {
      const ok = await check(url, viewport)
      allOk = allOk && ok
    } catch (error) {
      allOk = false
      console.log(`[ERREUR] ${viewport.width}px ${url} → ${error.message}`)
    }
  }
}

process.exit(allOk ? 0 : 1)
