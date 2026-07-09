import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import ScoreGauge from '@/components/ScoreGauge'
import { axeCheck } from './a11y'

describe('ScoreGauge accessibility', () => {
  it('has no axe violations in the danger band', async () => {
    const { container } = render(
      <main>
        <ScoreGauge score={15} footprintCount={2} totalResponses={20} />
      </main>,
    )
    expect(await axeCheck(container)).toHaveNoViolations()
  })

  it('has no axe violations in the primary band', async () => {
    const { container } = render(
      <main>
        <ScoreGauge score={45} footprintCount={9} totalResponses={20} />
      </main>,
    )
    expect(await axeCheck(container)).toHaveNoViolations()
  })

  it('has no axe violations in the success band', async () => {
    const { container } = render(
      <main>
        <ScoreGauge score={85} footprintCount={17} totalResponses={20} />
      </main>,
    )
    expect(await axeCheck(container)).toHaveNoViolations()
  })
})
