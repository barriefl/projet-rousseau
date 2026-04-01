import { test, expect } from '@playwright/test';

// --- DONNÉES SIMULÉES (MOCKS). ---
const mockDashboardStats = {
  total_students: 120,
  total_submissions: 345,
  global_average: 14.5,
  group_distribution_by_promo: {
    'BUT 1': { 'G1': 30, 'G2': 30 },
    'BUT 2': { 'G3': 40, 'G4': 20 }
  },
  group_averages: {
    'G1': { Initial: 20, Final: 10 },
    'G2': { Initial: 22, Final: 12 }
  },
  promo_averages: {
    'BUT 1': { Initial: 21, Final: 11 },
    'BUT 2': { Initial: 18, Final: 8 }
  },
  comparison_motivation: {
    'Régulier': 12,
    'Dernière minute': 4
  },
  mistakes_stats: {
    global: {
      'Grammaire': { 'Accord du participe': 150, 'Pluriel': 80 },
      'Lexique': { 'Homophones': 90 }
    },
    promotions: {
      'BUT 1': {
        'Grammaire': { 'Accord du participe': 100, 'Pluriel': 50 },
        'Lexique': { 'Homophones': 60 }
      }
    }
  },
  comparison_tool: {
    'Voltaire': { Initial: 19, Final: 9 },
    'Écri+': { Initial: 22, Final: 11 }
  },
  comparison_human_robot: {
    'Humain': { Initial: 20, Final: 10 },
    'IA': { Initial: 20, Final: 10 }
  }
};

test.describe('Tableau de Bord (É.M.I.L.E.)', () => {

  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('access_token', 'faux-token-e2e-playwright');
    });

    await page.route('**/api/stats/emile*', async (route) => {
      await route.fulfill({ status: 200, json: mockDashboardStats });
    });

    await page.goto('/emile');
  });

  test('Doit afficher les KPIs globaux avec les bonnes valeurs du mock', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Tableau de Bord É.M.I.L.E.');

    const kpiCards = page.locator('.grid-3 .card');
    
    await expect(kpiCards.nth(0)).toContainText('Total Étudiants');
    await expect(kpiCards.nth(0).locator('.stat-val')).toContainText('120');

    await expect(kpiCards.nth(1)).toContainText('Dictées Traitées');
    await expect(kpiCards.nth(1).locator('.stat-val')).toContainText('345');

    await expect(kpiCards.nth(2)).toContainText('Moyenne Globale (Malus)');
    await expect(kpiCards.nth(2).locator('.stat-val')).toContainText('14.5 pts');
    await expect(kpiCards.nth(2).locator('.stat-val')).toHaveClass(/danger/);
  });

  test('Doit afficher les conteneurs de graphiques', async ({ page }) => {
    await expect(page.locator('h2', { hasText: 'Analyse par Groupe' })).toBeVisible();
    await expect(page.locator('h2', { hasText: 'Analyse Pédagogique' })).toBeVisible();
    await expect(page.locator('h2', { hasText: 'Analyse des Erreurs' })).toBeVisible();
    await expect(page.locator('h2', { hasText: 'Outils & Corrections' })).toBeVisible();

    const canvasCount = await page.locator('canvas').count();
    expect(canvasCount).toBe(7);
  });

  test('Doit permettre de filtrer les graphiques via les menus déroulants', async ({ page }) => {
    const distSelect = page.locator('.select-filter').first();
    
    await expect(distSelect).toHaveValue('BUT 1');
    
    await distSelect.selectOption('BUT 2');
    await expect(distSelect).toHaveValue('BUT 2');

    const mistakesSelect = page.locator('.select-filter').last();
    
    await expect(mistakesSelect).toHaveValue('global');

    await mistakesSelect.selectOption('BUT 1');
    await expect(mistakesSelect).toHaveValue('BUT 1');
  });

  test('Doit afficher un état vide (Empty State) si l\'API échoue ou renvoie null', async ({ page }) => {
    await page.route('**/api/stats/emile*', async (route) => {
      await route.fulfill({ status: 500, body: 'Internal Server Error' });
    });

    await page.reload();

    await expect(page.locator('.grid-3')).toBeHidden();
    
    const emptyState = page.locator('.empty-state');
    await expect(emptyState).toBeVisible();
    await expect(emptyState).toContainText('Aucune donnée statistique');
    
    await expect(emptyState.locator('button', { hasText: 'Réessayer' })).toBeVisible();
  });

});