import type { AnalysisResponse, Prompt } from '@/lib/contracts'

interface ResultsTableProps {
  responses: AnalysisResponse[]
  prompts: Prompt[]
}

export default function ResultsTable({ responses, prompts }: ResultsTableProps) {
  const promptText = new Map(prompts.map((prompt) => [prompt.id, prompt.text]))

  return (
    <div className="overflow-x-auto rounded-lg border border-surface-border">
      <table className="w-full min-w-[640px] border-collapse text-left text-sm">
        <thead>
          <tr className="bg-surface-muted text-xs font-medium uppercase tracking-wide text-surface-subtle">
            <th scope="col" className="px-4 py-3">
              Engine
            </th>
            <th scope="col" className="px-4 py-3">
              Model
            </th>
            <th scope="col" className="px-4 py-3">
              Footprint
            </th>
            <th scope="col" className="px-4 py-3">
              Matched snippet
            </th>
            <th scope="col" className="px-4 py-3">
              Prompt
            </th>
          </tr>
        </thead>
        <tbody>
          {responses.map((response, index) => (
            <tr
              key={response.id}
              className={index % 2 === 1 ? 'bg-surface-muted' : 'bg-white'}
            >
              <td className="px-4 py-3 font-medium text-surface-foreground">
                {response.engine}
              </td>
              <td className="px-4 py-3 text-surface-subtle">{response.model}</td>
              <td className="px-4 py-3">
                <FootprintBadge value={response.footprint} />
              </td>
              <td className="max-w-xs px-4 py-3">
                {response.matched_snippet ? (
                  <span
                    className="block truncate font-mono text-xs text-surface-foreground"
                    title={response.matched_snippet}
                  >
                    {response.matched_snippet}
                  </span>
                ) : (
                  <span className="text-xs text-surface-subtle">
                    Not mentioned in this answer.
                  </span>
                )}
              </td>
              <td className="max-w-xs px-4 py-3">
                <span
                  className="block truncate text-surface-subtle"
                  title={promptText.get(response.prompt_id) ?? ''}
                >
                  {promptText.get(response.prompt_id) ?? '—'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function FootprintBadge({ value }: { value: boolean | null }) {
  if (value) {
    return (
      <span className="inline-flex items-center rounded-full bg-success-soft px-2 py-1 text-xs font-medium text-success-700">
        Yes
      </span>
    )
  }
  return (
    <span className="inline-flex items-center rounded-full bg-danger-soft px-2 py-1 text-xs font-medium text-danger-700">
      No
    </span>
  )
}
