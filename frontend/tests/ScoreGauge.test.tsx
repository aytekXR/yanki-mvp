import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ScoreGauge from '@/components/ScoreGauge'

describe('ScoreGauge', () => {
  it('states the score in words via aria-label', () => {
    render(<ScoreGauge score={45} footprintCount={9} totalResponses={20} />)
    const label = screen.getByRole('img').getAttribute('aria-label') ?? ''
    expect(label).toContain('GEO score')
    expect(label).toContain('45 percent')
    expect(label).toContain('9 of 20')
  })

  it('uses the danger band below 30', () => {
    render(<ScoreGauge score={15} footprintCount={2} totalResponses={20} />)
    expect(screen.getByRole('img')).toHaveClass('text-danger')
  })

  it('uses the primary band between 30 and 59', () => {
    render(<ScoreGauge score={45} footprintCount={9} totalResponses={20} />)
    expect(screen.getByRole('img')).toHaveClass('text-primary')
  })

  it('uses the success band at 60 and above', () => {
    render(<ScoreGauge score={85} footprintCount={17} totalResponses={20} />)
    expect(screen.getByRole('img')).toHaveClass('text-success')
  })
})
