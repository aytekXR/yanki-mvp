import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import KycCard from '@/components/KycCard'
import type { KYC } from '@/lib/contracts'
import { axeCheck } from './a11y'

const fullKyc: KYC = {
  company: 'Acme Analytics',
  description: 'Acme builds analytics tools for small, fast-moving teams.',
  industry: 'Business intelligence software',
  aliases: ['Acme', 'Acme Inc'],
  products: ['Dashboards', 'Reports'],
  services: ['Onboarding', 'Support'],
  keywords: ['analytics', 'CRM'],
  locations: ['San Francisco', 'Berlin'],
  competitors: ['Globex', 'Initech'],
}

const partialKyc: KYC = {
  company: 'Solo Co',
  description: 'A one-line company with no other details.',
  industry: '',
  aliases: [],
  products: [],
  services: [],
  keywords: [],
  locations: [],
  competitors: [],
}

describe('KycCard accessibility', () => {
  it('has no axe violations for a full profile', async () => {
    const { container } = render(
      <main>
        <KycCard kyc={fullKyc} />
      </main>,
    )
    expect(await axeCheck(container)).toHaveNoViolations()
  })

  it('has no axe violations for a partial profile with omitted rows', async () => {
    const { container } = render(
      <main>
        <KycCard kyc={partialKyc} />
      </main>,
    )
    expect(await axeCheck(container)).toHaveNoViolations()
  })
})
