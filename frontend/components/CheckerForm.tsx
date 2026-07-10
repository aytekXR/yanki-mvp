'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import Button from '@/components/Button'
import { createCheckerAnalysis } from '@/lib/api'

const ERROR_ID = 'checker-error'

type ErrorField = 'brand' | 'category' | 'form'

// A usable brand carries at least one letter or digit; reject symbol- or
// whitespace-only input client-side so no submit fires (mirrors the backend's
// non-blank rule while catching junk like "!!!").
function looksLikeBrand(value: string): boolean {
  return /[\p{L}\p{N}]/u.test(value)
}

export default function CheckerForm() {
  const router = useRouter()
  const [brand, setBrand] = useState('')
  const [category, setCategory] = useState('')
  const [error, setError] = useState<{ message: string; field: ErrorField } | null>(
    null,
  )
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    const trimmedBrand = brand.trim()
    const trimmedCategory = category.trim()
    if (!trimmedBrand) {
      setError({ message: 'Enter a brand to check.', field: 'brand' })
      return
    }
    if (!looksLikeBrand(trimmedBrand)) {
      setError({ message: 'Enter a valid brand name.', field: 'brand' })
      return
    }
    if (!trimmedCategory) {
      setError({
        message: 'Enter the category your brand competes in.',
        field: 'category',
      })
      return
    }

    setSubmitting(true)
    try {
      const { id, submission_id } = await createCheckerAnalysis(
        trimmedBrand,
        trimmedCategory,
      )
      // Carry submission_id to the results route — P5.5's email gate posts it.
      router.push(`/checker/${id}?submission_id=${submission_id}`)
    } catch (err) {
      setSubmitting(false)
      setError({
        message:
          err instanceof Error
            ? err.message
            : "We couldn't start the check. Try again.",
        field: 'form',
      })
    }
  }

  const inputClass =
    'w-full rounded-lg border border-surface-subtle bg-white px-4 py-3 text-base text-surface-foreground placeholder:text-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50'

  return (
    <form onSubmit={handleSubmit} noValidate className="w-full space-y-4">
      <div className="space-y-1.5">
        <label
          htmlFor="brand"
          className="block text-sm font-medium text-surface-foreground"
        >
          Brand
        </label>
        <input
          id="brand"
          name="brand"
          type="text"
          autoComplete="organization"
          placeholder="Your brand name"
          value={brand}
          onChange={(event) => setBrand(event.target.value)}
          disabled={submitting}
          aria-invalid={error?.field === 'brand' ? true : undefined}
          aria-describedby={error?.field === 'brand' ? ERROR_ID : undefined}
          className={inputClass}
        />
      </div>

      <div className="space-y-1.5">
        <label
          htmlFor="category"
          className="block text-sm font-medium text-surface-foreground"
        >
          Category
        </label>
        <input
          id="category"
          name="category"
          type="text"
          placeholder="e.g. project management software"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          disabled={submitting}
          aria-invalid={error?.field === 'category' ? true : undefined}
          aria-describedby={error?.field === 'category' ? ERROR_ID : undefined}
          className={inputClass}
        />
      </div>

      <Button type="submit" loading={submitting} className="w-full sm:w-auto">
        Check my brand
      </Button>

      {error ? (
        <p id={ERROR_ID} role="alert" className="text-sm text-danger">
          {error.message}
        </p>
      ) : null}
    </form>
  )
}
