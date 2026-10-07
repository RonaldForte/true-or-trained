import { useEffect, useState } from 'react'
import { fetchRound, submitGuess, type GuessResult, type Label, type Round } from './api'
import './App.css'

const LOAD_ERROR = 'Could not load an image. Is the backend running?'

function App() {
  const [round, setRound] = useState<Round | null>(null)
  const [result, setResult] = useState<GuessResult | null>(null)
  const [score, setScore] = useState({ correct: 0, total: 0 })
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(true)

  async function loadRound() {
    setBusy(true)
    setError(null)
    setResult(null)
    try {
      setRound(await fetchRound())
    } catch {
      setError(LOAD_ERROR)
    } finally {
      setBusy(false)
    }
  }

  async function guess(label: Label) {
    if (!round) return
    setBusy(true)
    try {
      const outcome = await submitGuess(round.image_id, label)
      setResult(outcome)
      setScore((s) => ({
        correct: s.correct + (outcome.correct ? 1 : 0),
        total: s.total + 1,
      }))
    } catch {
      setError('Could not submit your guess. Try again.')
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    // Ignore the response if the component unmounted (or StrictMode re-ran
    // this effect) before it arrived, so a stale round can't overwrite state.
    let ignore = false
    fetchRound()
      .then((r) => !ignore && setRound(r))
      .catch(() => !ignore && setError(LOAD_ERROR))
      .finally(() => !ignore && setBusy(false))
    return () => {
      ignore = true
    }
  }, [])

  return (
    <main className="game">
      <header>
        <h1>True or Trained</h1>
        <p className="score">
          Score: {score.correct} / {score.total}
        </p>
      </header>

      {error && <p className="error">{error}</p>}

      {!round && busy && (
        <p className="loading">
          Loading… the first load can take up to a minute while the server wakes up.
        </p>
      )}

      {round && (
        <img className="round-image" src={round.url} alt="Is this real or AI-generated?" />
      )}

      {round && !result && (
        <div className="actions">
          <button onClick={() => guess('real')} disabled={busy}>
            Real
          </button>
          <button onClick={() => guess('ai')} disabled={busy}>
            AI
          </button>
        </div>
      )}

      {result && (
        <div className="actions">
          <p className={result.correct ? 'result correct' : 'result wrong'}>
            {result.correct ? 'Correct!' : 'Wrong!'} It was {result.answer === 'ai' ? 'AI-generated' : 'real'}.
          </p>
          <button onClick={loadRound} disabled={busy}>
            Next image
          </button>
        </div>
      )}
    </main>
  )
}

export default App
