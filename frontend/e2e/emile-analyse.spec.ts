import { test, expect } from '@playwright/test'

// --- DONNÉES SIMULÉES (MOCKS). ---
const mockProgressionData = [
  {
    id: 'uuid-1',
    first_name: 'Jean',
    last_name: 'Dupont',
    group_name: 'G1',
    group_display: 'G1',
    score_initial: 20,
    score_final: 5,
    progress: -15,
  },
  {
    id: 'uuid-2',
    first_name: 'Marie',
    last_name: 'Curie',
    group_name: 'G2',
    group_display: 'G2',
    score_initial: 10,
    score_final: 15,
    progress: 5,
  },
  {
    id: 'uuid-3',
    first_name: 'Albert',
    last_name: 'Einstein',
    group_name: 'G1',
    group_display: 'G1',
    score_initial: null,
    score_final: null,
    progress: null,
  },
]

test.describe('Page Analyse des Travaux (É.M.I.L.E.)', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('access_token', 'faux-token-e2e-playwright')
    })

    await page.route('**/api/students/stats/progression', async (route) => {
      await route.fulfill({ status: 200, json: mockProgressionData })
    })

    await page.goto('/analyse')
  })

  test('Doit afficher les KPIs avec les bons calculs globaux', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Analyse des travaux')
    await expect(page.locator('.kpi-card').nth(0)).toContainText('3')
    await expect(page.locator('.kpi-card').nth(1)).toContainText('15 pts');
    await expect(page.locator('.kpi-card').nth(2)).toContainText('10 pts');

    const progressKpi = page.locator('.kpi-card').nth(3)
    await expect(progressKpi).toContainText('-5 pts');
    await expect(progressKpi.locator('.kpi-value')).toHaveClass(/text-success/)
  })

  test('Doit lister les étudiants avec le bon formatage de scores et de badges', async ({
    page,
  }) => {
    const table = page.locator('.data-table')
    await expect(table).toBeVisible()

    const rowDupont = table.locator('tr', { hasText: 'Dupont Jean' })
    await expect(rowDupont.locator('td').nth(2)).toContainText('20 pts')
    await expect(rowDupont.locator('td').nth(3)).toContainText('5 pts')
    const badgeDupont = rowDupont.locator('.badge-progress')
    await expect(badgeDupont).toContainText('-15')
    await expect(badgeDupont).toHaveClass(/bg-success/)

    const rowCurie = table.locator('tr', { hasText: 'Curie Marie' })
    const badgeCurie = rowCurie.locator('.badge-progress')
    await expect(badgeCurie).toContainText('+5')
    await expect(badgeCurie).toHaveClass(/bg-danger/)

    const rowEinstein = table.locator('tr', { hasText: 'Einstein Albert' })
    await expect(rowEinstein.locator('td').nth(2)).toContainText('Non passée')
    await expect(rowEinstein.locator('td').nth(4)).toContainText('-')
  })

  test('Doit filtrer correctement les étudiants via la barre de recherche', async ({ page }) => {
    const searchInput = page.getByPlaceholder('Rechercher un étudiant ou un groupe...')

    await searchInput.fill('jean')
    await expect(
      page.locator('.data-table').locator('tr', { hasText: 'Dupont Jean' }),
    ).toBeVisible()
    await expect(page.locator('.data-table').locator('tr', { hasText: 'Curie Marie' })).toBeHidden()

    await searchInput.fill('g2')
    await expect(
      page.locator('.data-table').locator('tr', { hasText: 'Curie Marie' }),
    ).toBeVisible()
    await expect(page.locator('.data-table').locator('tr', { hasText: 'Dupont Jean' })).toBeHidden()

    await searchInput.fill('Fantôme')
    await expect(page.locator('.empty-state')).toBeVisible()
    await expect(page.locator('.empty-state')).toContainText('Aucun étudiant')
  })

  test('Doit retourner à la page de gestion au clic sur le bouton Retour', async ({ page }) => {
    const btnRetour = page.getByRole('button', { name: '← Retour' })

    await btnRetour.click()
    await expect(page).toHaveURL(/.*\/gestion/)
  })
})
