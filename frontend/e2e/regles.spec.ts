import { test, expect } from '@playwright/test'
import { APP_BASE, authenticateAndGoTo } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'
import { mockCategories } from './helpers/mock-data.js'
import { setTimeout } from 'timers/promises'

test.describe('Catégories & Règles (/regles)', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/regles')
  })

  // ──────────────────────────────────────────────────────────────
  // Rendering
  // ──────────────────────────────────────────────────────────────
  test.describe('Rendering', () => {
    test('renders the page heading', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('Catégories & Règles')
    })

    test('shows the "Recalculer" button', async ({ page }) => {
      await expect(page.locator('button', { hasText: 'Recalculer les notes' })).toBeVisible()
    })

    test('renders one category card per mock category', async ({ page }) => {
      await expect(page.locator('.category-box')).toHaveCount(mockCategories.length)
    })

    test('each category card shows its name and penalty', async ({ page }) => {
      const firstCard = page.locator('.category-box').first()
      await expect(firstCard).toContainText('Grammaire')
      await expect(firstCard.locator('.penalty-badge')).toContainText('+1')
    })

    test('category ID is visible in the card header', async ({ page }) => {
      const firstCard = page.locator('.category-box').first()
      await expect(firstCard.locator('.category-id')).toContainText('GRAMMAR')
    })

    test('rules are listed inside each category card', async ({ page }) => {
      await expect(page.locator('.rule-item')).toHaveCount(3) // 2 + 1 + 0 from mock
    })

    test('each rule shows its LT ID', async ({ page }) => {
      await expect(page.locator('.rule-id', { hasText: 'FRENCH_GRAMMAR_1' })).toBeVisible()
    })

    test('active rule has toggle checked; inactive toggle is unchecked', async ({ page }) => {
      const toggles = page.locator('.switch input[type="checkbox"]')
      // First rule is_active: true
      await expect(toggles.first()).toBeChecked()
      // Second rule is_active: false
      await expect(toggles.nth(1)).not.toBeChecked()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Rule toggle
  // ──────────────────────────────────────────────────────────────
  test.describe('Rule toggle', () => {
    test('toggling a rule calls the PATCH rules API', async ({ page }) => {
      let patchCalled = false
      await page.route('**/api/rules/**', async (route) => {
        if (route.request().method() === 'PATCH') {
          patchCalled = true
          return route.fulfill({ json: { id: 1, is_active: false } })
        }
        return route.continue()
      })

      await page.locator('.switch input[type="checkbox"]').first().click()
      expect(patchCalled).toBe(true)
    })

    test('toggling reverts if API call fails', async ({ page }) => {
      await page.route('**/api/rules/**', (route) =>
        route.fulfill({ status: 500, json: {} }),
      )

      const firstToggle = page.locator('.switch input[type="checkbox"]').first()
      const initialState = await firstToggle.isChecked()
      await firstToggle.click()
      await expect(firstToggle).toHaveJSProperty('checked', initialState)
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Category edit modal
  // ──────────────────────────────────────────────────────────────
  test.describe('Category edit modal', () => {
    test('clicking the pencil icon opens the edit modal', async ({ page }) => {
      await page.locator('.edit-icon-svg').first().click()
      await expect(page.locator('.modal')).toBeVisible()
    })

    test('modal shows disabled fields for lt_category_id and name', async ({ page }) => {
      await page.locator('.edit-icon-svg').first().click()
      const inputs = page.locator('.modal input[disabled]')
      await expect(inputs).toHaveCount(2)
    })

    test('modal contains Rousseau type selector with all options', async ({ page }) => {
      await page.locator('.edit-icon-svg').first().click()
      const select = page.locator('.modal select')
      await expect(select.locator('option', { hasText: 'Dessin' })).toBeAttached()
      await expect(select.locator('option', { hasText: 'Sens' })).toBeAttached()
      await expect(select.locator('option', { hasText: 'Règle' })).toBeAttached()
      await expect(select.locator('option', { hasText: 'Autre' })).toBeAttached()
    })

    test('modal contains penalty numeric input', async ({ page }) => {
      await page.locator('.edit-icon-svg').first().click()
      await expect(page.locator('.modal input[type="number"]')).toBeVisible()
    })

    test('closing modal with "Annuler" hides it', async ({ page }) => {
      await page.locator('.edit-icon-svg').first().click()
      await page.locator('.modal button', { hasText: 'Annuler' }).click()
      await expect(page.locator('.modal')).toBeHidden()
    })

    test('clicking overlay closes the modal', async ({ page }) => {
      await page.locator('.edit-icon-svg').first().click()
      await page.locator('.modal-overlay').click({ position: { x: 5, y: 5 } })
      await expect(page.locator('.modal')).toBeHidden()
    })

    test('saving calls PATCH categories API and closes modal', async ({ page }) => {
      let patchCalled = false
      await page.route('**/api/categories/**', async (route) => {
        if (route.request().method() === 'PATCH') {
          patchCalled = true
          return route.fulfill({ json: mockCategories[0] })
        }
        return route.continue()
      })

      await page.locator('.edit-icon-svg').first().click()
      await page.locator('.modal input[type="number"]').fill('2.5')
      await page.locator('.modal button', { hasText: 'Enregistrer' }).click()

      await expect.poll(() => patchCalled).toBe(true)
      await expect(page.locator('.modal')).toBeHidden()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Recalculate global action
  // ──────────────────────────────────────────────────────────────
  test.describe('Recalculate global action', () => {
    test('shows confirmation dialog when "Recalculer" is clicked', async ({ page }) => {
      await page.locator('button', { hasText: 'Recalculer les notes' }).click()
      await expect(page.locator('.confirm-modal, .modal')).toBeVisible()
    })

    test('cancelling recalculate does not call the API', async ({ page }) => {
      let called = false
      await page.route('**/api/dictations/recalculate', async (route) => {
        called = true
        return route.continue()
      })

      await page.locator('button', { hasText: 'Recalculer les notes' }).click()
      await page.locator('button', { hasText: 'Annuler' }).click()
      expect(called).toBe(false)
    })

    test('confirming recalculate calls the POST API', async ({ page }) => {
      let called = false
      await page.route('**/api/dictations/recalculate', async (route) => {
        called = true
        return route.fulfill({ json: { detail: 'Toutes les copies ont été recalculées.' } })
      })

      await page.locator('button', { hasText: 'Recalculer les notes' }).click()
      await page.locator('button', { hasText: 'Confirmer' }).click()
      await expect.poll(() => called).toBe(true)
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Loading & empty states
  // ──────────────────────────────────────────────────────────────
  test.describe('Loading & empty states', () => {
    test('shows loading while fetching categories', async ({ page }) => {
      await page.route('**/api/categories/**', async (route) => {
        await setTimeout(500);
        await route.fulfill({ json: [] })
      })
      const gotoPromise = page.goto(`${APP_BASE}/regles`)
      await expect(page.locator('.loading-container, .loading-content')).toBeVisible()
      await gotoPromise
    })

    test('shows empty state when category list is empty', async ({ page }) => {
      await setupApiMocks(page, { categories: [] })
      await page.goto(`${APP_BASE}/regles`)
      await expect(page.locator('.empty-state')).toBeVisible()
    })
  })
})
