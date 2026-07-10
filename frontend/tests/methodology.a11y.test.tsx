import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import MethodologyPage from '@/app/methodology/page'
import { axeCheck } from './a11y'

describe('Methodology page accessibility', () => {
  it('has no axe violations', async () => {
    const { container } = render(<MethodologyPage />)
    expect(await axeCheck(container)).toHaveNoViolations()
  })
})
