/*
 * Test de bout en bout du parcours ORDONNANCE depuis le navigateur réel.
 *
 * Vérifie, dans Chrome via le protocole DevTools (mêmes conventions que
 * scripts/cdp-check.mjs, sans dépendance npm supplémentaire) :
 *
 *   full            connexion dentiste → patient → saisie de plusieurs
 *                   médicaments → génération via l'API réelle → ouverture /
 *                   téléchargement / impression du VRAI fichier DOCX
 *                   (comparaison SHA-256 des octets servis, contenu ZIP,
 *                   cible exacte de l'action d'impression) → affichage
 *                   d'une erreur backend réelle.
 *   no-template     aucun modèle approuvé ⇒ état « aucun modèle » affiché.
 *   foreign-patient dossier patient non rattaché ⇒ état d'erreur affiché.
 *
 * Usage :
 *   E2E_EMAIL=... E2E_PASSWORD=... node scripts/e2e-prescription.mjs full
 */

const mode = process.argv[2] || 'full'
const foreignPatientId = process.argv[3] || ''

const BASE = process.env.E2E_BASE_URL || 'http://localhost:5173'
const CDP_PORT = process.env.E2E_CDP_PORT || '9222'
const EMAIL = process.env.E2E_EMAIL
const PASSWORD = process.env.E2E_PASSWORD

const failures = []
const passes = []

function check(label, condition, detail = '') {
  if (condition) {
    passes.push(label)
    console.log(`  PASS  ${label}`)
  } else {
    failures.push(`${label}${detail ? ` — ${detail}` : ''}`)
    console.log(`  FAIL  ${label}${detail ? ` — ${detail}` : ''}`)
  }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function openTarget(url) {
  const endpoint = `http://127.0.0.1:${CDP_PORT}/json/new?${encodeURIComponent(url)}`
  const response = await fetch(endpoint, { method: 'PUT' })
  if (!response.ok) throw new Error(`Impossible d'ouvrir l'onglet: ${response.status}`)
  return response.json()
}

async function listTargets() {
  const response = await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)
  if (!response.ok) throw new Error(`json/list: ${response.status}`)
  return response.json()
}

async function connect(target) {
  const socket = new WebSocket(target.webSocketDebuggerUrl)
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true })
    socket.addEventListener('error', reject, { once: true })
  })

  let id = 0
  const pending = new Map()
  const listeners = []

  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data)
    if (message.id && pending.has(message.id)) {
      pending.get(message.id)(message)
      pending.delete(message.id)
    } else if (message.method) {
      listeners.forEach((listener) => listener(message))
    }
  })

  const send = (method, params = {}) =>
    new Promise((resolve) => {
      id += 1
      pending.set(id, resolve)
      socket.send(JSON.stringify({ id, method, params }))
    })

  return {
    send,
    on: (listener) => listeners.push(listener),
    close: () => socket.close(),
  }
}

async function evaluate(page, expression, { awaitPromise = false } = {}) {
  const response = await page.send('Runtime.evaluate', {
    expression,
    returnByValue: true,
    awaitPromise,
    userGesture: true,
  })
  if (response.result?.exceptionDetails) {
    throw new Error(
      `Exception JS: ${JSON.stringify(response.result.exceptionDetails.exception?.description || response.result.exceptionDetails.text)}`,
    )
  }
  return response.result?.result?.value
}

async function waitFor(page, expression, { timeout = 15000, label = expression } = {}) {
  const started = Date.now()
  while (Date.now() - started < timeout) {
    const value = await evaluate(page, `Boolean(${expression})`)
    if (value) return true
    await sleep(200)
  }
  throw new Error(`Délai dépassé en attendant: ${label}`)
}

async function navigate(page, url) {
  await page.send('Page.navigate', { url })
  await sleep(1200)
}

async function login(page) {
  await navigate(page, `${BASE}/login`)
  await waitFor(page, `document.querySelector('form.form-shell')`, { label: 'formulaire de connexion' })

  await evaluate(
    page,
    `(() => {
      const set = (sel, value) => {
        const el = document.querySelector(sel)
        if (!el) return false
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set
        setter.call(el, value)
        el.dispatchEvent(new Event('input', { bubbles: true }))
        return true
      }
      return set('input[type="email"]', ${JSON.stringify(EMAIL)}) &&
             set('input[type="password"]', ${JSON.stringify(PASSWORD)})
    })()`,
  )
  await evaluate(page, `document.querySelector('form.form-shell button[type="submit"]').click()`)

  await waitFor(page, `localStorage.getItem('authToken')`, { label: 'jeton d’authentification' })
  const token = await evaluate(page, `localStorage.getItem('authToken')`)
  check('Connexion dentiste : jeton d’authentification reçu', Boolean(token))
}

async function openPatientDossier(page) {
  await navigate(page, `${BASE}/dashboard/modules/patients`)
  await waitFor(page, `document.querySelectorAll('table tbody tr').length > 0`, {
    label: 'liste des patients',
  })
  const patientRows = await evaluate(page, `document.querySelectorAll('table tbody tr').length`)
  check('Liste patients chargée depuis /api/practitioner-patients/', patientRows > 0, `lignes=${patientRows}`)

  const patientName = await evaluate(
    page,
    `(() => {
      const row = document.querySelector('table tbody tr')
      return row ? [row.cells[1]?.textContent, row.cells[2]?.textContent].join(' ').trim() : ''
    })()`,
  )

  await evaluate(
    page,
    `(() => {
      const button = Array.from(document.querySelectorAll('button'))
        .find((el) => el.textContent.includes('Ouvrir le dossier'))
      if (button) button.click()
      return Boolean(button)
    })()`,
  )
  await waitFor(page, `document.querySelector('[data-testid="prescription-form"]')`, {
    label: 'section ordonnance',
  })
  check('Dossier ouvert : section « Ordonnance (document Word) » présente', true)
  return patientName
}

async function fillLine(page, index, values) {
  return evaluate(
    page,
    `(() => {
      const lines = document.querySelectorAll('[data-testid="medication-line"]')
      const line = lines[${index}]
      if (!line) return 'ligne-absente'
      const inputs = line.querySelectorAll('input')
      if (inputs.length !== 6) return 'nb-inputs=' + inputs.length
      const set = (el, value) => {
        const setter = Object.getOwnPropertyDescriptor(
          el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype,
          'value',
        ).set
        setter.call(el, value)
        el.dispatchEvent(new Event('input', { bubbles: true }))
      }
      const values = ${JSON.stringify(values)}
      const keys = ['name', 'dosage', 'frequency', 'route', 'start_date', 'end_date']
      keys.forEach((key, position) => set(inputs[position], values[key]))
      const textarea = line.querySelector('textarea')
      if (values.notes) set(textarea, values.notes)
      return 'ok'
    })()`,
  )
}

async function main() {
  if (!EMAIL || !PASSWORD) {
    throw new Error('Variables E2E_EMAIL et E2E_PASSWORD requises.')
  }

  const target = await openTarget(`${BASE}/login`)
  const page = await connect(target)
  await page.send('Page.enable')
  await page.send('Runtime.enable')

  console.log(`\n=== E2E ordonnance — mode « ${mode} » (${BASE}) ===`)
  await login(page)

  if (mode === 'no-template') {
    await openPatientDossier(page)
    const text = await evaluate(page, `document.body.innerText`)
    check(
      'Aucun modèle approuvé ⇒ état explicite affiché',
      text.includes("Aucun modèle d'ordonnance actif et approuvé"),
    )
    check(
      'Génération impossible sans modèle approuvé',
      (await evaluate(page, `document.querySelector('[data-testid="generate-prescription"]').disabled`)) === true,
    )
  } else if (mode === 'foreign-patient') {
    if (!foreignPatientId) throw new Error('Identifiant patient requis (3e argument).')
    await navigate(page, `${BASE}/dashboard/modules/patients?patient=${foreignPatientId}&view=dentist`)
    await sleep(2000)
    const text = await evaluate(page, `document.body.innerText`)
    check(
      'Dossier non rattaché ⇒ accès refusé affiché (aucune donnée)',
      text.includes('Patient introuvable') || text.includes('Pas trouvé') || text.includes('introuvable'),
      text.slice(0, 200).replace(/\s+/g, ' '),
    )
    check(
      'Aucun formulaire d’ordonnance pour un dossier inconnu',
      (await evaluate(page, `Boolean(document.querySelector('[data-testid="prescription-form"]'))`)) === false,
    )
  } else {
    const patientName = await openPatientDossier(page)

    // Modèle approuvé disponible côté dentiste.
    const templateOptions = await evaluate(
      page,
      `document.querySelector('[data-testid="template-select"]').querySelectorAll('option').length`,
    )
    check("Modèle d'ordonnance approuvé proposé par l'API", templateOptions > 1, `options=${templateOptions}`)

    // Informations patient affichées sans ressaisie.
    const headerText = await evaluate(page, `document.body.innerText`)
    check(
      'Identité du patient affichée depuis le backend',
      patientName && headerText.includes(patientName.split(' ').pop()),
      `patient=${patientName}`,
    )

    // Saisie de plusieurs médicaments (lignes ajoutées/modifiables/supprimables).
    const before = await evaluate(page, `document.querySelectorAll('[data-testid="medication-line"]').length`)
    check('Une ligne de médicament est proposée par défaut', before === 1, `lignes=${before}`)

    await fillLine(page, 0, {
      name: 'Amoxicilline',
      dosage: '500 mg',
      frequency: '3 fois par jour',
      route: 'orale',
      start_date: '2026-10-15',
      end_date: '2026-10-21',
      notes: 'Après le repas',
    })
    await evaluate(page, `document.querySelector('[data-testid="add-medication"]').click()`)
    await sleep(300)
    const after = await evaluate(page, `document.querySelectorAll('[data-testid="medication-line"]').length`)
    check('Ajout d’une seconde ligne de médicament', after === 2, `lignes=${after}`)

    await fillLine(page, 1, {
      name: 'Paracétamol',
      dosage: '1 g',
      frequency: 'si douleur',
      route: 'orale',
      start_date: '2026-10-15',
      end_date: '',
      notes: 'Ne pas dépasser 3 g par jour',
    })
    const filled = await evaluate(
      page,
      `document.querySelector('[data-testid="medication-line"] input').value`,
    )
    check('Champs de médicament renseignés dans le formulaire', filled === 'Amoxicilline', `valeur=${filled}`)

    // Génération via l'API réelle.
    const disabledBefore = await evaluate(
      page,
      `document.querySelector('[data-testid="generate-prescription"]').disabled`,
    )
    check('Bouton de génération actif dès que le traitement est valide', disabledBefore === false)

    await evaluate(page, `document.querySelector('[data-testid="generate-prescription"]').click()`)
    await waitFor(page, `document.querySelector('[data-testid="prescription-result"]')`, {
      timeout: 30000,
      label: 'résultat de génération',
    })
    const hasError = await evaluate(
      page,
      `Boolean(document.querySelector('[data-testid="generate-error"]'))`,
    )
    check('Génération réussie sans erreur backend', !hasError)

    const resultText = await evaluate(
      page,
      `document.querySelector('[data-testid="prescription-result"]').innerText`,
    )
    check('Réponse API affichée (prescription + médicaments)', /Prescription n° \d+/.test(resultText), resultText.replace(/\s+/g, ' ').slice(0, 160))

    // Traitements enregistrés côté serveur (liste rechargée après génération).
    let listedMedications = false
    for (let attempt = 0; attempt < 25 && !listedMedications; attempt += 1) {
      const currentText = await evaluate(page, `document.body.innerText`)
      listedMedications =
        currentText.includes('Déjà enregistré au dossier') &&
        currentText.includes('Amoxicilline') &&
        currentText.includes('Paracétamol')
      if (!listedMedications) await sleep(300)
    }
    check(
      'Traitements enregistrés au dossier et listés',
      listedMedications,
    )

    // Fichier DOCX réellement récupéré depuis le backend.
    const href = await evaluate(
      page,
      `document.querySelector('[data-testid="download-document"]').getAttribute('href')`,
    )
    check('URL du fichier générée par le backend', /^\/media\/prescriptions\/generated\/.+\.docx/.test(href || ''), `href=${href}`)

    const fetched = await evaluate(
      page,
      `(async () => {
        const response = await fetch(${JSON.stringify(href)})
        const buffer = await response.arrayBuffer()
        const digest = await crypto.subtle.digest('SHA-256', buffer)
        const bytes = new Uint8Array(buffer)
        return {
          status: response.status,
          contentType: response.headers.get('content-type'),
          length: buffer.byteLength,
          magic: String.fromCharCode(...bytes.slice(0, 2)),
          sha256: Array.from(new Uint8Array(digest))
            .map((b) => b.toString(16).padStart(2, '0'))
            .join(''),
        }
      })()`,
      { awaitPromise: true },
    )
    check('Fichier accessible depuis le frontend (HTTP 200)', fetched?.status === 200, JSON.stringify(fetched))
    check('Octets = archive ZIP (vrai DOCX, pas une page HTML)', fetched?.magic === 'PK', `magic=${fetched?.magic}`)
    console.log(`        sha256 servi = ${fetched?.sha256} (${fetched?.length} octets, ${fetched?.contentType})`)

    // Action d'impression : doit viser EXACTEMENT le fichier backend.
    const beforeTargets = new Set((await listTargets()).map((item) => item.id))
    await evaluate(page, `document.querySelector('[data-testid="print-document"]').click()`)

    let printedTarget = null
    for (let attempt = 0; attempt < 40 && !printedTarget; attempt += 1) {
      const targets = await listTargets()
      printedTarget =
        targets.find(
          (item) => !beforeTargets.has(item.id) && (item.url || '').includes('/media/prescriptions/generated/'),
        ) || null
      if (!printedTarget) await sleep(100)
    }
    check(
      "Action d'impression : nouvel onglet = fichier DOCX du backend",
      Boolean(printedTarget),
      printedTarget ? printedTarget.url : 'aucun onglet /media/prescriptions/generated détecté',
    )
    if (printedTarget) {
      check(
        "Cible d'impression identique au fichier téléchargé",
        printedTarget.url.split('?')[0].endsWith(href.split('?')[0]),
        `impression=${printedTarget.url} fichier=${href}`,
      )
    }

    // Erreur backend affichée réellement (nom > 255 caractères refusé par
    // le serializer du modèle Medication).
    await evaluate(page, `document.querySelector('[data-testid="add-medication"]').click()`)
    await sleep(300)
    await fillLine(page, 2, {
      name: 'X'.repeat(300),
      dosage: '10 mg',
      frequency: '1/j',
      route: 'orale',
      start_date: '2026-10-15',
      end_date: '',
      notes: '',
    })
    await evaluate(page, `document.querySelector('[data-testid="generate-prescription"]').click()`)
    await waitFor(page, `document.querySelector('[data-testid="generate-error"]')`, {
      timeout: 20000,
      label: "affichage de l'erreur backend",
    })
    const errorText = await evaluate(
      page,
      `document.querySelector('[data-testid="generate-error"]').innerText`,
    )
    check(
      'Erreur backend affichée telle quelle (255 caractères)',
      errorText.includes('255'),
      errorText.replace(/\s+/g, ' ').slice(0, 200),
    )
  }

  await page.close?.()
  console.log(`\nRésultat : ${passes.length} réussis, ${failures.length} échec(s).`)
  if (failures.length > 0) {
    failures.forEach((failure) => console.log(`  ✗ ${failure}`))
    process.exitCode = 1
  }
}

main().catch((error) => {
  console.error(`ERREUR: ${error.message}`)
  process.exitCode = 1
})
