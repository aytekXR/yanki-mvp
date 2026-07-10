import type { AnalysisStatus, PipelineStep } from '@/lib/contracts'

type StepState = 'done' | 'active' | 'pending'

interface StepDef {
  key: PipelineStep
  label: string
  // The `progress` value the backend sets once this step COMPLETES (SPEC).
  threshold: number
}

const STEPS: StepDef[] = [
  { key: 'discovery', label: 'Discovery', threshold: 15 },
  { key: 'kyc', label: 'KYC', threshold: 30 },
  { key: 'prompts', label: 'Prompts', threshold: 45 },
  { key: 'execute', label: 'Executing', threshold: 80 },
  { key: 'footprint', label: 'Footprint', threshold: 90 },
  { key: 'scoring', label: 'Scoring', threshold: 100 },
]

const STATE_WORD: Record<StepState, string> = {
  done: 'completed',
  active: 'in progress',
  pending: 'waiting',
}

interface StepProgressProps {
  status: AnalysisStatus
  progress: number
  currentStep: PipelineStep | null
}

export default function StepProgress({
  status,
  progress,
  currentStep,
}: StepProgressProps) {
  const firstPendingIndex = STEPS.findIndex((step) => progress < step.threshold)

  function stateFor(step: StepDef, index: number): StepState {
    if (progress >= step.threshold) return 'done'
    if (status === 'running') {
      if (currentStep === step.key) return 'active'
      if (currentStep === null && index === firstPendingIndex) return 'active'
    }
    return 'pending'
  }

  const activeStep = STEPS.find((step, index) => stateFor(step, index) === 'active')
  const statusText =
    status === 'queued'
      ? 'Queued — starting soon.'
      : `Analyzing… this takes a few minutes.${
          activeStep ? ` Step: ${activeStep.label}.` : ''
        }`

  return (
    <div className="space-y-6">
      <ol className="space-y-3">
        {STEPS.map((step, index) => {
          const state = stateFor(step, index)
          return (
            <li key={step.key} className="flex items-center gap-3">
              <span className={dotClass(state)} aria-hidden="true">
                {state === 'done' ? '✓' : index + 1}
              </span>
              <span className={labelClass(state)}>{step.label}</span>
              <span className="sr-only">{STATE_WORD[state]}</span>
            </li>
          )
        })}
      </ol>

      <div
        role="progressbar"
        aria-label="Analysis progress"
        aria-valuenow={progress}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-2 w-full overflow-hidden rounded-full bg-surface-border"
      >
        <div
          className="h-full rounded-full bg-primary motion-safe:transition-[width] motion-safe:duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <p aria-live="polite" className="text-sm text-surface-subtle">
        {statusText}
      </p>
    </div>
  )
}

function dotClass(state: StepState): string {
  const base =
    'flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-medium'
  if (state === 'done') return `${base} bg-success-soft text-success-strong`
  if (state === 'active') return `${base} bg-primary text-white motion-safe:animate-pulse-ring`
  return `${base} border border-surface-border bg-surface-muted text-surface-subtle`
}

function labelClass(state: StepState): string {
  if (state === 'done') return 'text-sm font-medium text-surface-foreground'
  if (state === 'active') return 'text-sm font-semibold text-primary'
  return 'text-sm text-surface-subtle'
}
