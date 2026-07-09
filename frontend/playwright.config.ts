import { defineConfig } from '@playwright/test'

// Minimal config. The happy-path spec skips itself unless E2E_BASE_URL points at
// a running stack (e.g. http://localhost:8140 with the DRY_RUN backend up).
export default defineConfig({
  testDir: './e2e',
  timeout: 200_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: process.env.E2E_BASE_URL,
  },
})
