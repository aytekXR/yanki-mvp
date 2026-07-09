import { test, expect } from '@playwright/test'

// Runs only when E2E_BASE_URL points at a live stack (DRY_RUN backend + web).
// Skipped otherwise so CI and local `npm test` stay green with no services up.
const baseURL = process.env.E2E_BASE_URL
const scenario = baseURL ? test : test.skip

scenario('submits a URL and renders a GEO score', async ({ page }) => {
  await page.goto('/')

  await page.getByLabel(/url/i).fill('https://example.com')
  await page.getByRole('button', { name: /run analysis/i }).click()

  // The pipeline runs the six steps; give it a generous window.
  const gauge = page.getByRole('img', { name: /GEO score/i })
  await expect(gauge).toBeVisible({ timeout: 180_000 })

  // A percentage is rendered on the results screen.
  await expect(page.getByText(/%/).first()).toBeVisible()
})
