export type Label = 'real' | 'ai'

export interface Round {
  image_id: string
  url: string
}

export interface GuessResult {
  correct: boolean
  answer: Label
}

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init)
  if (!response.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${path} failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

/** Fetch a random image to guess on. Never includes the answer. */
export function fetchRound(): Promise<Round> {
  return request<Round>('/round')
}

/** Submit a guess; the server says whether it was right and reveals the answer. */
export function submitGuess(imageId: string, guess: Label): Promise<GuessResult> {
  return request<GuessResult>('/guess', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_id: imageId, guess }),
  })
}
