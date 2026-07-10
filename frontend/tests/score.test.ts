import { describe, it, expect } from 'vitest'
import { scoreBand } from '@/lib/score'

describe('scoreBand', () => {
  it('returns danger below 30', () => {
    expect(scoreBand(0)).toBe('danger')
    expect(scoreBand(15)).toBe('danger')
    expect(scoreBand(29)).toBe('danger')
  })

  it('returns warning between 30 and 59', () => {
    expect(scoreBand(30)).toBe('warning')
    expect(scoreBand(45)).toBe('warning')
    expect(scoreBand(59)).toBe('warning')
  })

  it('returns success at 60 and above', () => {
    expect(scoreBand(60)).toBe('success')
    expect(scoreBand(85)).toBe('success')
    expect(scoreBand(100)).toBe('success')
  })
})
