import type { Page } from '@playwright/test'

/** Base path matching vite.config.ts `base: '/rousseau/'` */
export const APP_BASE = ''

/** A fake but structurally-valid JWT token for bypassing route guards */
export const TEST_TOKEN = 'e2e-test-access-token'

/**
 * Inject the auth token into localStorage BEFORE the page loads (addInitScript),
 * so the Vue Router guard sees it immediately and doesn't redirect to /login.
 */
export async function authenticate(page: Page): Promise<void> {
  await page.addInitScript((token: string) => {
    localStorage.setItem('access_token', token)
  }, TEST_TOKEN)
}

/** Remove the token (useful to test unauthenticated states) */
export async function clearAuthentication(page: Page): Promise<void> {
  await page.evaluate(() => localStorage.removeItem('access_token'))
}

/** Navigate to a path relative to the app base */
export async function goTo(page: Page, path: string): Promise<void> {
  await page.goto(`${APP_BASE}${path}`)
}

/**
 * Authenticate then navigate. The most common pattern for tests that
 * skip the login page and go straight to a feature.
 */
export async function authenticateAndGoTo(page: Page, path: string): Promise<void> {
  await authenticate(page)
  await page.goto(`${APP_BASE}${path}`)
}
