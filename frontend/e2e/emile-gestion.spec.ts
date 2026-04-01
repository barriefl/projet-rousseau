import { test, expect } from '@playwright/test'

test.describe('Page Gestion des Dictées (Menu principal)', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('access_token', 'faux-token-e2e-playwright')
    })

    await page.goto('/gestion')
  })

  test("Doit afficher le titre et les 3 cartes d'action", async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Gestion des Dictées')

    const cards = page.locator('.action-card')
    await expect(cards).toHaveCount(3)

    await expect(cards.nth(0).locator('h3')).toContainText('Consulter une dictée')
    await expect(cards.nth(0).locator('p')).toContainText('Consulter les corrections')

    await expect(cards.nth(1).locator('h3')).toContainText('Importer une dictée')
    await expect(cards.nth(1).locator('p')).toContainText('Ajouter et analyser le texte')

    await expect(cards.nth(2).locator('h3')).toContainText('Dictée Référente')
    await expect(cards.nth(2).locator('p')).toContainText('Définir le texte référent')
  })

  test('Doit rediriger vers la page de correction au clic sur "Consulter"', async ({ page }) => {
    const card = page.locator('.action-card', { hasText: 'Consulter une dictée' })
    await card.click()

    await expect(page).toHaveURL(/.*\/correction/)
  })

  test('Doit rediriger vers la page d\'import au clic sur "Importer"', async ({ page }) => {
    const card = page.locator('.action-card', { hasText: 'Importer une dictée' })
    await card.click()

    await expect(page).toHaveURL(/.*\/import-dictee/)
  })

  test('Doit rediriger vers la page de référence au clic sur "Dictée Référente"', async ({
    page,
  }) => {
    const card = page.locator('.action-card', { hasText: 'Dictée Référente' })
    await card.click()

    await expect(page).toHaveURL(/.*\/dictee-referente/)
  })
})
