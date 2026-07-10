import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MethodologyPage from '@/app/methodology/page'
// Assert against the SAME generated artifact the page renders, never string
// literals: a re-export via `make gen-types` must flow through to the page with
// no test edit. This is the anti-drift guarantee, tested.
import methodology from '../../shared/contracts/checker_methodology.json'

describe('Methodology page', () => {
  it('renders the version stamp from the artifact', () => {
    render(<MethodologyPage />)
    expect(screen.getByText(methodology.version)).toBeInTheDocument()
  })

  it('renders every one of the exact prompts from the artifact', () => {
    render(<MethodologyPage />)
    expect(methodology.prompts.length).toBe(12)
    for (const prompt of methodology.prompts) {
      expect(screen.getByText(prompt.text)).toBeInTheDocument()
    }
  })

  it('renders every engine from the artifact', () => {
    render(<MethodologyPage />)
    expect(methodology.engines).toEqual([
      'anthropic',
      'openai',
      'gemini',
      'perplexity',
    ])
    const list = screen.getByRole('list', { name: /ai engines/i })
    expect(list).toBeInTheDocument()
  })

  it('shows the score formula honestly', () => {
    render(<MethodologyPage />)
    expect(
      screen.getByText(`score = ${methodology.score_formula.expression}`),
    ).toBeInTheDocument()
  })

  it('states the candid caveats', () => {
    render(<MethodologyPage />)
    expect(screen.getByText(/one sample per prompt/i)).toBeInTheDocument()
    expect(screen.getByText(/binary/i)).toBeInTheDocument()
    expect(screen.getByText(/unprompted visibility/i)).toBeInTheDocument()
    expect(screen.getByText(/english only/i)).toBeInTheDocument()
    expect(screen.getByText(/cached for 24 hours/i)).toBeInTheDocument()
  })

  it('links back to the checker', () => {
    render(<MethodologyPage />)
    const link = screen.getByRole('link', { name: /check your brand/i })
    expect(link).toHaveAttribute('href', '/checker')
  })
})
