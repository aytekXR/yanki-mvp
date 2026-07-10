import { scoreBand } from '@/lib/score'
import type { ScoreBand } from '@/lib/score'

interface ScoreGaugeProps {
  // GEO score as a whole-number percentage, 0–100.
  score: number
  footprintCount: number
  totalResponses: number
}

// Full literal class names so Tailwind's content scanner keeps them.
const BAND_CLASSES: Record<ScoreBand, { text: string; stroke: string }> = {
  danger: { text: 'text-danger', stroke: 'stroke-danger' },
  warning: { text: 'text-warning', stroke: 'stroke-warning' },
  success: { text: 'text-success', stroke: 'stroke-success' },
}

const RADIUS = 80
const CENTER_X = 100
const BASELINE_Y = 100
const ARC_LENGTH = Math.PI * RADIUS // length of a semicircle
// Semicircle from the left baseline over the top to the right baseline.
const ARC_PATH = `M ${CENTER_X - RADIUS} ${BASELINE_Y} A ${RADIUS} ${RADIUS} 0 0 1 ${
  CENTER_X + RADIUS
} ${BASELINE_Y}`

export default function ScoreGauge({
  score,
  footprintCount,
  totalResponses,
}: ScoreGaugeProps) {
  const percent = Math.max(0, Math.min(100, Math.round(score)))
  const band = scoreBand(percent)
  const colors = BAND_CLASSES[band]
  const dashOffset = ARC_LENGTH * (1 - percent / 100)

  const label = `GEO score ${percent} percent, mentioned in ${footprintCount} of ${totalResponses} answers.`

  return (
    <figure className="flex flex-col items-center">
      <svg
        role="img"
        aria-label={label}
        viewBox="0 0 200 120"
        className={`w-64 max-w-full ${colors.text}`}
      >
        <path
          d={ARC_PATH}
          fill="none"
          className="stroke-surface-border"
          strokeWidth={14}
          strokeLinecap="round"
        />
        <path
          d={ARC_PATH}
          fill="none"
          className={`${colors.stroke} motion-safe:transition-[stroke-dashoffset] motion-safe:duration-700`}
          strokeWidth={14}
          strokeLinecap="round"
          strokeDasharray={ARC_LENGTH}
          strokeDashoffset={dashOffset}
        />
        <text
          x={CENTER_X}
          y={BASELINE_Y - 8}
          textAnchor="middle"
          className="fill-surface-foreground text-4xl font-bold"
        >
          {percent}%
        </text>
      </svg>
      <figcaption className="mt-2 text-sm text-surface-subtle">
        GEO score — mentioned in {footprintCount} of {totalResponses} answers.
      </figcaption>
    </figure>
  )
}
