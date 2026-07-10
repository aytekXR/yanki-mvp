import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('@/lib/api', () => ({
  joinWaitlist: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number
    constructor(message: string, status: number) {
      super(message)
      this.name = 'ApiError'
      this.status = status
    }
  },
}))

import WaitlistForm from '@/components/WaitlistForm'
import { joinWaitlist, ApiError } from '@/lib/api'

const mockedJoin = vi.mocked(joinWaitlist)

describe('WaitlistForm', () => {
  beforeEach(() => {
    mockedJoin.mockReset()
  })

  it('posts a valid email and shows an inline thank-you confirmation', async () => {
    const user = userEvent.setup()
    mockedJoin.mockResolvedValue({ ok: true })
    render(<WaitlistForm />)

    await user.type(screen.getByLabelText(/email/i), 'reader@example.com')
    await user.click(screen.getByRole('button', { name: /join waitlist/i }))

    await waitFor(() =>
      expect(mockedJoin).toHaveBeenCalledWith('reader@example.com'),
    )
    expect(await screen.findByText(/you're on the list/i)).toBeInTheDocument()
    // The form (and its submit button) is replaced by the confirmation.
    expect(
      screen.queryByRole('button', { name: /join waitlist/i }),
    ).not.toBeInTheDocument()
  })

  it('rejects an invalid email inline without firing a request', async () => {
    const user = userEvent.setup()
    render(<WaitlistForm />)

    await user.type(screen.getByLabelText(/email/i), 'not-an-email')
    await user.click(screen.getByRole('button', { name: /join waitlist/i }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(mockedJoin).not.toHaveBeenCalled()
  })

  it('shows a friendly inline retry message on an API error', async () => {
    const user = userEvent.setup()
    const onError = vi.fn()
    mockedJoin.mockRejectedValue(new ApiError('Server is busy.', 500))
    render(<WaitlistForm />)

    await user.type(screen.getByLabelText(/email/i), 'reader@example.com')
    await user.click(screen.getByRole('button', { name: /join waitlist/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/server is busy/i)
    // The form stays put so the user can retry.
    expect(
      screen.getByRole('button', { name: /join waitlist/i }),
    ).toBeInTheDocument()
    expect(onError).not.toHaveBeenCalled()
  })

  it('trims surrounding whitespace before posting', async () => {
    const user = userEvent.setup()
    mockedJoin.mockResolvedValue({ ok: true })
    render(<WaitlistForm />)

    await user.type(screen.getByLabelText(/email/i), '  reader@example.com  ')
    await user.click(screen.getByRole('button', { name: /join waitlist/i }))

    await waitFor(() =>
      expect(mockedJoin).toHaveBeenCalledWith('reader@example.com'),
    )
  })
})
