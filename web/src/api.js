// Thin client over the FastAPI backend.
// All paths go through the Vite dev proxy (`/api/*` → http://localhost:8000).
// In production, the same paths should be reverse-proxied by whatever serves the SPA.

const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: options.body && !(options.body instanceof FormData)
      ? { 'content-type': 'application/json', ...(options.headers || {}) }
      : options.headers,
    ...options
  })
  if (!res.ok) {
    let detail
    try {
      detail = (await res.json()).detail
    } catch {
      detail = res.statusText
    }
    throw new Error(`${res.status} ${detail || 'request failed'}`)
  }
  return res.json()
}

export const api = {
  health: () => request('/health'),

  createSession: (patient) =>
    request('/sessions', {
      method: 'POST',
      body: JSON.stringify({
        age: Number(patient.age),
        gender: patient.gender,
        height: Number(patient.height),
        weight: Number(patient.weight)
      })
    }),

  uploadTongue: (sessionId, file) => {
    const form = new FormData()
    form.append('image', file)
    return request(`/sessions/${sessionId}/tongue`, {
      method: 'POST',
      body: form
    })
  },

  submitPulse: (sessionId, { waveform=[] } = {}) =>
    request(`/sessions/${sessionId}/pulse`, {
      method: 'POST',
      body: JSON.stringify({
        waveform: waveform
      })
    }),

  diagnose: (sessionId) =>
    request(`/sessions/${sessionId}/diagnose`, { method: 'POST' }),

  // Proxy through the backend so the Pexels API key never reaches the SPA.
  // Returns the photo URL on success; throws on 404 (no match) or 5xx.
  foodImage: (query) =>
    request(`/foods/image?q=${encodeURIComponent(query)}`)
}

// Helper for fields that the API returns as { zh, en }.
export function pickLang(bi, lang) {
  if (!bi) return ''
  return bi[lang] ?? bi.zh ?? bi.en ?? ''
}
