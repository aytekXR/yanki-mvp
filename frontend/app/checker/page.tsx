import Link from 'next/link'
import CheckerForm from '@/components/CheckerForm'

const STEPS = [
  {
    title: 'Name your brand',
    body: 'Tell us your brand and the category you compete in.',
  },
  {
    title: 'Ask the engines',
    body: 'We ask the AI engines what they recommend in your category.',
  },
  {
    title: 'See where you land',
    body: 'Get a score, per-engine presence, and the competitors that showed up.',
  },
]

export default function CheckerPage() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-16 sm:px-8">
      <section className="space-y-6">
        <h1 className="text-5xl font-semibold tracking-tight text-surface-foreground">
          Is your brand showing up in AI answers?
        </h1>
        <p className="max-w-2xl text-base text-surface-subtle">
          Enter your brand and category. We ask the AI engines what they recommend
          and measure how often you show up — with every raw answer behind the
          score. It&rsquo;s free.
        </p>
        <div className="max-w-xl">
          <CheckerForm />
        </div>
        <p className="text-sm text-surface-subtle">
          Curious how we score it?{' '}
          <Link
            href="/methodology"
            className="font-medium text-primary hover:text-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            See our methodology
          </Link>
          .
        </p>
      </section>

      <section className="mt-16 grid gap-6 sm:grid-cols-3" aria-label="How it works">
        {STEPS.map((step, index) => (
          <div
            key={step.title}
            className="rounded-xl border border-surface-border bg-white p-6 shadow-sm"
          >
            <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-full bg-primary-soft text-xs font-medium text-primary-strong">
              {index + 1}
            </div>
            <h2 className="text-xl font-semibold text-surface-foreground">
              {step.title}
            </h2>
            <p className="mt-1 text-sm text-surface-subtle">{step.body}</p>
          </div>
        ))}
      </section>
    </main>
  )
}
