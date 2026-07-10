import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { axeCheck } from './a11y'

vi.mock('@/lib/api', () => ({
  submitLead: vi.fn(),
}))

import EmailGate from '@/components/EmailGate'
import { submitLead } from '@/lib/api'

const mockedSubmit = vi.mocked(submitLead)

describe('EmailGate accessibility', () => {
  beforeEach(() => {
    mockedSubmit.mockReset()
  })

  it('has no axe violations in its idle state', async () => {
    const { container } = render(
      <main>
        <EmailGate submissionId="sub-1" hiddenCount={5} onUnlock={vi.fn()} />
      </main>,
    )
    expect(await axeCheck(container)).toHaveNoViolations()
  })

  it('has no axe violations while showing an invalid-email error', async () => {
    const user = userEvent.setup()
    const { container } = render(
      <main>
        <EmailGate submissionId="sub-1" hiddenCount={5} onUnlock={vi.fn()} />
      </main>,
    )
    await user.type(screen.getByLabelText(/email/i), 'nope')
    await user.click(screen.getByRole('button', { name: /unlock full report/i }))

    const error = await screen.findByRole('alert')
    // The input names its error via aria-describedby (never color-only).
    expect(screen.getByLabelText(/email/i)).toHaveAttribute(
      'aria-describedby',
      error.id,
    )
    expect(screen.getByLabelText(/email/i)).toHaveAttribute('aria-invalid', 'true')
    expect(await axeCheck(container)).toHaveNoViolations()
  })
})
