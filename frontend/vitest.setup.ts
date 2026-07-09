import '@testing-library/jest-dom/vitest'
import * as axeMatchers from 'vitest-axe/matchers'
import { afterEach, expect } from 'vitest'
import { cleanup } from '@testing-library/react'

// vitest-axe ships the matcher but does not self-register it, so wire it up.
expect.extend(axeMatchers)

// We do not enable vitest globals, so register cleanup explicitly.
afterEach(() => {
  cleanup()
})
