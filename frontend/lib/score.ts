export type ScoreBand = 'danger' | 'warning' | 'success'

// GEO score bands from brandkit v2 §2 (score is a percentage, 0–100):
// 0–29 danger, 30–59 warning (v1 used primary; v2 makes the mid band
// semantic), 60–100 success. Always paired with the numeric percentage.
export function scoreBand(score: number): ScoreBand {
  if (score < 30) return 'danger'
  if (score < 60) return 'warning'
  return 'success'
}
