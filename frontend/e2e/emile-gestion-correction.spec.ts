import { test, expect } from '@playwright/test'
import { APP_BASE, authenticateAndGoTo } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'
import { mockStudentsWithScores } from './helpers/mock-data.js'

// ================================================================
// EmileGestionView – /gestion hub
// ================================================================
test.describe('Gestion des Dictées (/gestion)', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/gestion')
  })

  test('renders the page heading', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Gestion des Dictées')
  })

  test('shows three action cards', async ({ page }) => {
    await expect(page.locator('.action-card')).toHaveCount(3)
  })

  test('"Consulter une dictée" card is visible', async ({ page }) => {
    await expect(page.locator('.action-card', { hasText: 'Consulter une dictée' })).toBeVisible()
  })

  test('"Importer une dictée" card is visible', async ({ page }) => {
    await expect(page.locator('.action-card', { hasText: 'Importer une dictée' })).toBeVisible()
  })

  test('"Dictée Référente" card is visible', async ({ page }) => {
    await expect(page.locator('.action-card', { hasText: 'Dictée Référente' })).toBeVisible()
  })

  test('clicking "Consulter" navigates to /correction', async ({ page }) => {
    await page.locator('.action-card', { hasText: 'Consulter' }).click()
    await expect(page).toHaveURL(new RegExp(`${APP_BASE}/correction`))
  })

  test('clicking "Importer" navigates to /import-dictee', async ({ page }) => {
    await page.locator('.action-card', { hasText: 'Importer' }).click()
    await expect(page).toHaveURL(new RegExp(`${APP_BASE}/import-dictee`))
  })

  test('clicking "Dictée Référente" navigates to /dictee-referente', async ({ page }) => {
    await page.locator('.action-card', { hasText: 'Référente' }).click()
    await expect(page).toHaveURL(new RegExp(`${APP_BASE}/dictee-referente`))
  })
})

// ================================================================
// CorrectionView – /correction
// ================================================================
test.describe('Correction (/correction)', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/correction')
  })

  // ── Rendering ─────────────────────────────────────────────────
  test.describe('Rendering', () => {
    test('renders the page heading', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('É.M.I.L.E.')
    })

    test('shows "Retour" button linking back to /gestion', async ({ page }) => {
      await expect(page.locator('button', { hasText: '← Retour' })).toBeVisible()
    })

    test('shows search input', async ({ page }) => {
      await expect(page.locator('.search-input')).toBeVisible()
    })

    test('renders the student card list with mock students', async ({ page }) => {
      await expect(page.locator('.student-card')).toHaveCount(mockStudentsWithScores.length)
    })

    test('student card displays name and score badges', async ({ page }) => {
      const card = page.locator('.student-card').first()
      await expect(card).toContainText('DUPONT')
      await expect(card.locator('.score-badge')).toHaveCount(2)
    })

    test('"I : 8.5" initial score badge is shown', async ({ page }) => {
      await expect(page.locator('.score-badge', { hasText: 'I : 8.5' })).toBeVisible()
    })

    test('"F : -" is shown when final score is null', async ({ page }) => {
      await expect(page.locator('.score-badge', { hasText: 'F : -' })).toBeVisible()
    })
  })

  // ── Search ────────────────────────────────────────────────────
  test.describe('Search', () => {
    test('filters students by last name', async ({ page }) => {
      await page.fill('.search-input', 'DUPONT')
      await expect(page.locator('.student-card')).toHaveCount(1)
      await expect(page.locator('.student-card')).toContainText('DUPONT')
    })

    test('filters students by first name', async ({ page }) => {
      await page.fill('.search-input', 'Bob')
      await expect(page.locator('.student-card')).toHaveCount(1)
      await expect(page.locator('.student-card')).toContainText('MARTIN')
    })

    test('shows no cards when search has no match', async ({ page }) => {
      await page.fill('.search-input', 'XXXXXXXX')
      await expect(page.locator('.student-card')).toHaveCount(0)
    })

    test('clears filter when search input is emptied', async ({ page }) => {
      await page.fill('.search-input', 'DUPONT')
      await page.fill('.search-input', '')
      await expect(page.locator('.student-card')).toHaveCount(mockStudentsWithScores.length)
    })
  })

  // ── Student selection & dictation buttons ─────────────────────
  test.describe('Student selection', () => {
    test('clicking a student card shows submission buttons', async ({ page }) => {
      await page.locator('.student-card').first().click()
      await expect(page.locator('.dictation-selector')).toBeVisible()
    })

    test('selected student card has the "selected" CSS class', async ({ page }) => {
      await page.locator('.student-card').first().click()
      await expect(page.locator('.student-card.selected')).toHaveCount(1)
    })

    test('dictation buttons are displayed after student selection', async ({ page }) => {
      await page.locator('.student-card').first().click()
      await expect(page.locator('.dictation-btn')).toHaveCount(1) // one submission in mock
    })

    test('clicking a dictation button loads the submission detail', async ({ page }) => {
      await page.locator('.student-card').first().click()
      await page.locator('.dictation-btn').first().click()
      // The correction panel should appear
      await expect(page.locator('.atelier-container')).toBeVisible()
    })

    test('html correction text is rendered in the text editor', async ({ page }) => {
      await page.locator('.student-card').first().click()
      await page.locator('.dictation-btn').first().click()
      await expect(page.locator('.text-editor')).toBeVisible()
      await expect(page.locator('.content-html')).toBeVisible()
    })

    test('score display panel shows the final score', async ({ page }) => {
      await page.locator('.student-card').first().click()
      await page.locator('.dictation-btn').first().click()
      await expect(page.locator('.score-display span')).toContainText('8.5')
    })

    test('scores breakdown is shown in the side panel', async ({ page }) => {
      await page.locator('.student-card').first().click()
      await page.locator('.dictation-btn').first().click()
      await expect(page.locator('.panel', { hasText: 'Grammaire' })).toBeVisible()
    })

    test('mistakes list is rendered', async ({ page }) => {
      await page.locator('.student-card').first().click()
      await page.locator('.dictation-btn').first().click()
      await expect(page.locator('.error-item')).toHaveCount(1)
    })
  })

  // ── Navigation ────────────────────────────────────────────────
  test.describe('Navigation', () => {
    test('"Retour" button navigates back to /gestion', async ({ page }) => {
      await page.locator('button', { hasText: '← Retour' }).click()
      await expect(page).toHaveURL(new RegExp(`${APP_BASE}/gestion`))
    })
  })

  // ── Loading state ──────────────────────────────────────────────
  test.describe('Loading states', () => {
    test('shows loading indicator while fetching students', async ({ page }) => {
      await page.route('**/api/students/with-scores', async (route) => {
        await new Promise((r) => setTimeout(r, 500))
        await route.fulfill({ json: [] })
      })
      const gotoPromise = page.goto(`${APP_BASE}/correction`)
      await expect(page.locator('.loading-container, .loading-content')).toBeVisible()
      await gotoPromise
    })

    test('shows empty state when no students are returned', async ({ page }) => {
      await setupApiMocks(page, { studentsWithScores: [] })
      await page.goto(`${APP_BASE}/correction`)
      await expect(page.locator('.empty-state')).toBeVisible()
    })
  })
})
