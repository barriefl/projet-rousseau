import { test, expect } from '@playwright/test'
import { APP_BASE, authenticateAndGoTo } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'
import * as path from 'path'

test.describe('Importation de Dictées (/import-dictee)', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/import-dictee')
  })

  // ──────────────────────────────────────────────────────────────
  // Rendering
  // ──────────────────────────────────────────────────────────────
  test.describe('Rendering', () => {
    test('renders the page heading', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('Importation de Dictées')
    })

    test('shows "Retour" button', async ({ page }) => {
      await expect(page.locator('button', { hasText: '← Retour' })).toBeVisible()
    })

    test('shows three selector dropdowns: promotion, dictée, type', async ({ page }) => {
      await expect(page.locator('.global-settings select')).toHaveCount(3)
    })

    test('upload zone is disabled when no promotion and dictation are selected', async ({ page }) => {
      await expect(page.locator('.upload-zone.disabled')).toBeVisible()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Form interaction
  // ──────────────────────────────────────────────────────────────
  test.describe('Form selectors', () => {
    test('promotion dropdown is populated with mock promotions', async ({ page }) => {
      const select = page.locator('.global-settings select').first()
      await expect(select.locator('option', { hasText: 'BUT INFO 2024-2025' })).toBeAttached()
    })

    test('dictation dropdown is populated with mock dictations', async ({ page }) => {
      const select = page.locator('.global-settings select').nth(1)
      await expect(select.locator('option', { hasText: 'Dictée Initiale 2024' })).toBeAttached()
    })

    test('assessment type dropdown has "Initiale" and "Finale" options', async ({ page }) => {
      const select = page.locator('.global-settings select').nth(2)
      await expect(select.locator('option', { hasText: 'Initiale' })).toBeAttached()
      await expect(select.locator('option', { hasText: 'Finale' })).toBeAttached()
    })

    test('upload zone becomes enabled after promotion and dictation are selected', async ({ page }) => {
      await page.locator('.global-settings select').first().selectOption({ index: 1 })
      await page.locator('.global-settings select').nth(1).selectOption({ index: 1 })
      await expect(page.locator('.upload-zone:not(.disabled)')).toBeVisible()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // File upload & matching
  // ──────────────────────────────────────────────────────────────
  test.describe('File upload and matching', () => {
    async function selectFormOptions(page: import('@playwright/test').Page) {
      await page.locator('.global-settings select').first().selectOption({ index: 1 })
      await page.locator('.global-settings select').nth(1).selectOption({ index: 1 })
    }

    test('uploading a .txt file creates a file item in the list', async ({ page }) => {
      await selectFormOptions(page)

      // Create a temporary buffer representing the text file
      const fileContent = 'Ceci est la dictée de test.'
      await page.locator('input[type="file"]').setInputFiles({
        name: 'DUPONT_Alice_2024.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from(fileContent),
      })

      await expect(page.locator('.file-item')).toHaveCount(1)
      await expect(page.locator('.file-name', { hasText: 'DUPONT_Alice_2024.txt' })).toBeVisible()
    })

    test('matched file shows green "Associé à" status', async ({ page }) => {
      await selectFormOptions(page)

      await page.locator('input[type="file"]').setInputFiles({
        name: 'DUPONT_Alice.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('Texte élève'),
      })

      // Alice DUPONT is in the mock students → should be MATCHED
      await expect(page.locator('.file-item.status-matched, .file-item.status-confirmed')).toHaveCount(1)
    })

    test('unrecognised file shows "UNKNOWN" status with action buttons', async ({ page }) => {
      await selectFormOptions(page)

      await page.locator('input[type="file"]').setInputFiles({
        name: 'ZZZZZZ_Nobody.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('Texte inconnu'),
      })

      await expect(page.locator('.file-item.status-unknown')).toHaveCount(1)
      await expect(page.locator('.file-action.danger button', { hasText: 'Créer étudiant' })).toBeVisible()
      await expect(page.locator('.file-action.danger button', { hasText: 'Ignorer fichier' })).toBeVisible()
    })

    test('"Ignorer fichier" sets the file to IGNORED status', async ({ page }) => {
      await selectFormOptions(page)

      await page.locator('input[type="file"]').setInputFiles({
        name: 'ZZZZZZ_Nobody.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('Texte inconnu'),
      })

      await page.locator('.file-action.danger button', { hasText: 'Ignorer fichier' }).click()
      await expect(page.locator('.file-item.status-ignored')).toHaveCount(1)
    })

    test('submit button is disabled when there are unresolved files', async ({ page }) => {
      await selectFormOptions(page)

      await page.locator('input[type="file"]').setInputFiles({
        name: 'ZZZZZZ_Nobody.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('Texte inconnu'),
      })

      // UNKNOWN file blocks submission
      await expect(page.locator('.btn-large')).toBeDisabled()
    })

    test('submit button is enabled when all files are resolved', async ({ page }) => {
      await selectFormOptions(page)

      await page.locator('input[type="file"]').setInputFiles({
        name: 'DUPONT_Alice.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('Texte élève'),
      })

      // MATCHED file → submit should be enabled
      await expect(page.locator('.btn-large')).toBeEnabled()
    })

    test('successful bulk submit shows progress bar and then redirects', async ({ page }) => {
      await selectFormOptions(page)

      await page.locator('input[type="file"]').setInputFiles({
        name: 'DUPONT_Alice.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('Texte élève'),
      })

      await page.locator('.btn-large').click()
      // Progress bar should appear
      await expect(page.locator('.progress-bar, .progress-container')).toBeVisible()
      // Eventually redirects to /correction
      await expect(page).toHaveURL(new RegExp(`${APP_BASE}/correction`), { timeout: 5000 })
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Navigation
  // ──────────────────────────────────────────────────────────────
  test.describe('Navigation', () => {
    test('"Retour" navigates back to /gestion', async ({ page }) => {
      await page.locator('button', { hasText: '← Retour' }).click()
      await expect(page).toHaveURL(new RegExp(`${APP_BASE}/gestion`))
    })
  })
})
