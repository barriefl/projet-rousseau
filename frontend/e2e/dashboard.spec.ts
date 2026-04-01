import { test, expect } from '@playwright/test';

// --- DONNÉES SIMULÉES (MOCKS). ---
const mockRousseauStats = {
  h1_summary: {
    labels: ['BUT 1', 'BUT 2'],
    effectif: [150, 120],
    dictation_initial: [45.5, 50.2],
    dictation_final: [65.0, 68.5],
    tools_initial: [0.35, 0.40],
    tools_final: [0.65, 0.70]
  },
  h2_equivalence: {
    labels: ['G2', 'G5'],
    effectif: [40, 45],
    g2_final: [68],
    g2_progress: [20],
    g5_final: [66],
    g5_progress: [18]
  },
  h2_boxplots: {
    'G2': { initial: [20,30,40], final: [50,60,70], delta: [10,20,30] }
  },
  h2_stats_test: {
    anova: {
      p_value: 0.035,
      is_significant: true
    },
    tukey: [
      { group1: 'G2', group2: 'G5', p_value: 0.035, conclusion: 'G2 a une progression significativement différente de G5' }
    ]
  },
  h3_teacher: {
    'Professeur A': { effectif: 60, score: 72.5 },
    'Professeur B': { effectif: 85, score: 68.0 }
  },
  h4_sociocultural: {
    'Genre': {
      'Féminin': { Initial: 55, Progress: 18, Effectif: 90 },
      'Masculin': { Initial: 50, Progress: 15, Effectif: 80 }
    }
  },
  anova_multifactorial: [
    { factor: 'Série Bac', impact_percent: 25.5, p_value: 0.0001, is_significant: true },
    { factor: 'Boursier', impact_percent: 2.1, p_value: 0.45, is_significant: false }
  ],
  regression_model: {
    r2: 0.45,
    coefficients: [
      { feature: 'Série Bac_Générale', weight: 8.5 },
      { feature: 'Boursier_Oui', weight: -1.2 }
    ]
  }
};

test.describe('Page Dashboard (Étude Rousseau)', () => {

  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('access_token', 'faux-token-e2e-playwright');
      window.sessionStorage.clear(); 
    });

    await page.route('**/api/stats/rousseau', async (route) => {
      await route.fulfill({ status: 200, json: mockRousseauStats });
    });

    await page.goto('/');
  });

  test('Doit afficher les titres principaux et les conteneurs de graphiques', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Étude Rousseau : Analyses et Conclusions');

    await expect(page.locator('h2').filter({ hasText: 'Hypothèse 1' })).toBeVisible();
    await expect(page.locator('h2').filter({ hasText: 'Hypothèse 2' })).toBeVisible();
    await expect(page.locator('h2').filter({ hasText: 'Hypothèse 3' })).toBeVisible();
    await expect(page.locator('h2').filter({ hasText: 'Hypothèse 4' })).toBeVisible();

    const canvasCount = await page.locator('canvas').count();
    expect(canvasCount).toBeGreaterThan(0);
  });

  test('Doit afficher le verdict statistique (ANOVA) pour l\'Hypothèse 2', async ({ page }) => {
    const verdictBox = page.locator('.verdict-box.significant');
    
    await expect(verdictBox).toBeVisible();
    await expect(verdictBox).toContainText('Différence significative détectée !');
    await expect(verdictBox).toContainText('p = 0.035');
    
    const tukeyItem = page.locator('.tukey-list li').first();
    await expect(tukeyItem).toContainText('G2 a une progression');
  });

  test('Doit permettre d\'interagir avec les contrôles de l\'Hypothèse 4', async ({ page }) => {
    const progressCheckbox = page.locator('label').filter({ hasText: 'Progression (%)' }).locator('input');
    await expect(progressCheckbox).toBeChecked();
    await progressCheckbox.uncheck();
    await expect(progressCheckbox).not.toBeChecked();

    const btnInitialSort = page.locator('.btn-toggle-group button').filter({ hasText: 'Score Initial' });
    const btnEffectifSort = page.locator('.btn-toggle-group button').filter({ hasText: 'Effectif' });

    await expect(btnEffectifSort).toHaveClass(/active/);
    
    await btnInitialSort.click();
    
    await expect(btnInitialSort).toHaveClass(/active/);
    await expect(btnEffectifSort).not.toHaveClass(/active/);

    const selectGenre = page.locator('.socio-select').first();
    await expect(selectGenre).toBeVisible();
  });

  test('Doit afficher correctement la liste des facteurs ANOVA (Déterminisme)', async ({ page }) => {
    const significantFactor = page.locator('.factor-row.is-significant');
    await expect(significantFactor).toBeVisible();
    await expect(significantFactor.locator('.factor-name')).toContainText('Série Bac');
    await expect(significantFactor.locator('.impact-badge')).toContainText('25.5%');

    const nonSignificantFactor = page.locator('.factor-row:not(.is-significant)').first();
    await expect(nonSignificantFactor).toBeVisible();
    await expect(nonSignificantFactor.locator('.factor-name')).toContainText('Boursier');
  });

  test('Doit afficher les données du modèle prédictif (Régression Multiple)', async ({ page }) => {
    const regressionSection = page.locator('.card', { hasText: 'Importance des variables' });
    await expect(regressionSection).toBeVisible();

    await expect(regressionSection).toContainText('Score de fiabilité ($R^2$) : 45.0 %');
  });

});