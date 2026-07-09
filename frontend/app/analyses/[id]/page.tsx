'use client'

import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { getAnalysis, ApiError } from '@/lib/api'
import type { Analysis } from '@/lib/contracts'
import StepProgress from '@/components/StepProgress'
import ScoreGauge from '@/components/ScoreGauge'
import ResultsTable from '@/components/ResultsTable'

const POLL_MS = 2000

export default function AnalysisPage() {
  const params = useParams<{ id: string }>()
  const id = params.id
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    let cancelled = false

    function stop() {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }

    async function poll() {
      try {
        const data = await getAnalysis(id)
        if (cancelled) return
        setAnalysis(data)
        setLoadError(null)
        if (data.status === 'done' || data.status === 'failed') stop()
      } catch (err) {
        if (cancelled) return
        setLoadError(err instanceof Error ? err.message : 'Something went wrong.')
        // A 404/422 will never self-resolve (unknown or malformed id), so stop
        // polling; transient errors keep retrying.
        if (err instanceof ApiError && (err.status === 404 || err.status === 422)) {
          stop()
        }
      }
    }

    poll()
    timerRef.current = setInterval(poll, POLL_MS)

    return () => {
      cancelled = true
      stop()
    }
  }, [id])

  let content: ReactNode
  if (!analysis && loadError) {
    content = <FailureCard reason={loadError} />
  } else if (!analysis) {
    content = <p className="text-sm text-surface-subtle">Loading…</p>
  } else if (analysis.status === 'failed') {
    content = <FailureCard reason={analysis.error ?? 'The analysis failed.'} />
  } else if (analysis.status === 'done') {
    content = <Results analysis={analysis} />
  } else {
    content = (
      <StepProgress
        status={analysis.status}
        progress={analysis.progress}
        currentStep={analysis.current_step}
      />
    )
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-12 sm:px-8">
      <div className="space-y-8">
        <header className="space-y-1">
          <h1 className="text-3xl font-semibold text-surface-foreground">Analysis</h1>
          {analysis ? (
            <p className="break-all text-sm text-surface-subtle">{analysis.url}</p>
          ) : null}
        </header>
        {/* Persistent live region: StepProgress (and its own live region) unmounts
            on completion, so announce the terminal outcome here instead. */}
        <p aria-live="polite" className="sr-only">
          {analysis?.status === 'done'
            ? 'Analysis complete. Your GEO score is ready.'
            : analysis?.status === 'failed'
              ? 'Analysis failed.'
              : ''}
        </p>
        {content}
      </div>
    </main>
  )
}

function FailureCard({ reason }: { reason: string }) {
  return (
    <div className="space-y-3 rounded-lg border border-danger bg-danger-soft p-6">
      <h2 className="text-xl font-semibold text-danger">
        {"We couldn't finish this analysis."}
      </h2>
      <p className="text-sm text-surface-foreground">{reason}</p>
      <Link
        href="/"
        className="inline-block rounded text-sm font-medium text-primary hover:text-primary-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        Try another URL
      </Link>
    </div>
  )
}

function Results({ analysis }: { analysis: Analysis }) {
  const { result } = analysis
  const total = result.total_responses ?? result.responses.length
  const footprints =
    result.footprint_count ??
    result.responses.filter((response) => response.footprint).length
  const percent = Math.round((result.geo_score ?? 0) * 100)

  return (
    <div className="space-y-8">
      <section className="rounded-lg border border-surface-border bg-white p-6 shadow-sm">
        <ScoreGauge score={percent} footprintCount={footprints} totalResponses={total} />
      </section>

      {result.kyc ? (
        <section className="space-y-3">
          <h2 className="text-xl font-semibold text-surface-foreground">
            Company profile (KYC)
          </h2>
          <pre className="overflow-x-auto rounded-lg bg-surface-muted p-4 font-mono text-sm text-surface-foreground">
            {JSON.stringify(result.kyc, null, 2)}
          </pre>
        </section>
      ) : null}

      {result.prompts.length > 0 ? (
        <section className="space-y-3">
          <h2 className="text-xl font-semibold text-surface-foreground">
            Generated prompts
          </h2>
          <ul className="space-y-2">
            {result.prompts.map((prompt) => (
              <li
                key={prompt.id}
                className="flex flex-col gap-2 rounded-lg border border-surface-border bg-white p-3 sm:flex-row sm:items-start"
              >
                <span className="w-fit rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-700">
                  {prompt.category}
                </span>
                <span className="text-sm text-surface-foreground">{prompt.text}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-surface-foreground">Responses</h2>
        <ResultsTable responses={result.responses} prompts={result.prompts} />
      </section>
    </div>
  )
}
