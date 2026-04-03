import { test, expect } from '@playwright/test'
import { APP_BASE, authenticateAndGoTo } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'

test.describe('Dictée Référente (/dictee-referente)', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/dictee-referente')
  })

  // ──────────────────────────────────────────────────────────────
  // Rendering
  // ──────────────────────────────────────────────────────────────
  test.describe('Rendering', () => {
    test('renders the page heading', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('Définir une dictée référente')
    })

    test('shows the info paragraph about the purpose', async ({ page }) => {
      await expect(page.locator('.intro-text')).toContainText('texte servira de base parfaite')
    })

    test('shows title input field', async ({ page }) => {
      await expect(page.locator('input[type="text"]')).toBeVisible()
    })

    test('shows textarea for the reference text', async ({ page }) => {
      await expect(page.locator('textarea')).toBeVisible()
    })

    test('shows the file upload zone', async ({ page }) => {
      await expect(page.locator('.upload-zone')).toBeVisible()
      await expect(page.locator('.upload-zone h3')).toContainText('Importez le fichier du professeur')
    })

    test('shows the "Sauvegarder" submit button', async ({ page }) => {
      await expect(page.locator('.btn-warning')).toContainText('Sauvegarder')
    })

    test('shows "← Retour" button', async ({ page }) => {
      await expect(page.locator('button', { hasText: '← Retour' })).toBeVisible()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Form validation
  // ──────────────────────────────────────────────────────────────
  test.describe('Validation', () => {
    test('does not submit when title is empty', async ({ page }) => {
      let apiCalled = false
      await page.route('**/api/dictations', async (route) => {
        if (route.request().method() === 'POST') {
          apiCalled = true
          return route.fulfill({ status: 201, json: { id: 1 } })
        }
        return route.continue()
      })

      await page.locator('textarea').fill('Texte de référence valide.')
      await page.locator('.btn-warning').click()
      // Should NOT have called API (title is empty)
      expect(apiCalled).toBe(false)
    })

    test('does not submit when text is empty', async ({ page }) => {
      let apiCalled = false
      await page.route('**/api/dictations', async (route) => {
        if (route.request().method() === 'POST') {
          apiCalled = true
          return route.fulfill({ status: 201, json: { id: 1 } })
        }
        return route.continue()
      })

      await page.fill('input[type="text"]', 'Titre valide')
      // textarea intentionally left empty
      await page.locator('.btn-warning').click()
      expect(apiCalled).toBe(false)
    })
  })

  // ──────────────────────────────────────────────────────────────
  // File upload
  // ──────────────────────────────────────────────────────────────
  test.describe('File upload', () => {
    test('uploading a .txt file populates the textarea', async ({ page }) => {
      const content = 'Le chat dort sur le canapé.'
      await page.locator('.upload-zone').click()
      await page.locator('input[type="file"]').setInputFiles({
        name: 'reference.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from(content),
      })
      await expect(page.locator('textarea')).toHaveValue(content)
    })

    test('uploaded file name is displayed after selection', async ({ page }) => {
      await page.locator('.upload-zone').click()
      await page.locator('input[type="file"]').setInputFiles({
        name: 'professor_text.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('Contenu'),
      })
      await expect(page.locator('.upload-zone p')).toContainText('professor_text.txt')
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Successful submission
  // ──────────────────────────────────────────────────────────────
  test.describe('Successful submission', () => {
    test('fills form and submits successfully, redirects to /gestion', async ({ page }) => {
      await page.fill('input[type="text"]', 'Dictée Initiale – Sept. 2024')
      await page.locator('textarea').fill('Voici le texte sans aucune faute.')
      await page.locator('.btn-warning').click()

      // Button should briefly show "Enregistrement..."
      // then redirect
      await expect(page).toHaveURL(new RegExp(`${APP_BASE}/gestion`), { timeout: 5000 })
    })

    test('"Enregistrement..." label appears during submission', async ({ page }) => {
      await page.route('**/api/dictations', async (route) => {
        await new Promise((r) => setTimeout(r, 400))
        await route.fulfill({ status: 201, json: { id: 1, title: 'T', content_reference: 'C' } })
      })

      await page.fill('input[type="text"]', 'Titre')
      await page.locator('textarea').fill('Contenu')
      await page.locator('.btn-warning').click()

      await expect(page.locator('.btn-warning')).toContainText('Enregistrement...')
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
