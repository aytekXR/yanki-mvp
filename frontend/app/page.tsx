import UrlForm from '@/components/UrlForm'
import WaitlistForm from '@/components/WaitlistForm'

const STEPS = [
  {
    title: 'Discover',
    body: 'We read your site and build a structured company profile.',
  },
  {
    title: 'Ask the engines',
    body: 'We run generated prompts across multiple AI models.',
  },
  {
    title: 'Score',
    body: 'We count how often you show up and turn it into a GEO score.',
  },
]

export default function HomePage() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-16 sm:px-8">
      <section className="space-y-6">
        <h1 className="text-5xl font-semibold tracking-tight text-surface-foreground">
          See how AI answers talk about your brand.
        </h1>
        <p className="max-w-2xl text-base text-surface-subtle">
          Enter your company URL. We ask the AI engines what they say about you and
          measure how often you show up — with every raw answer one click away.
        </p>
        <UrlForm />
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

      <WaitlistForm />
    </main>
  )
}
