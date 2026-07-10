import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { axeCheck } from './a11y'

vi.mock('@/lib/api', () => ({
  joinWaitlist: vi.fn(),
}))

import WaitlistForm from '@/components/WaitlistForm'
import { joinWaitlist } from '@/lib/api'

const mockedJoin = vi.mocked(joinWaitlist)

describe('WaitlistForm accessibility', () => {
  beforeEach(() => {
    mockedJoin.mockReset()
  })

  it('has a labelled email input and a named submit button', () => {
    render(
      <main>
        <WaitlistForm />
      </main>,
    )
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /join waitlist/i }),
    ).toBeInTheDocument()
  })

  it('has no axe violations in its idle state', async () => {
    const { container } = render(
      <main>
        <WaitlistForm />
      </main>,
    )
    expect(await axeCheck(container)).toHaveNoViolations()
  })

  it('has no axe violations while showing an invalid-email error', async () => {
    const user = userEvent.setup()
    const { container } = render(
      <main>
        <WaitlistForm />
      </main>,
    )
    await user.type(screen.getByLabelText(/email/i), 'nope')
    await user.click(screen.getByRole('button', { name: /join waitlist/i }))

    const error = await screen.findByRole('alert')
    // The input names its error via aria-describedby (never color-only).
    expect(screen.getByLabelText(/email/i)).toHaveAttribute(
      'aria-describedby',
      error.id,
    )
    expect(screen.getByLabelText(/email/i)).toHaveAttribute('aria-invalid', 'true')
    expect(await axeCheck(container)).toHaveNoViolations()
  })

  it('is keyboard operable from input to submit', async () => {
    const user = userEvent.setup()
    mockedJoin.mockResolvedValue({ ok: true })
    render(
      <main>
        <WaitlistForm />
      </main>,
    )

    await user.tab()
    expect(screen.getByLabelText(/email/i)).toHaveFocus()
    await user.keyboard('reader@example.com')
    await user.tab()
    expect(screen.getByRole('button', { name: /join waitlist/i })).toHaveFocus()
    await user.keyboard('{Enter}')

    await waitFor(() =>
      expect(mockedJoin).toHaveBeenCalledWith('reader@example.com'),
    )
  })

  it('has no axe violations in the success confirmation state', async () => {
    const user = userEvent.setup()
    mockedJoin.mockResolvedValue({ ok: true })
    const { container } = render(
      <main>
        <WaitlistForm />
      </main>,
    )
    await user.type(screen.getByLabelText(/email/i), 'reader@example.com')
    await user.click(screen.getByRole('button', { name: /join waitlist/i }))

    await screen.findByText(/you're on the list/i)
    expect(await axeCheck(container)).toHaveNoViolations()
  })
})
