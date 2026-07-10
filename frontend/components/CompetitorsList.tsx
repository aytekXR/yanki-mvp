import type { CompetitorMention } from '@/lib/contracts'

interface CompetitorsListProps {
  competitors: CompetitorMention[]
}

// Competitor brands the answers named (proper-noun co-mentions, not the KYC
// list). Each chip pairs the name with its mention count — never color-only.
export default function CompetitorsList({ competitors }: CompetitorsListProps) {
  return (
    <section className="space-y-3" aria-labelledby="competitors-heading">
      <h2
        id="competitors-heading"
        className="text-xl font-semibold text-surface-foreground"
      >
        Competitors that showed up
      </h2>
      {competitors.length > 0 ? (
        <ul className="flex flex-wrap gap-2">
          {competitors.map((competitor) => (
            <li
              key={competitor.name}
              className="inline-flex items-center gap-2 rounded-full bg-primary-soft px-3 py-1.5 text-sm text-primary-strong"
            >
              <span className="font-medium">{competitor.name}</span>
              <span className="inline-flex items-center rounded-full bg-white px-1.5 py-0.5 text-xs font-medium text-primary-strong">
                {competitor.mentions}
              </span>
              <span className="sr-only">
                mentioned in {competitor.mentions} answers
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-surface-subtle">
          No competitor brands were named in these answers.
        </p>
      )}
    </section>
  )
}
