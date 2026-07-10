'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'
import Button from '@/components/Button'
import { submitLead } from '@/lib/api'

// Mirror the backend's conservative shape check (api/schemas.py _EMAIL_RE) so an
// invalid address is caught client-side and NOTHING is revealed before a POST.
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

const ERROR_ID = 'email-gate-error'
const STATUS_ID = 'email-gate-status'

type Status = 'idle' | 'submitting' | 'success' | 'error'

interface EmailGateProps {
  // Carried from the submit response via the results route query param. When
  // absent the gate can't post, so submit is blocked with an inline message.
  submissionId: string | null
  // How many answers stay hidden until the email unlocks the full report.
  hiddenCount: number
  onUnlock: () => void
}

export default function EmailGate({
  submissionId,
  hiddenCount,
  onUnlock,
}: EmailGateProps) {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage(null)

    const trimmed = email.trim()
    if (!EMAIL_RE.test(trimmed)) {
      // Invalid: inline danger message, reveal nothing, no network call.
      setStatus('error')
      setErrorMessage('Enter a valid email address to unlock the full report.')
      return
    }
    if (!submissionId) {
      setStatus('error')
      setErrorMessage("We couldn't link this check to your email. Refresh and try again.")
      return
    }

    setStatus('submitting')
    try {
      await submitLead(submissionId, trimmed)
      setStatus('success')
      onUnlock()
    } catch (err) {
      setStatus('error')
      setErrorMessage(
        err instanceof Error
          ? err.message
          : "We couldn't unlock the report. Try again.",
      )
    }
  }

  const invalid = status === 'error' && errorMessage !== null

  return (
    <section
      aria-labelledby="email-gate-heading"
      className="rounded-xl border border-surface-border bg-surface-muted p-6"
    >
      <h3
        id="email-gate-heading"
        className="text-lg font-semibold text-surface-foreground"
      >
        See every answer
      </h3>
      <p className="mt-1 text-sm text-surface-subtle">
        {hiddenCount === 1
          ? '1 more answer is waiting. Enter your email to reveal it.'
          : `${hiddenCount} more answers are waiting. Enter your email to reveal them all.`}
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-4 space-y-3">
        <div className="space-y-1.5">
          <label
            htmlFor="email-gate-input"
            className="block text-sm font-medium text-surface-foreground"
          >
            Work email
          </label>
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              id="email-gate-input"
              name="email"
              type="email"
              inputMode="email"
              autoComplete="email"
              placeholder="you@company.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              disabled={status === 'submitting'}
              aria-invalid={invalid ? true : undefined}
              aria-describedby={invalid ? ERROR_ID : undefined}
              className="min-h-[40px] w-full rounded-lg border border-surface-subtle bg-white px-4 py-2.5 text-base text-surface-foreground placeholder:text-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50 sm:flex-1"
            />
            <Button
              type="submit"
              size="sm"
              loading={status === 'submitting'}
              className="shrink-0"
            >
              Unlock full report
            </Button>
          </div>
        </div>

        <p className="text-xs text-surface-subtle">
          We&apos;ll email you this report and occasional product updates. No spam;
          unsubscribe anytime.
        </p>

        {invalid ? (
          <p id={ERROR_ID} role="alert" className="text-sm text-danger">
            {errorMessage}
          </p>
        ) : null}

        {/* Polite live region so a screen reader hears the unlock succeed
            (brandkit v2 §7). Kept mounted so the announcement is registered. */}
        <p id={STATUS_ID} aria-live="polite" className="sr-only">
          {status === 'success' ? 'Email saved. The full report is unlocked.' : ''}
        </p>
      </form>
    </section>
  )
}
