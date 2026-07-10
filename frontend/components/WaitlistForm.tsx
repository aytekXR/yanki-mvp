'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'
import Button from '@/components/Button'
import { joinWaitlist } from '@/lib/api'

// Mirror the backend's conservative shape check so an invalid address is caught
// client-side and NO request is fired (same regex as api/schemas.py _EMAIL_RE).
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

const ERROR_ID = 'waitlist-error'

type Status = 'idle' | 'submitting' | 'success' | 'error'

export default function WaitlistForm() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage(null)

    const trimmed = email.trim()
    if (!EMAIL_RE.test(trimmed)) {
      // Invalid: inline danger message, no network call.
      setStatus('error')
      setErrorMessage('Enter a valid email address to join the waitlist.')
      return
    }

    setStatus('submitting')
    try {
      await joinWaitlist(trimmed)
      setStatus('success')
      setEmail('')
    } catch (err) {
      setStatus('error')
      setErrorMessage(
        err instanceof Error
          ? err.message
          : "We couldn't add you to the waitlist. Try again.",
      )
    }
  }

  const invalid = status === 'error' && errorMessage !== null

  return (
    <section
      aria-labelledby="waitlist-heading"
      className="mt-16 rounded-xl border border-surface-border bg-surface-muted p-6 sm:p-8"
    >
      <h2
        id="waitlist-heading"
        className="text-xl font-semibold text-surface-foreground"
      >
        Get updates when Yanki launches new features
      </h2>
      <p className="mt-2 max-w-2xl text-sm text-surface-subtle">
        Leave your email and we&apos;ll send you occasional product updates as we
        ship. No score, no report — just what&apos;s new.
      </p>

      {status === 'success' ? (
        <p
          role="status"
          aria-live="polite"
          className="mt-4 rounded-lg bg-success-soft px-4 py-3 text-sm text-success-strong"
        >
          Thanks — you&apos;re on the list. We&apos;ll email you when there&apos;s
          something new.
        </p>
      ) : (
        <form onSubmit={handleSubmit} noValidate className="mt-4 space-y-3">
          <div className="space-y-1.5">
            <label
              htmlFor="waitlist-email"
              className="block text-sm font-medium text-surface-foreground"
            >
              Email address
            </label>
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                id="waitlist-email"
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
                loading={status === 'submitting'}
                className="shrink-0"
              >
                Join waitlist
              </Button>
            </div>
          </div>

          <p className="text-xs text-surface-subtle">
            You&apos;re joining a product-updates waitlist. Unsubscribe anytime.
          </p>

          {invalid ? (
            <p id={ERROR_ID} role="alert" className="text-sm text-danger">
              {errorMessage}
            </p>
          ) : null}
        </form>
      )}
    </section>
  )
}
