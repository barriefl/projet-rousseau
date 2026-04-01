import { test, expect } from '@playwright/test'

// --- DONNÉES SIMULÉES (MOCKS). ---
const mockCategories = [
  {
    id: 1,
    name: 'Accord du participe',
    lt_category_id: 'ACCORD_PARTICIPE',
    type_rousseau: 'Règle',
    penalty: 2,
    rules: [
      {
        id: 101,
        lt_rule_id: 'ACCORD_P_PASSE_AVEC_AVOIR',
        description: "Le participe passé employé avec l'auxiliaire avoir s'accorde...",
        is_active: true,
      },
      {
        id: 102,
        lt_rule_id: 'ACCORD_P_PASSE_AVEC_ETRE',
        description: "Le participe passé employé avec être s'accorde avec le sujet.",
        is_active: false,
      },
    ],
  },
  {
    id: 2,
    name: 'Homophones grammaticaux',
    lt_category_id: 'HOMOPHONES',
    type_rousseau: 'Sens',
    penalty: 1,
    rules: [],
  },
]

test.describe('Page Catégories & Règles (É.M.I.L.E.)', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('access_token', 'faux-token-e2e-playwright')
    })

    await page.route('**/api/categories', async (route) => {
      await route.fulfill({ status: 200, json: mockCategories })
    })

    await page.goto('/regles')
  })

  test('Doit afficher les catégories, leurs pénalités et leurs règles', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Catégories & Règles')

    const categoryBoxes = page.locator('.category-box')
    await expect(categoryBoxes).toHaveCount(2)

    const cat1 = categoryBoxes.nth(0)
    await expect(cat1.locator('.category-name')).toContainText('Accord du participe')
    await expect(cat1.locator('.penalty-badge')).toContainText('+2 pts')

    const rules = cat1.locator('.rule-item')
    await expect(rules).toHaveCount(2)
    await expect(rules.nth(0).locator('.rule-id')).toContainText('ACCORD_P_PASSE_AVEC_AVOIR')

    await expect(rules.nth(0).locator('input[type="checkbox"]')).toBeChecked()
    await expect(rules.nth(1).locator('input[type="checkbox"]')).not.toBeChecked()

    const cat2 = categoryBoxes.nth(1)
    await expect(cat2.locator('.category-name')).toContainText('Homophones grammaticaux')
    await expect(cat2.locator('.penalty-badge')).toContainText('+1 pt')
    await expect(cat2.locator('.category-body')).toContainText('Aucune règle détectée')
  })

  test("Doit permettre d'activer/désactiver une règle via le switch", async ({ page }) => {
    await page.route('**/api/rules/102', async (route) => {
      expect(route.request().method()).toMatch(/PUT|PATCH/)
      await route.fulfill({ status: 200, json: { success: true } })
    })

    const ruleItem = page.locator('.rule-item').filter({ hasText: 'ACCORD_P_PASSE_AVEC_ETRE' })

    await ruleItem.locator('.slider').click()

    const checkbox = ruleItem.locator('input[type="checkbox"]')
    await expect(checkbox).toBeChecked()

    await expect(page.locator('.toast-notification')).toBeVisible()
    await expect(page.locator('.toast-notification, .notification')).toContainText('activée')
  })

  test("Doit permettre de modifier le barème et le type d'une catégorie via la modale", async ({
    page,
  }) => {
    await page.route('**/api/categories/1', async (route) => {
      const payload = route.request().postDataJSON()
      expect(payload.penalty).toBe(3)
      expect(payload.type_rousseau).toBe('Dessin')
      await route.fulfill({ status: 200, json: { success: true } })
    })

    const cat1 = page.locator('.category-box').nth(0)
    await cat1.locator('.edit-icon-svg').click()

    const modal = page.locator('.modal')
    await expect(modal).toBeVisible()
    await expect(modal.locator('h2')).toContainText('Modifier la Catégorie')

    await expect(modal.locator('input[disabled]').first()).toHaveValue('ACCORD_PARTICIPE')

    const selectType = modal.locator('select')
    await selectType.selectOption('Dessin')

    const inputPenalty = modal.locator('input[type="number"]')
    await inputPenalty.fill('3')

    await modal.getByRole('button', { name: 'Enregistrer' }).click()

    await expect(modal).toBeHidden()
    await expect(page.locator('.toast-notification, .notification')).toContainText('mise à jour')
  })

  test('Doit déclencher le recalcul global après confirmation', async ({ page }) => {
    await page.route('**/recalculate*', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500))
      await route.fulfill({ status: 200, json: { success: true } })
    })

    const btnRecalculer = page.locator('.page-header .btn-primary')
    await btnRecalculer.click()

    const btnConfirmer = page.getByRole('button', { name: 'Confirmer' })
    await expect(btnConfirmer).toBeVisible()
    await btnConfirmer.click()

    await expect(btnRecalculer).toContainText('Recalcul en cours...')
    await expect(btnRecalculer).toBeDisabled()

    await expect(page.locator('.toast-notification, .notification')).toContainText(
      'Toutes les copies ont été recalculées',
    )
  })
})
