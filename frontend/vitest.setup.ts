import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// We do not enable vitest globals, so register cleanup explicitly.
afterEach(() => {
  cleanup()
})
