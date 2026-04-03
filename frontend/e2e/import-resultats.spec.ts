import { test, expect } from '@playwright/test'
import { APP_BASE, authenticateAndGoTo } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'

test.describe('Importation des Résultats (/import-resultats)', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/import-resultats')
  })

  // ──────────────────────────────────────────────────────────────
  // Rendering
  // ──────────────────────────────────────────────────────────────
  test.describe('Rendering', () => {
    test('renders the page heading', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('Importation des Résultats')
    })

    test('shows "Retour" button', async ({ page }) => {
      await expect(page.locator('button', { hasText: '← Retour' })).toBeVisible()
    })

    test('shows step 1 panel', async ({ page }) => {
      await expect(page.locator('.step-title', { hasText: '1.' })).toBeVisible()
    })

    test('shows three configuration selectors', async ({ page }) => {
      await expect(page.locator('.form-grid .action-select')).toHaveCount(3)
    })

    test('promotion selector has mock promotions', async ({ page }) => {
      const select = page.locator('.form-grid .action-select').first()
      await expect(select.locator('option', { hasText: 'BUT INFO 2024-2025' })).toBeAttached()
    })

    test('tool selector has mock tools', async ({ page }) => {
      const select = page.locator('.form-grid .action-select').nth(1)
      await expect(select.locator('option', { hasText: 'Projet Voltaire' })).toBeAttached()
    })

    test('type selector has Initiale / Finale options', async ({ page }) => {
      const select = page.locator('.form-grid .action-select').nth(2)
      await expect(select.locator('option', { hasText: 'Initiale' })).toBeAttached()
      await expect(select.locator('option', { hasText: 'Finale' })).toBeAttached()
    })

    test('"Analyser" button is disabled until all fields are filled', async ({ page }) => {
      await expect(page.locator('button', { hasText: 'Analyser' })).toBeDisabled()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Step 2 – Preview after analysis
  // ──────────────────────────────────────────────────────────────
  test.describe('Step 2 – Preview', () => {
    async function goToStep2(page: import('@playwright/test').Page) {
      await page.locator('.form-grid .action-select').first().selectOption({ index: 1 })
      await page.locator('.form-grid .action-select').nth(1).selectOption({ index: 1 })
      await page.locator('.form-grid .action-select').nth(2).selectOption({ index: 1 })

      await page.locator('input[type="file"]').setInputFiles({
        name: 'resultats.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from('Nom;Prénom;Score évaluation initiale\nDUPONT;Alice;72'),
      })

      await page.locator('button', { hasText: 'Analyser' }).click()
      await expect(page.locator('.step-title', { hasText: '2.' })).toBeVisible({ timeout: 5000 })
    }

    test('step 2 appears after successful analysis', async ({ page }) => {
      await goToStep2(page)
      await expect(page.locator('.step-title', { hasText: '2.' })).toBeVisible()
    })

    test('three stats cards show matched, fuzzy, unmatched counts', async ({ page }) => {
      await goToStep2(page)
      await expect(page.locator('.stat-card')).toHaveCount(3)
      await expect(page.locator('.stat-number').nth(0)).toContainText('1') // exact matched
      await expect(page.locator('.stat-number').nth(2)).toContainText('1') // unmatched
    })

    test('unmatched section shows student names as red badges', async ({ page }) => {
      await goToStep2(page)
      await expect(page.locator('.badge-red', { hasText: 'UNKNOWN' })).toBeVisible()
    })

    test('fuzzy matches section is shown when present', async ({ page }) => {
      // Override to return a fuzzy match
      await setupApiMocks(page, {})
      await page.route('**/api/import/assessments/preview', (route) =>
        route.fulfill({
          json: {
            tool_id: 1,
            assessment_type: 'Initiale',
            matched_results: [
              {
                csv_nom: 'DUPONT',
                csv_prenom: 'Alise',
                db_student_id: 1,
                db_first_name: 'Alice',
                db_last_name: 'DUPONT',
                match_type: 'fuzzy',
                score: 0.72,
                details: {},
              },
            ],
            unmatched_results: [],
          },
        }),
      )

      await page.locator('.form-grid .action-select').first().selectOption({ index: 1 })
      await page.locator('.form-grid .action-select').nth(1).selectOption({ index: 1 })
      await page.locator('.form-grid .action-select').nth(2).selectOption({ index: 1 })

      await page.locator('input[type="file"]').setInputFiles({
        name: 'r.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from('Nom;Prénom;Score\nDUPONT;Alise;72'),
      })

      await page.locator('button', { hasText: 'Analyser' }).click()
      await expect(page.locator('.fuzzy-section')).toBeVisible({ timeout: 5000 })
      await expect(page.locator('.preview-table')).toBeVisible()
    })

    test('"Annuler" resets to step 1', async ({ page }) => {
      await goToStep2(page)
      await page.locator('button', { hasText: 'Annuler' }).click()
      await expect(page.locator('.step-title', { hasText: '1.' })).toBeVisible()
    })

    test('"Sauvegarder" shows success panel', async ({ page }) => {
      await goToStep2(page)
      await page.locator('button', { hasText: 'Sauvegarder les résultats' }).click()
      await expect(page.locator('.success-panel')).toBeVisible({ timeout: 5000 })
      await expect(page.locator('.success-panel h2')).toContainText('enregistrés')
    })

    test('success panel shows new and updated score counts', async ({ page }) => {
      await goToStep2(page)
      await page.locator('button', { hasText: 'Sauvegarder les résultats' }).click()
      await expect(page.locator('.success-stats')).toContainText('1')
    })

    test('"Faire un nouvel import" resets to step 1', async ({ page }) => {
      await goToStep2(page)
      await page.locator('button', { hasText: 'Sauvegarder' }).click()
      await page.locator('button', { hasText: 'Faire un nouvel import' }).click()
      await expect(page.locator('.step-title', { hasText: '1.' })).toBeVisible()
      await expect(page.locator('.success-panel')).toBeHidden()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Navigation
  // ──────────────────────────────────────────────────────────────
  test.describe('Navigation', () => {
    test('"Retour" navigates back to /', async ({ page }) => {
      await page.locator('button', { hasText: '← Retour' }).click()
      await expect(page).toHaveURL(new RegExp(`${APP_BASE}/?$`))
    })
  })
})
