import { test, expect } from '@playwright/test'
import { APP_BASE, authenticateAndGoTo } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'

/**
 * Component tests are exercised through the pages that render them,
 * since Playwright is a real-browser tool.
 */

// ================================================================
// AppToast
// ================================================================
test.describe('AppToast component', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/gestion-etudiants')
  })

  test('success toast appears after creating a promotion', async ({ page }) => {
    await page.locator('button', { hasText: 'Nouvelle Promotion' }).click()
    await page.locator('.modal input[type="text"]').fill('Promo Test Toast')
    await page.locator('.modal button', { hasText: 'Enregistrer' }).click()

    await expect(page.locator('.toast-notification.success')).toBeVisible()
  })

  test('success toast contains a confirmation message', async ({ page }) => {
    await page.locator('button', { hasText: 'Nouvelle Promotion' }).click()
    await page.locator('.modal input[type="text"]').fill('Promo')
    await page.locator('.modal button', { hasText: 'Enregistrer' }).click()

    const toast = page.locator('.toast-notification.success')
    await expect(toast).toBeVisible()
    // message text comes from ui.notify(), which the component displays
    await expect(toast.locator('.message')).not.toBeEmpty()
  })

  test('toast has a close "×" button', async ({ page }) => {
    await page.locator('button', { hasText: 'Nouvelle Promotion' }).click()
    await page.locator('.modal input[type="text"]').fill('Promo')
    await page.locator('.modal button', { hasText: 'Enregistrer' }).click()

    await expect(page.locator('.toast-notification .close-btn')).toBeVisible()
  })

  test('clicking the close button hides the toast', async ({ page }) => {
    await page.locator('button', { hasText: 'Nouvelle Promotion' }).click()
    await page.locator('.modal input[type="text"]').fill('Promo')
    await page.locator('.modal button', { hasText: 'Enregistrer' }).click()

    await page.locator('.toast-notification .close-btn').click()
    await expect(page.locator('.toast-notification')).toBeHidden()
  })

  test('error toast appears when API call fails', async ({ page }) => {
    await page.route('**/api/promotions/', async (route) => {
      if (route.request().method() === 'POST') {
        return route.fulfill({ status: 400, json: { detail: 'Duplicate' } })
      }
      return route.continue()
    })

    await page.locator('button', { hasText: 'Nouvelle Promotion' }).click()
    await page.locator('.modal input[type="text"]').fill('Duplicate')
    await page.locator('.modal button', { hasText: 'Enregistrer' }).click()

    await expect(page.locator('.toast-notification.error')).toBeVisible()
  })
})

// ================================================================
// AppConfirm
// ================================================================
test.describe('AppConfirm component', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/gestion-etudiants')
  })

  test('confirm dialog appears with warning icon', async ({ page }) => {
    await page.locator('button', { hasText: 'Supprimer' }).first().click()
    await expect(page.locator('.confirm-modal')).toBeVisible()
    await expect(page.locator('.warning-icon')).toBeVisible()
  })

  test('confirm dialog shows a meaningful title', async ({ page }) => {
    await page.locator('button', { hasText: 'Supprimer' }).first().click()
    await expect(page.locator('.confirm-header h3')).not.toBeEmpty()
  })

  test('confirm dialog has "Annuler" and "Confirmer" buttons', async ({ page }) => {
    await page.locator('button', { hasText: 'Supprimer' }).first().click()
    await expect(page.locator('.confirm-actions button', { hasText: 'Annuler' })).toBeVisible()
    await expect(page.locator('.confirm-actions button', { hasText: 'Confirmer' })).toBeVisible()
  })

  test('"Annuler" closes the dialog without taking action', async ({ page }) => {
    let deleteCalled = false
    await page.route('**/api/promotions/**', async (route) => {
      if (route.request().method() === 'DELETE') deleteCalled = true
      return route.continue()
    })

    await page.locator('button', { hasText: 'Supprimer' }).first().click()
    await page.locator('.confirm-actions button', { hasText: 'Annuler' }).click()

    await expect(page.locator('.confirm-modal')).toBeHidden()
    expect(deleteCalled).toBe(false)
  })

  test('clicking backdrop closes the dialog', async ({ page }) => {
    await page.locator('button', { hasText: 'Supprimer' }).first().click()
    await page.locator('.modal-overlay').click({ position: { x: 5, y: 5 } })
    await expect(page.locator('.confirm-modal')).toBeHidden()
  })

  test('"Confirmer" button has danger styling', async ({ page }) => {
    await page.locator('button', { hasText: 'Supprimer' }).first().click()
    await expect(page.locator('.confirm-actions .btn-danger')).toBeVisible()
  })
})

// ================================================================
// AppLoading
// ================================================================
test.describe('AppLoading component', () => {
  test('loading spinner is visible while data is fetching', async ({ page }) => {
    await setupApiMocks(page)
    await page.route('**/api/students/', async (route) => {
      await new Promise((r) => setTimeout(r, 600))
      await route.fulfill({ json: [] })
    })

    const gotoPromise = authenticateAndGoTo(page, '/etudiants')
    await expect(page.locator('.loading-container')).toBeVisible()
    await gotoPromise
  })

  test('loading spinner disappears once data loads', async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/etudiants')
    await expect(page.locator('.loading-container')).toBeHidden()
  })

  test('loading message text is shown', async ({ page }) => {
    await setupApiMocks(page)
    await page.route('**/api/students/', async (route) => {
      await new Promise((r) => setTimeout(r, 600))
      await route.fulfill({ json: [] })
    })

    const gotoPromise = authenticateAndGoTo(page, '/etudiants')
    const loadingText = page.locator('.loading-content p, .loading-container p')
    await expect(loadingText).not.toBeEmpty()
    await gotoPromise
  })
})

// ================================================================
// AppEmptyState
// ================================================================
test.describe('AppEmptyState component', () => {
  test('empty state is shown when students list is empty', async ({ page }) => {
    await setupApiMocks(page, { students: [] })
    await authenticateAndGoTo(page, '/etudiants')

    await expect(page.locator('.empty-state')).toBeVisible()
  })

  test('empty state contains an icon, title and message', async ({ page }) => {
    await setupApiMocks(page, { students: [] })
    await authenticateAndGoTo(page, '/etudiants')

    const emptyState = page.locator('.empty-state')
    await expect(emptyState.locator('svg, .empty-icon')).toBeVisible()
    await expect(emptyState.locator('h3')).not.toBeEmpty()
    await expect(emptyState.locator('p')).not.toBeEmpty()
  })

  test('empty state on correction page shows retry button', async ({ page }) => {
    await setupApiMocks(page, { studentsWithScores: [] })
    await authenticateAndGoTo(page, '/correction')

    const retryBtn = page.locator('.empty-state button', { hasText: 'Réessayer' })
    await expect(retryBtn).toBeVisible()
  })

  test('clicking retry on correction page re-fetches students', async ({ page }) => {
    let callCount = 0
    await setupApiMocks(page, { studentsWithScores: [] })
    await page.route('**/api/students/with-scores', async (route) => {
      callCount++
      return route.fulfill({ json: [] })
    })

    await authenticateAndGoTo(page, '/correction')
    await page.locator('.empty-state button', { hasText: 'Réessayer' }).click()

    // Should have been called at least twice (initial + retry)
    expect(callCount).toBeGreaterThanOrEqual(2)
  })
})

// ================================================================
// StudentFormModal
// ================================================================
test.describe('StudentFormModal component', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await authenticateAndGoTo(page, '/etudiants')
    // Open the modal via the first "Modifier" button
    await page.locator('button', { hasText: 'Modifier' }).first().click()
    await expect(page.locator('.modal-container')).toBeVisible()
  })

  test.describe('Identity section', () => {
    test('shows "Identité" card section', async ({ page }) => {
      await expect(page.locator('.card-title', { hasText: 'Identité' })).toBeVisible()
    })

    test('shows last name, first name, promotion, group and tool fields', async ({ page }) => {
      await expect(page.locator('input[placeholder="ROUSSEAU"]')).toBeVisible()
      await expect(page.locator('input[placeholder="Jean-Jacques"]')).toBeVisible()
      await expect(page.locator('.modal-container select')).toHaveCount(3)
    })
  })

  test.describe('Reading habits section', () => {
    test('shows "Habitudes de lecture" section', async ({ page }) => {
      await expect(page.locator('.card-title', { hasText: 'lecture' })).toBeVisible()
    })

    test('shows appetence level input', async ({ page }) => {
      await expect(page.locator('input[type="number"]')).toBeVisible()
    })

    test('shows reading works checkboxes (pill grid)', async ({ page }) => {
      await expect(page.locator('.pill')).toHaveCount(5)
    })

    test('clicking a pill checkbox toggles it active', async ({ page }) => {
      const firstPill = page.locator('.pill').first()
      await firstPill.click()
      await expect(firstPill).toHaveClass(/active/)
      await firstPill.click()
      await expect(firstPill).not.toHaveClass(/active/)
    })

    test('segment (declared level) buttons render', async ({ page }) => {
      await expect(page.locator('.segment')).toHaveCount(4)
    })

    test('clicking a segment selects it', async ({ page }) => {
      const firstSegment = page.locator('.segment').first()
      await firstSegment.click()
      await expect(firstSegment.locator('input')).toBeChecked()
    })
  })

  test.describe('Family section', () => {
    test('shows "Environnement Familial" section', async ({ page }) => {
      await expect(page.locator('.card-title', { hasText: 'Familial' })).toBeVisible()
    })

    test('shows two parent sub-cards', async ({ page }) => {
      await expect(page.locator('.parent-subcard')).toHaveCount(2)
    })

    test('each parent sub-card has degree and CSP selectors', async ({ page }) => {
      const firstParent = page.locator('.parent-subcard').first()
      await expect(firstParent.locator('select')).toHaveCount(2)
    })
  })

  test.describe('Footer actions', () => {
    test('"Sauvegarder" button is visible in edit mode', async ({ page }) => {
      await expect(page.locator('.btn-submit', { hasText: 'Sauvegarder' })).toBeVisible()
    })

    test('"Sauvegarder" is disabled when required fields are empty', async ({ page }) => {
      await page.locator('input[placeholder="ROUSSEAU"]').fill('')
      await page.locator('input[placeholder="Jean-Jacques"]').fill('')
      await expect(page.locator('.btn-submit')).toBeDisabled()
    })

    test('"Annuler" closes the modal', async ({ page }) => {
      await page.locator('.modal-footer .btn-text').click()
      await expect(page.locator('.modal-container')).toBeHidden()
    })

    test('close (×) button in header closes the modal', async ({ page }) => {
      await page.locator('.close-x').click()
      await expect(page.locator('.modal-container')).toBeHidden()
    })
  })
})
