import { test, expect } from '@playwright/test'
import { APP_BASE, authenticateAndGoTo } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'

test.describe('ÉMILE Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/emile')
  })

  // ──────────────────────────────────────────────────────────────
  // Page structure
  // ──────────────────────────────────────────────────────────────
  test.describe('Page structure', () => {
    test('renders the page title', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('É.M.I.L.E.')
    })

    test('shows the three KPI cards with correct values', async ({ page }) => {
      await expect(page.locator('.stat-val').first()).toContainText('2')    // total_students
      await expect(page.locator('.stat-val').nth(1)).toContainText('3')    // total_submissions
      await expect(page.locator('.stat-val').nth(2)).toContainText('7.5')  // global_average
    })

    test('renders KPI descriptions', async ({ page }) => {
      await expect(page.locator('.stat-desc', { hasText: 'Étudiants' })).toBeVisible()
      await expect(page.locator('.stat-desc', { hasText: 'Dictées' })).toBeVisible()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Section headings
  // ──────────────────────────────────────────────────────────────
  test.describe('Section headings', () => {
    const sections = [
      'Analyse par Groupe',
      'Analyse Pédagogique',
      "Analyse des Erreurs",
      'Outils & Corrections',
    ]
    for (const section of sections) {
      test(`shows "${section}" section`, async ({ page }) => {
        await expect(page.locator('.section-title', { hasText: section })).toBeVisible()
      })
    }
  })

  // ──────────────────────────────────────────────────────────────
  // Promo distribution filter
  // ──────────────────────────────────────────────────────────────
  test.describe('Promo distribution filter', () => {
    test('promotion selector is populated and selectable', async ({ page }) => {
      const select = page.locator('.select-filter').first()
      await expect(select).toBeVisible()
      await expect(select.locator('option')).toHaveCount(1) // one promo in mock
      await expect(select).toHaveValue('BUT INFO 2024-2025')
    })

    test('mistake filter includes "Vue Globale" option', async ({ page }) => {
      const mistakeFilter = page.locator('.select-filter').last()
      await expect(mistakeFilter.locator('option', { hasText: 'Vue Globale' })).toBeVisible()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Charts
  // ──────────────────────────────────────────────────────────────
  test.describe('Charts', () => {
    test('chart canvas elements are rendered', async ({ page }) => {
      const count = await page.locator('.chart-wrapper canvas').count()
      expect(count).toBeGreaterThan(0)
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Loading & error states
  // ──────────────────────────────────────────────────────────────
  test.describe('Loading state', () => {
    test('shows loading indicator while fetching stats', async ({ page }) => {
      await page.route('**/api/stats/emile', async (route) => {
        await new Promise((r) => setTimeout(r, 500))
        await route.fulfill({ json: {} })
      })
      const gotoPromise = page.goto(`${APP_BASE}/emile`)
      await expect(page.locator('.loading-container, .loading-content')).toBeVisible()
      await gotoPromise
    })

    test('shows empty state when API returns an error', async ({ page }) => {
      await page.route('**/api/stats/emile', (route) =>
        route.fulfill({ status: 500, json: { detail: 'Server error' } }),
      )
      await page.goto(`${APP_BASE}/emile`)
      await expect(page.locator('.empty-state')).toBeVisible()
    })
  })
})
