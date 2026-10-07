export interface RoundImage {
  image_id: string
  url: string
}

export interface Round {
  pair_id: string
  caption: string
  images: RoundImage[]
}

export interface Credit {
  source: string
  license: string
  license_url: string
  source_url: string
}

export interface RevealedImage {
  image_id: string
  credit: Credit
}

export interface GuessResult {
  correct: boolean
  generator: string
  real: RevealedImage
  ai: RevealedImage
}

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init)
  if (!response.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${path} failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

/** Fetch a random pair: a real photo and an AI image of the same subject, in random order. */
export function fetchRound(): Promise<Round> {
  return request<Round>('/round')
}

/** Submit the image the player thinks is real; the server reveals which one was. */
export function submitGuess(pairId: string, imageId: string): Promise<GuessResult> {
  return request<GuessResult>('/guess', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pair_id: pairId, image_id: imageId }),
  })
}
