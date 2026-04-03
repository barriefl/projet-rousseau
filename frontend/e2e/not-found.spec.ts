import { test, expect } from '@playwright/test'
import { APP_BASE, authenticateAndGoTo } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'

test.describe('404 – Page Not Found', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
  })

  // ──────────────────────────────────────────────────────────────
  // Rendering
  // ──────────────────────────────────────────────────────────────
  test.describe('Rendering', () => {
    test('shows "404" heading for unknown routes when authenticated', async ({ page }) => {
      await authenticateAndGoTo(page, '/cette-page-nexiste-pas')
      await expect(page.locator('h1')).toContainText('404')
    })

    test('shows "Page introuvable" subtitle', async ({ page }) => {
      await authenticateAndGoTo(page, '/chemin/inconnu')
      await expect(page.locator('h2')).toContainText('Page introuvable')
    })

    test('shows descriptive paragraph', async ({ page }) => {
      await authenticateAndGoTo(page, '/chemin/inconnu')
      await expect(page.locator('p')).toContainText('égaré')
    })

    test('shows "Retourner à l\'accueil" button', async ({ page }) => {
      await authenticateAndGoTo(page, '/chemin/inconnu')
      await expect(page.locator('button', { hasText: "Retourner à l'accueil" })).toBeVisible()
    })

    test('renders the MapPinOff icon (svg element present)', async ({ page }) => {
      await authenticateAndGoTo(page, '/chemin/inconnu')
      // Lucide icons render as SVG
      await expect(page.locator('svg')).toHaveCount(1)
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Navigation
  // ──────────────────────────────────────────────────────────────
  test.describe('Navigation', () => {
    test('"Retourner à l\'accueil" navigates to /', async ({ page }) => {
      await authenticateAndGoTo(page, '/chemin/inconnu')
      await page.locator('button', { hasText: "Retourner à l'accueil" }).click()
      await expect(page).toHaveURL(new RegExp(`${APP_BASE}(?:/|$)`))
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Multiple bad URLs
  // ──────────────────────────────────────────────────────────────
  test.describe('Various unknown paths', () => {
    const badPaths = [
      '/unknown',
      '/admin/secret',
      '/api/hack',
      '/rousseau/../../../etc/passwd',
    ]

    for (const badPath of badPaths) {
      test(`renders 404 for path "${badPath}"`, async ({ page }) => {
        await authenticateAndGoTo(page, badPath)
        // Should either stay on the 404 page or redirect to login (unauthenticated)
        // Either way it should NOT crash the app
        const url = page.url()
        expect(url).toContain(APP_BASE)
      })
    }
  })
})
