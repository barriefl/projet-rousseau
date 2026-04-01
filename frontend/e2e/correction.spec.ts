import { test, expect } from '@playwright/test'

// --- DONNÉES SIMULÉES (MOCKS). ---
const mockStudents = [
  {
    id: 'student-1',
    first_name: 'Jean',
    last_name: 'Dupont',
    promotion_name: 'BUT 1',
    group_display: 'G1',
    initial_score: 12,
    final_score: 4,
  },
  {
    id: 'student-2',
    first_name: 'Marie',
    last_name: 'Curie',
    promotion_name: 'BUT 2',
    group_display: 'G2',
    initial_score: 2,
    final_score: 0,
  },
]

const mockSubmissions = [
  {
    id: 101,
    assessment_type: 'Initiale',
    created_at: '2024-09-01T10:00:00Z',
  },
]

const mockSubmissionDetails = {
  id: 101,
  html_text:
    'Il était une <span class="faute" data-type="Règle" data-malus="2" data-corr="fois" data-desc="Accord orthographique" data-rule-id="RULE_1">foi</span> dans l\'ouest.',
  final_score: 2,
  scores: {
    Règle: 2,
  },
  mistakes: [
    {
      student_word: 'foi',
      correct_word: 'fois',
      type_rousseau: 'Règle',
      malus_applied: 2,
      position_index: 0,
      rule_id_lt: 'RULE_1',
    },
  ],
}

test.describe('Page Correction (É.M.I.L.E.)', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('access_token', 'faux-token-e2e-playwright');
    });

    await page.route('**/api/students/with-scores', async (route) => {
      await route.fulfill({ status: 200, json: mockStudents })
    })

    await page.route('**/api/submissions?student_uuid=*', async (route) => {
      await route.fulfill({ status: 200, json: mockSubmissions })
    })

    await page.route(/\/api\/submissions\/\d+/, async (route) => {
      await route.fulfill({ status: 200, json: mockSubmissionDetails })
    })

    await page.goto('/correction')
  })

  test('Doit afficher les éléments principaux et la liste des étudiants', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('É.M.I.L.E.')

    const student1 = page.locator('.student-card').filter({ hasText: 'Dupont Jean' })
    const student2 = page.locator('.student-card').filter({ hasText: 'Curie Marie' })

    await expect(student1).toBeVisible()
    await expect(student2).toBeVisible()

    await expect(student1.locator('.score-badge').first()).toContainText('I : 12')
  })

  test('Doit filtrer les étudiants via la barre de recherche', async ({ page }) => {
    const searchInput = page.getByPlaceholder('Rechercher un étudiant par nom...')

    await searchInput.fill('Curie')

    await expect(page.locator('.student-card').filter({ hasText: 'Curie Marie' })).toBeVisible()
    await expect(page.locator('.student-card').filter({ hasText: 'Dupont Jean' })).toBeHidden()
  })

  test("Doit afficher les dictées d'un étudiant lors du clic sur sa carte", async ({ page }) => {
    await page.locator('.student-card').filter({ hasText: 'Dupont Jean' }).click()

    await expect(page.locator('.dictation-selector')).toBeVisible()
    await expect(page.locator('.dictation-selector h4')).toContainText('Dictées de Dupont Jean')

    const dictationBtn = page.locator('.dictation-btn').filter({ hasText: 'Dictée Initiale' })
    await expect(dictationBtn).toBeVisible()
  })

  test('Doit afficher les détails de la correction lors du clic sur une dictée', async ({
    page,
  }) => {
    await page.locator('.student-card').filter({ hasText: 'Dupont Jean' }).click()
    await page.locator('.dictation-btn').filter({ hasText: 'Dictée Initiale' }).click()

    await expect(page.locator('.atelier-container')).toBeVisible()

    await expect(page.locator('.score-display span')).toContainText('2 pts')

    await expect(page.locator('.panel').filter({ hasText: 'Règle' })).toContainText('+2')

    const errorItem = page.locator('.error-item').first()
    await expect(errorItem).toContainText('foi')
    await expect(errorItem).toContainText('Correction : fois (+2)')
    await expect(errorItem).toContainText('Règle : RULE_1')
  })

  test("Doit afficher une infobulle (tooltip) au survol d'une faute dans le texte", async ({
    page,
  }) => {
    await page.locator('.student-card').filter({ hasText: 'Dupont Jean' }).click()
    await page.locator('.dictation-btn').filter({ hasText: 'Dictée Initiale' }).click()

    const fauteElement = page.locator('.faute').first()
    await expect(fauteElement).toContainText('foi')

    await fauteElement.hover()

    const tooltip = page.locator('.reverso-tooltip')
    await expect(tooltip).toBeVisible()
    await expect(tooltip).toContainText("Type 'Règle'")
    await expect(tooltip).toContainText('+2 pt')
    await expect(tooltip.locator('.correction')).toContainText("fois");
    await expect(tooltip).toContainText('Accord orthographique')
  })

  test('Doit retourner à la gestion au clic sur le bouton Retour', async ({ page }) => {
    const btnRetour = page.getByRole('button', { name: '← Retour' })

    await btnRetour.click()
    await expect(page).toHaveURL(/.*\/gestion/)
  })
})
