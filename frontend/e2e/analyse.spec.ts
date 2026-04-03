import { test, expect } from '@playwright/test'
import { APP_BASE, authenticateAndGoTo } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'
import { mockStudentsProgression } from './helpers/mock-data.js'

test.describe('Analyse des Travaux (/analyse)', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/analyse')
  })

  // ──────────────────────────────────────────────────────────────
  // Rendering
  // ──────────────────────────────────────────────────────────────
  test.describe('Rendering', () => {
    test('renders the page heading', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('Analyse des travaux')
    })

    test('shows the "Retour" button', async ({ page }) => {
      await expect(page.locator('button', { hasText: '← Retour' })).toBeVisible()
    })

    test('displays four KPI cards', async ({ page }) => {
      await expect(page.locator('.kpi-card')).toHaveCount(4)
    })
  })

  // ──────────────────────────────────────────────────────────────
  // KPI computations
  // ──────────────────────────────────────────────────────────────
  test.describe('KPI values', () => {
    test('shows correct total students count', async ({ page }) => {
      await expect(page.locator('.kpi-value').first()).toContainText(
        String(mockStudentsProgression.length),
      )
    })

    test('shows computed average initial score', async ({ page }) => {
      // mock initial scores: 8.5 (only Alice has one, Bob is null)
      // avg = 8.5 / 1 = 8.5
      await expect(page.locator('.kpi-value', { hasText: '8.5' })).toBeVisible()
    })

    test('shows "Non passée" for students without initial score', async ({ page }) => {
      await expect(page.locator('td', { hasText: 'Non passée' })).toBeVisible()
    })

    test('shows progress value for students with both scores', async ({ page }) => {
      // Alice has progress = -4.5
      await expect(page.locator('.badge-progress', { hasText: '-4.5' })).toBeVisible()
    })

    test('shows "–" for students without progress', async ({ page }) => {
      // Bob has null progress
      await expect(page.locator('td', { hasText: '-' })).toHaveCount(1)
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Table
  // ──────────────────────────────────────────────────────────────
  test.describe('Table', () => {
    test('renders table with correct headers', async ({ page }) => {
      await expect(page.locator('th', { hasText: 'Étudiant' })).toBeVisible()
      await expect(page.locator('th', { hasText: 'Groupe' })).toBeVisible()
      await expect(page.locator('th', { hasText: 'Dictée Initiale' })).toBeVisible()
      await expect(page.locator('th', { hasText: 'Dictée Finale' })).toBeVisible()
      await expect(page.locator('th', { hasText: 'Évolution' })).toBeVisible()
    })

    test('renders one row per student in mock data', async ({ page }) => {
      await expect(page.locator('tbody tr')).toHaveCount(mockStudentsProgression.length)
    })

    test('displays student name in the first column', async ({ page }) => {
      await expect(page.locator('tbody tr').first()).toContainText('DUPONT')
    })

    test('shows group badge in the second column', async ({ page }) => {
      await expect(page.locator('.badge-group').first()).toContainText('G1')
    })

    test('negative progress badge has green (success) class', async ({ page }) => {
      // Alice: progress = -4.5 → amélioration → badge-progress.bg-success
      await expect(page.locator('.badge-progress.bg-success')).toHaveCount(1)
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Search
  // ──────────────────────────────────────────────────────────────
  test.describe('Search', () => {
    test('search input is visible', async ({ page }) => {
      await expect(page.locator('.search-box input')).toBeVisible()
    })

    test('filtering by name reduces visible rows', async ({ page }) => {
      await page.fill('.search-box input', 'DUPONT')
      await expect(page.locator('tbody tr')).toHaveCount(1)
    })

    test('filtering by group name', async ({ page }) => {
      await page.fill('.search-box input', 'G1')
      await expect(page.locator('tbody tr')).toHaveCount(1)
    })

    test('shows empty state message when no results', async ({ page }) => {
      await page.fill('.search-box input', 'XXXXXXXXXXXXXXX')
      await expect(page.locator('.empty-state')).toBeVisible()
    })

    test('clearing search restores all rows', async ({ page }) => {
      await page.fill('.search-box input', 'DUPONT')
      await page.fill('.search-box input', '')
      await expect(page.locator('tbody tr')).toHaveCount(mockStudentsProgression.length)
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Loading state
  // ──────────────────────────────────────────────────────────────
  test.describe('Loading state', () => {
    test('shows loading indicator while fetching progression data', async ({ page }) => {
      await page.route('**/api/students/stats/progression', async (route) => {
        await new Promise((r) => setTimeout(r, 500))
        await route.fulfill({ json: [] })
      })
      const gotoPromise = page.goto(`${APP_BASE}/analyse`)
      await expect(page.locator('.loading-container, .loading-content')).toBeVisible()
      await gotoPromise
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Navigation
  // ──────────────────────────────────────────────────────────────
  test.describe('Navigation', () => {
    test('"Retour" button navigates to /gestion', async ({ page }) => {
      await page.locator('button', { hasText: '← Retour' }).click()
      await expect(page).toHaveURL(new RegExp(`${APP_BASE}/gestion`))
    })
  })
})
