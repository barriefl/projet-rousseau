import { test, expect } from '@playwright/test'
import { APP_BASE, authenticateAndGoTo } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'

test.describe('Étude Rousseau Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/')
  })

  // ──────────────────────────────────────────────────────────────
  // Page structure
  // ──────────────────────────────────────────────────────────────
  test.describe('Page structure', () => {
    test('renders the page title', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('Étude Rousseau')
    })

    test('shows all four main section headings', async ({ page }) => {
      const sections = ['Hypothèse 1', 'Hypothèse 2', 'Hypothèse 3', 'Hypothèse 4']
      for (const section of sections) {
        await expect(page.locator('.section-title', { hasText: section })).toBeVisible()
      }
    })

    test('shows the regression model section', async ({ page }) => {
      await expect(page.locator('.section-title', { hasText: 'Modèle Prédictif' })).toBeVisible()
    })

    test('shows the ANOVA section', async ({ page }) => {
      await expect(page.locator('.section-title', { hasText: 'Niveau Initial' })).toBeVisible()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Charts
  // ──────────────────────────────────────────────────────────────
  test.describe('Charts', () => {
    test('chart canvas elements are rendered for H1', async ({ page }) => {
      const canvases = await page.locator('.chart-wrapper canvas').count()
      expect(canvases).toBeGreaterThan(0)
    })

    test('H2 statistical verdict box is rendered', async ({ page }) => {
      await expect(page.locator('.statistical-verdict')).toBeVisible()
      // The mock ANOVA is NOT significant
      await expect(page.locator('.verdict-box.neutral')).toBeVisible()
    })

    test('H3 teacher comparison chart container is rendered', async ({ page }) => {
      const h3Section = page.locator('.section-title', { hasText: 'Hypothèse 3' })
      await expect(h3Section).toBeVisible()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // H4 socio-cultural controls
  // ──────────────────────────────────────────────────────────────
  test.describe('H4 controls', () => {
    test('H4 metric checkboxes are visible', async ({ page }) => {
      await expect(page.locator('.h4-controls label', { hasText: 'Score Initial' })).toBeVisible()
      await expect(page.locator('.h4-controls label', { hasText: 'Progression' })).toBeVisible()
    })

    test('sort-by toggle buttons are visible and clickable', async ({ page }) => {
      const sortBtns = page.locator('.btn-toggle-group button')
      await expect(sortBtns).toHaveCount(3)
      await sortBtns.nth(1).click()
      await expect(sortBtns.nth(1)).toHaveClass(/active/)
    })

    test('H4 category selector dropdowns render', async ({ page }) => {
      const selects = page.locator('.socio-select')
      const count = await selects.count()
      expect(count).toBeGreaterThan(0)
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Loading & error states
  // ──────────────────────────────────────────────────────────────
  test.describe('Loading state', () => {
    test('shows a loading indicator while fetching stats', async ({ page }) => {
      // Slow the response so we can observe the spinner
      await page.route('**/api/stats/rousseau', async (route) => {
        await new Promise((r) => setTimeout(r, 500))
        await route.fulfill({ json: {} })
      })

      const gotoPromise = page.goto(`${APP_BASE}/`)
      await expect(page.locator('.loading-container, .loading-content')).toBeVisible()
      await gotoPromise
    })

    test('shows empty state when API returns an error', async ({ page }) => {
      await page.route('**/api/stats/rousseau', (route) =>
        route.fulfill({ status: 500, json: { detail: 'Server error' } }),
      )
      await page.goto(`${APP_BASE}/`)
      await expect(page.locator('.empty-state')).toBeVisible()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Regression model
  // ──────────────────────────────────────────────────────────────
  test.describe('Regression model', () => {
    test('renders R² score badge', async ({ page }) => {
      const r2Badge = page.locator('span', { hasText: 'Score de fiabilité' })
      await expect(r2Badge).toBeVisible()
    })
  })
})
