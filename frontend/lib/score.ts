export type ScoreBand = 'danger' | 'primary' | 'success'

// GEO score color scale from docs/frontend-brandkit.md §2 (score is a percentage,
// 0–100): 0–29 danger, 30–59 primary, 60–100 success.
export function scoreBand(score: number): ScoreBand {
  if (score < 30) return 'danger'
  if (score < 60) return 'primary'
  return 'success'
}
