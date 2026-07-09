import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StepProgress from '@/components/StepProgress'
import { axeCheck } from './a11y'

describe('StepProgress accessibility', () => {
  it('has no axe violations while running with an active step', async () => {
    const { container } = render(
      <main>
        <StepProgress status="running" progress={30} currentStep="prompts" />
      </main>,
    )
    // Covers the progressbar role + aria-valuenow and the aria-live status line.
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '30')
    expect(await axeCheck(container)).toHaveNoViolations()
  })

  it('has no axe violations while queued', async () => {
    const { container } = render(
      <main>
        <StepProgress status="queued" progress={0} currentStep={null} />
      </main>,
    )
    expect(await axeCheck(container)).toHaveNoViolations()
  })
})
