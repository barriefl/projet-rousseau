import { test, expect } from '@playwright/test'
import { APP_BASE, authenticateAndGoTo } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'

test.describe('Importation d\'une Étude (/import-etude)', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/import-etude')
  })

  // ──────────────────────────────────────────────────────────────
  // Rendering
  // ──────────────────────────────────────────────────────────────
  test.describe('Rendering', () => {
    test('renders the page heading', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('Importation d\'une Étude')
    })

    test('shows "Retour" button', async ({ page }) => {
      await expect(page.locator('button', { hasText: '← Retour' })).toBeVisible()
    })

    test('shows step 1 panel with selectors and file input', async ({ page }) => {
      await expect(page.locator('.step-title', { hasText: '1.' })).toBeVisible()
      await expect(page.locator('select')).toHaveCount(2) // promotion + tool
      await expect(page.locator('input[type="file"]')).toBeVisible()
    })

    test('shows "Analyser le fichier" button', async ({ page }) => {
      await expect(page.locator('button', { hasText: 'Analyser le fichier' })).toBeVisible()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Step 1 – Configuration
  // ──────────────────────────────────────────────────────────────
  test.describe('Step 1 – Configuration', () => {
    test('promotion selector is populated with mock data', async ({ page }) => {
      const select = page.locator('select').first()
      await expect(select.locator('option', { hasText: 'BUT INFO 2024-2025' })).toBeAttached()
    })

    test('tool selector is populated with mock tools', async ({ page }) => {
      const select = page.locator('select').nth(1)
      await expect(select.locator('option', { hasText: 'Projet Voltaire' })).toBeAttached()
      await expect(select.locator('option', { hasText: 'Ecri+' })).toBeAttached()
    })

    test('"Analyser" button is disabled when no promotion selected', async ({ page }) => {
      await expect(page.locator('button', { hasText: 'Analyser' })).toBeDisabled()
    })

    test('"Analyser" button is enabled when all fields are filled', async ({ page }) => {
      await page.locator('select').first().selectOption({ index: 1 })
      await page.locator('select').nth(1).selectOption({ index: 1 })

      await page.locator('input[type="file"]').setInputFiles({
        name: 'enquete.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from('15. nom;16. prenom\nDUPONT;Alice'),
      })

      await expect(page.locator('button', { hasText: 'Analyser' })).toBeEnabled()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Step 2 – Preview
  // ──────────────────────────────────────────────────────────────
  test.describe('Step 2 – Preview', () => {
    async function goToStep2(page: import('@playwright/test').Page) {
      await page.locator('select').first().selectOption({ index: 1 })
      await page.locator('select').nth(1).selectOption({ index: 1 })

      await page.locator('input[type="file"]').setInputFiles({
        name: 'enquete.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from('15. nom;16. prenom\nDUPONT;Alice\nMARTIN;Bob\nDURAND;Charlie'),
      })

      await page.locator('button', { hasText: 'Analyser' }).click()
      await expect(page.locator('.step-title', { hasText: '2.' })).toBeVisible()
    }

    test('shows step 2 heading after analysis', async ({ page }) => {
      await goToStep2(page)
      await expect(page.locator('.step-title', { hasText: '2.' })).toBeVisible()
    })

    test('stats grid shows exact, fuzzy, and new counts', async ({ page }) => {
      await goToStep2(page)
      await expect(page.locator('.stat-card')).toHaveCount(3)
      await expect(page.locator('.stat-number').nth(0)).toContainText('1') // exact
      await expect(page.locator('.stat-number').nth(1)).toContainText('1') // fuzzy
      await expect(page.locator('.stat-number').nth(2)).toContainText('1') // new
    })

    test('groups-to-create alert is shown', async ({ page }) => {
      await goToStep2(page)
      await expect(page.locator('.info-box')).toBeVisible()
      await expect(page.locator('.badge-gray', { hasText: 'G6' })).toBeVisible()
    })

    test('fuzzy matches section shows the correction dropdown', async ({ page }) => {
      await goToStep2(page)
      await expect(page.locator('.fuzzy-section')).toBeVisible()
      await expect(page.locator('.action-select')).toBeVisible()
    })

    test('"Annuler" resets back to step 1', async ({ page }) => {
      await goToStep2(page)
      await page.locator('button', { hasText: 'Annuler' }).click()
      await expect(page.locator('.step-title', { hasText: '1.' })).toBeVisible()
      await expect(page.locator('.step-title', { hasText: '2.' })).toBeHidden()
    })

    test('"Valider et Importer" shows success panel after confirmation', async ({ page }) => {
      await goToStep2(page)
      await page.locator('button', { hasText: 'Valider et Importer' }).click()
      await expect(page.locator('.success-panel')).toBeVisible({ timeout: 5000 })
      await expect(page.locator('.success-panel h2')).toContainText('réussie')
    })

    test('success panel shows created and updated counts', async ({ page }) => {
      await goToStep2(page)
      await page.locator('button', { hasText: 'Valider et Importer' }).click()
      await expect(page.locator('.success-stats')).toContainText('1')
    })

    test('"Faire un nouvel import" from success panel resets to step 1', async ({ page }) => {
      await goToStep2(page)
      await page.locator('button', { hasText: 'Valider et Importer' }).click()
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
