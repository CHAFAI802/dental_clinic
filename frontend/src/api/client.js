import { API_BASE_URL, AUTH_TOKEN_STORAGE_KEY } from '../config/api.js'

function extractDrfErrorMessage(data) {
  if (!data) return 'Requête échouée.'

  if (typeof data === 'string') return data

  if (typeof data.detail === 'string') return data.detail

  if (Array.isArray(data.non_field_errors) && data.non_field_errors.length > 0) {
    return data.non_field_errors.join(' ')
  }

  if (typeof data === 'object') {
    const fieldMessages = Object.entries(data)
      .flatMap(([field, value]) => {
        if (value == null) return []
        if (Array.isArray(value)) return value.map((v) => `${field}: ${v}`)
        if (typeof value === 'string') return [`${field}: ${value}`]
        return [`${field}: ${JSON.stringify(value)}`]
      })

    if (fieldMessages.length > 0) {
      return fieldMessages.join('\n')
    }
  }

  return 'Requête échouée.'
}

async function parseResponseBody(response) {
  if (response.status === 204) return null

  const contentType = response.headers.get('content-type') || ''
  const isJson = contentType.includes('application/json')

  if (!isJson) {
    return await response.text()
  }

  try {
    return await response.json()
  } catch {
    return null
  }
}

export async function apiRequest(path, options = {}) {
  const { method = 'GET', body, headers = {}, token } = options

  const authToken = token ?? localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)

  const requestHeaders = {
    ...headers,
  }

  if (body !== undefined && body !== null && !(body instanceof FormData)) {
    requestHeaders['Content-Type'] = 'application/json'
  }

  if (authToken) {
    requestHeaders.Authorization = `Token ${authToken}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: requestHeaders,
    body:
      body === undefined || body === null
        ? undefined
        : body instanceof FormData
          ? body
          : JSON.stringify(body),
  })

  const data = await parseResponseBody(response)

  if (!response.ok) {
    const error = new Error(extractDrfErrorMessage(data))
    error.status = response.status
    error.data = data
    throw error
  }

  return data
}

export function apiGet(path, options) {
  return apiRequest(path, { ...options, method: 'GET' })
}

export function apiPost(path, body, options) {
  return apiRequest(path, { ...options, method: 'POST', body })
}

export function apiPut(path, body, options) {
  return apiRequest(path, { ...options, method: 'PUT', body })
}

export function apiPatch(path, body, options) {
  return apiRequest(path, { ...options, method: 'PATCH', body })
}

export function apiDelete(path, options) {
  return apiRequest(path, { ...options, method: 'DELETE' })
}
