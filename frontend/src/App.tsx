import { useEffect, useState } from 'react'
import { fetchRound, submitGuess, type Credit, type GuessResult, type Round } from './api'
import './App.css'

const LOAD_ERROR = 'Could not load images. Is the backend running?'

function CreditLine({ credit }: { credit: Credit }) {
  return (
    <small className="credit">
      <a href={credit.source_url} target="_blank" rel="noreferrer">
        {credit.source}
      </a>{' '}
      ·{' '}
      <a href={credit.license_url} target="_blank" rel="noreferrer">
        {credit.license}
      </a>
    </small>
  )
}

function App() {
  const [round, setRound] = useState<Round | null>(null)
  const [picked, setPicked] = useState<string | null>(null)
  const [result, setResult] = useState<GuessResult | null>(null)
  const [score, setScore] = useState({ correct: 0, total: 0 })
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(true)

  async function loadRound() {
    setBusy(true)
    setError(null)
    setResult(null)
    setPicked(null)
    try {
      setRound(await fetchRound())
    } catch {
      setError(LOAD_ERROR)
    } finally {
      setBusy(false)
    }
  }

  async function guess(imageId: string) {
    if (!round || result || busy) return
    setBusy(true)
    setPicked(imageId)
    try {
      const outcome = await submitGuess(round.pair_id, imageId)
      setResult(outcome)
      setScore((s) => ({
        correct: s.correct + (outcome.correct ? 1 : 0),
        total: s.total + 1,
      }))
    } catch {
      setPicked(null)
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

  function cardClass(imageId: string) {
    if (!result) return picked === imageId ? 'card picked' : 'card'
    return imageId === result.real.image_id ? 'card real' : 'card ai'
  }

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
        <>
          <p className="prompt">
            One of these is a real photo. Which one?
            <span className="caption">“{round.caption}”</span>
          </p>

          <div className="pair">
            {round.images.map((image) => {
              const revealed = result && (image.image_id === result.real.image_id ? result.real : result.ai)
              return (
                <figure key={image.image_id} className={cardClass(image.image_id)}>
                  <button
                    onClick={() => guess(image.image_id)}
                    disabled={busy || result !== null}
                    aria-label="This one is real"
                  >
                    <img src={image.url} alt="" width={432} height={432} />
                  </button>
                  {revealed && result && (
                    <figcaption>
                      <strong>
                        {revealed === result.real ? 'Real photo' : `AI · ${result.generator}`}
                      </strong>
                      <CreditLine credit={revealed.credit} />
                    </figcaption>
                  )}
                </figure>
              )
            })}
          </div>

          {result && (
            <div className="actions">
              <p className={result.correct ? 'result correct' : 'result wrong'}>
                {result.correct ? 'Correct!' : 'Wrong — that one was AI-generated.'}
              </p>
              <button onClick={loadRound} disabled={busy}>
                Next pair
              </button>
            </div>
          )}
        </>
      )}
    </main>
  )
}

export default App
