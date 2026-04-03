import { test, expect } from '@playwright/test'
import { APP_BASE, authenticateAndGoTo } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'

test.describe('Gestion des Étudiants (/gestion-etudiants)', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/gestion-etudiants')
  })

  // ──────────────────────────────────────────────────────────────
  // Page structure & Tab navigation
  // ──────────────────────────────────────────────────────────────
  test.describe('Tab navigation', () => {
    test('renders the page heading', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('Gestion des Étudiants')
    })

    test('shows three tabs: Promotions, Outils, Groupes', async ({ page }) => {
      await expect(page.locator('.tab-btn', { hasText: 'Promotions' })).toBeVisible()
      await expect(page.locator('.tab-btn', { hasText: 'Outils' })).toBeVisible()
      await expect(page.locator('.tab-btn', { hasText: 'Groupes' })).toBeVisible()
    })

    test('"Promotions" tab is active by default', async ({ page }) => {
      await expect(page.locator('.tab-btn.active')).toContainText('Promotions')
    })

    test('clicking "Outils" shows the tools table', async ({ page }) => {
      await page.locator('.tab-btn', { hasText: 'Outils' }).click()
      await expect(page.locator('.tab-btn.active')).toContainText('Outils')
      await expect(page.locator('h2', { hasText: 'Liste des Outils' })).toBeVisible()
    })

    test('clicking "Groupes" shows the groups table', async ({ page }) => {
      await page.locator('.tab-btn', { hasText: 'Groupes' }).click()
      await expect(page.locator('.tab-btn.active')).toContainText('Groupes')
      await expect(page.locator('h2', { hasText: 'Liste des Groupes' })).toBeVisible()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Promotions CRUD
  // ──────────────────────────────────────────────────────────────
  test.describe('Promotions', () => {
    test('lists existing promotions', async ({ page }) => {
      await expect(page.locator('tbody tr', { hasText: 'BUT INFO 2024-2025' })).toBeVisible()
      await expect(page.locator('tbody tr', { hasText: 'BUT INFO 2025-2026' })).toBeVisible()
    })

    test('opens "create promotion" modal when button is clicked', async ({ page }) => {
      await page.locator('button', { hasText: 'Nouvelle Promotion' }).click()
      await expect(page.locator('.modal')).toBeVisible()
      await expect(page.locator('.modal h2')).toContainText('Ajouter')
    })

    test('"Enregistrer" is disabled when the name field is empty', async ({ page }) => {
      await page.locator('button', { hasText: 'Nouvelle Promotion' }).click()
      await expect(page.locator('.modal button', { hasText: 'Enregistrer' })).toBeDisabled()
    })

    test('successfully creates a promotion', async ({ page }) => {
      await page.locator('button', { hasText: 'Nouvelle Promotion' }).click()
      await page.locator('.modal input[type="text"]').fill('BUT INFO 2026-2027')
      await page.locator('.modal button', { hasText: 'Enregistrer' }).click()
      await expect(page.locator('.modal')).toBeHidden()
    })

    test('closes modal on "Annuler"', async ({ page }) => {
      await page.locator('button', { hasText: 'Nouvelle Promotion' }).click()
      await page.locator('.modal button', { hasText: 'Annuler' }).click()
      await expect(page.locator('.modal')).toBeHidden()
    })

    test('opens edit modal pre-filled with existing promotion name', async ({ page }) => {
      await page.locator('button', { hasText: 'Modifier' }).first().click()
      const input = page.locator('.modal input[type="text"]')
      await expect(input).toHaveValue('BUT INFO 2024-2025')
    })

    test('shows confirm dialog when deleting a promotion', async ({ page }) => {
      await page.locator('button', { hasText: 'Supprimer' }).first().click()
      await expect(page.locator('.confirm-modal, .modal')).toBeVisible()
    })

    test('cancelling delete dismisses the dialog', async ({ page }) => {
      await page.locator('button', { hasText: 'Supprimer' }).first().click()
      await page.locator('button', { hasText: 'Annuler' }).click()
      await expect(page.locator('.confirm-modal')).toBeHidden()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Tools CRUD
  // ──────────────────────────────────────────────────────────────
  test.describe('Outils', () => {
    test.beforeEach(async ({ page }) => {
      await page.locator('.tab-btn', { hasText: 'Outils' }).click()
    })

    test('lists mock tools with code and full name', async ({ page }) => {
      await expect(page.locator('tbody td strong', { hasText: 'PV' })).toBeVisible()
      await expect(page.locator('tbody td', { hasText: 'Projet Voltaire' })).toBeVisible()
    })

    test('opens "create tool" modal', async ({ page }) => {
      await page.locator('button', { hasText: 'Nouvel Outil' }).click()
      await expect(page.locator('.modal')).toBeVisible()
      await expect(page.locator('.modal h2')).toContainText('Ajouter')
    })

    test('"Enregistrer" disabled when only code is filled (full_name required)', async ({ page }) => {
      await page.locator('button', { hasText: 'Nouvel Outil' }).click()
      await page.locator('.modal input[type="text"]').first().fill('TP')
      // full_name still empty → disabled
      await expect(page.locator('.modal button', { hasText: 'Enregistrer' })).toBeDisabled()
    })

    test('successfully creates a tool when both fields are filled', async ({ page }) => {
      await page.locator('button', { hasText: 'Nouvel Outil' }).click()
      const inputs = page.locator('.modal input[type="text"]')
      await inputs.first().fill('TP')
      await inputs.nth(1).fill('Outil de Test')
      await page.locator('.modal button', { hasText: 'Enregistrer' }).click()
      await expect(page.locator('.modal')).toBeHidden()
    })

    test('deletes a tool after confirmation', async ({ page }) => {
      let deleteCalled = false
      await page.route('**/api/tools/**', async (route) => {
        if (route.request().method() === 'DELETE') {
          deleteCalled = true
          return route.fulfill({ status: 204 })
        }
        return route.continue()
      })
      await page.locator('button', { hasText: 'Supprimer' }).first().click()
      await page.locator('button', { hasText: 'Confirmer' }).click()
      await expect.poll(() => deleteCalled).toBe(true)
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Groups CRUD
  // ──────────────────────────────────────────────────────────────
  test.describe('Groupes', () => {
    test.beforeEach(async ({ page }) => {
      await page.locator('.tab-btn', { hasText: 'Groupes' }).click()
    })

    test('lists mock groups with name and description', async ({ page }) => {
      await expect(page.locator('tbody td strong', { hasText: 'G0' })).toBeVisible()
      await expect(page.locator('tbody td', { hasText: 'Groupe contrôle' })).toBeVisible()
    })

    test('opens "create group" modal', async ({ page }) => {
      await page.locator('button', { hasText: 'Nouveau Groupe' }).click()
      await expect(page.locator('.modal')).toBeVisible()
    })

    test('description textarea is visible in group modal', async ({ page }) => {
      await page.locator('button', { hasText: 'Nouveau Groupe' }).click()
      await expect(page.locator('.modal textarea')).toBeVisible()
    })

    test('successfully creates a group', async ({ page }) => {
      await page.locator('button', { hasText: 'Nouveau Groupe' }).click()
      await page.locator('.modal input[type="text"]').fill('G7')
      await page.locator('.modal textarea').fill('Nouveau groupe')
      await page.locator('.modal button', { hasText: 'Enregistrer' }).click()
      await expect(page.locator('.modal')).toBeHidden()
    })

    test('updates group name via edit modal', async ({ page }) => {
      await page.locator('button', { hasText: 'Modifier' }).first().click()
      const input = page.locator('.modal input[type="text"]')
      await input.fill('G0-MODIFIÉ')
      await page.locator('.modal button', { hasText: 'Enregistrer' }).click()
      await expect(page.locator('.modal')).toBeHidden()
    })
  })
})
