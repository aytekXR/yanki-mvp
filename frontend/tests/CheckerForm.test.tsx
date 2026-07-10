import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

const push = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('@/lib/api', () => ({
  createCheckerAnalysis: vi.fn(),
}))

import CheckerForm from '@/components/CheckerForm'
import { createCheckerAnalysis } from '@/lib/api'

const mockedCreate = vi.mocked(createCheckerAnalysis)

describe('CheckerForm', () => {
  beforeEach(() => {
    push.mockReset()
    mockedCreate.mockReset()
  })

  it('shows an inline error and does not POST for a blank brand', async () => {
    const user = userEvent.setup()
    render(<CheckerForm />)

    // Fill only the category, leave brand blank, then submit.
    await user.type(screen.getByLabelText(/category/i), 'note taking apps')
    await user.click(screen.getByRole('button', { name: /check my brand/i }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(mockedCreate).not.toHaveBeenCalled()
  })

  it('shows an inline error and does not POST for an invalid brand', async () => {
    const user = userEvent.setup()
    render(<CheckerForm />)

    // Symbol-only brand is rejected client-side.
    await user.type(screen.getByLabelText(/brand/i), '!!!')
    await user.type(screen.getByLabelText(/category/i), 'note taking apps')
    await user.click(screen.getByRole('button', { name: /check my brand/i }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(mockedCreate).not.toHaveBeenCalled()
  })

  it('posts and disables the button for a valid brand and category', async () => {
    const user = userEvent.setup()
    // Never resolves, so the form stays in its submitting (disabled) state.
    mockedCreate.mockReturnValue(
      new Promise<{ id: string; submission_id: string }>(() => {}),
    )
    render(<CheckerForm />)

    await user.type(screen.getByLabelText(/brand/i), 'Notion')
    await user.type(screen.getByLabelText(/category/i), 'note taking apps')
    await user.click(screen.getByRole('button', { name: /check my brand/i }))

    expect(mockedCreate).toHaveBeenCalledWith('Notion', 'note taking apps')
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: /check my brand/i }),
      ).toBeDisabled(),
    )
  })
})
