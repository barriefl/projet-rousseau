import { test, expect } from '@playwright/test'
import { APP_BASE, authenticateAndGoTo } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'
import { mockStudents } from './helpers/mock-data.js'

test.describe('Liste des Étudiants (/etudiants)', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/etudiants')
  })

  // ──────────────────────────────────────────────────────────────
  // Rendering
  // ──────────────────────────────────────────────────────────────
  test.describe('Rendering', () => {
    test('renders the page heading', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('Liste des Étudiants')
    })

    test('renders table headers', async ({ page }) => {
      await expect(page.locator('th', { hasText: 'Étudiant' })).toBeVisible()
      await expect(page.locator('th', { hasText: 'Promotion' })).toBeVisible()
      await expect(page.locator('th', { hasText: 'Groupe' })).toBeVisible()
      await expect(page.locator('th', { hasText: 'Actions' })).toBeVisible()
    })

    test('renders the correct number of student rows', async ({ page }) => {
      const rows = page.locator('tbody tr').filter({ hasText: 'DUPONT' })
      await expect(rows).toHaveCount(1)
    })

    test('displays student name, promo and group', async ({ page }) => {
      const firstRow = page.locator('tbody tr').first()
      await expect(firstRow).toContainText('DUPONT')
      await expect(firstRow).toContainText('Alice')
      await expect(firstRow).toContainText('BUT INFO 2024-2025')
    })

    test('shows "Modifier" and "Supprimer" action buttons per row', async ({ page }) => {
      const firstRow = page.locator('tbody tr').first()
      await expect(firstRow.locator('button', { hasText: 'Modifier' })).toBeVisible()
      await expect(firstRow.locator('button', { hasText: 'Supprimer' })).toBeVisible()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Edit modal
  // ──────────────────────────────────────────────────────────────
  test.describe('Edit modal', () => {
    test('opens StudentFormModal when "Modifier" is clicked', async ({ page }) => {
      await page.locator('button', { hasText: 'Modifier' }).first().click()
      await expect(page.locator('.modal-container')).toBeVisible()
    })

    test('modal pre-fills first and last name', async ({ page }) => {
      await page.locator('button', { hasText: 'Modifier' }).first().click()
      await expect(page.locator('input[placeholder="ROUSSEAU"]')).toHaveValue(mockStudents[0].last_name)
      await expect(page.locator('input[placeholder="Jean-Jacques"]')).toHaveValue(mockStudents[0].first_name)
    })

    test('modal closes when cancel button is clicked', async ({ page }) => {
      await page.locator('button', { hasText: 'Modifier' }).first().click()
      await expect(page.locator('.modal-container')).toBeVisible()
      await page.locator('.btn-text', { hasText: 'Annuler' }).click()
      await expect(page.locator('.modal-container')).toBeHidden()
    })

    test('modal closes when overlay backdrop is clicked', async ({ page }) => {
      await page.locator('button', { hasText: 'Modifier' }).first().click()
      await page.locator('.modal-overlay').click({ position: { x: 5, y: 5 } })
      await expect(page.locator('.modal-container')).toBeHidden()
    })

    test('"Sauvegarder" button is disabled when name fields are empty', async ({ page }) => {
      await page.locator('button', { hasText: 'Modifier' }).first().click()
      await page.locator('input[placeholder="ROUSSEAU"]').fill('')
      await page.locator('input[placeholder="Jean-Jacques"]').fill('')
      await expect(page.locator('.btn-submit')).toBeDisabled()
    })

    test('successfully submits the edit form', async ({ page }) => {
      await page.locator('button', { hasText: 'Modifier' }).first().click()
      await page.locator('input[placeholder="ROUSSEAU"]').fill('UPDATED')
      await page.locator('.btn-submit').click()
      // Modal should close after save
      await expect(page.locator('.modal-container')).toBeHidden()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Delete
  // ──────────────────────────────────────────────────────────────
  test.describe('Delete student', () => {
    test('shows confirmation dialog when "Supprimer" is clicked', async ({ page }) => {
      await page.locator('button', { hasText: 'Supprimer' }).first().click()
      await expect(page.locator('.confirm-modal, .modal')).toBeVisible()
    })

    test('cancelling deletion keeps the student in the table', async ({ page }) => {
      await page.locator('button', { hasText: 'Supprimer' }).first().click()
      await page.locator('button', { hasText: 'Annuler' }).click()
      await expect(page.locator('tbody tr')).toHaveCount(mockStudents.length)
    })

    test('confirming deletion triggers the delete API call', async ({ page }) => {
      let deleteCalled = false
      await page.route('**/api/students/**', async (route) => {
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
  // Empty & loading states
  // ──────────────────────────────────────────────────────────────
  test.describe('Empty state', () => {
    test('shows empty state when no students are returned', async ({ page }) => {
      await setupApiMocks(page, { students: [] })
      await page.goto(`${APP_BASE}/etudiants`)
      await expect(page.locator('.empty-state, [title="Aucun étudiant"]')).toBeVisible()
    })
  })
})
