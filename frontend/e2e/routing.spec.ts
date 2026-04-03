import { test, expect } from '@playwright/test'
import { APP_BASE, authenticate } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'

/**
 * Every protected route that should redirect to /login when the user has no token.
 */
const PROTECTED_ROUTES = [
  '/',
  '/import-etude',
  '/import-resultats',
  '/emile',
  '/gestion',
  '/correction',
  '/import-dictee',
  '/dictee-referente',
  '/analyse',
  '/regles',
  '/etudiants',
  '/gestion-etudiants',
]

test.describe('Route Guards', () => {
  // ──────────────────────────────────────────────────────────────
  // Unauthenticated access
  // ──────────────────────────────────────────────────────────────
  test.describe('Unauthenticated access', () => {
    for (const route of PROTECTED_ROUTES) {
      test(`redirects unauthenticated user from "${route}" to /login`, async ({ page }) => {
        await page.goto(`${APP_BASE}${route}`)
        await expect(page).toHaveURL(new RegExp(`${APP_BASE}/login`))
      })
    }

    test('does NOT redirect /login itself to /login (infinite-loop guard)', async ({ page }) => {
      await page.goto(`${APP_BASE}/login`)
      await expect(page).toHaveURL(new RegExp(`${APP_BASE}/login`))
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Authenticated access
  // ──────────────────────────────────────────────────────────────
  test.describe('Authenticated access', () => {
    test.beforeEach(async ({ page }) => {
      await setupApiMocks(page)
      await authenticate(page)
    })

    test('authenticated user can access the dashboard', async ({ page }) => {
      await page.goto(`${APP_BASE}/`)
      await expect(page).not.toHaveURL(new RegExp(`${APP_BASE}/login`))
    })

    test('authenticated user can access /etudiants', async ({ page }) => {
      await page.goto(`${APP_BASE}/etudiants`)
      await expect(page).not.toHaveURL(new RegExp(`${APP_BASE}/login`))
    })

    test('authenticated user can access /gestion', async ({ page }) => {
      await page.goto(`${APP_BASE}/gestion`)
      await expect(page).not.toHaveURL(new RegExp(`${APP_BASE}/login`))
    })

    test('authenticated user can access /regles', async ({ page }) => {
      await page.goto(`${APP_BASE}/regles`)
      await expect(page).not.toHaveURL(new RegExp(`${APP_BASE}/login`))
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Navigation sidebar
  // ──────────────────────────────────────────────────────────────
  test.describe('Sidebar navigation', () => {
    test.beforeEach(async ({ page }) => {
      await setupApiMocks(page)
      await authenticate(page)
      await page.goto(`${APP_BASE}/`)
    })

    test('sidebar is visible with "Projet Rousseau" logo', async ({ page }) => {
      await expect(page.locator('.logo')).toContainText('Projet')
      await expect(page.locator('.logo')).toContainText('Rousseau')
    })

    test('clicking "Étudiants" link navigates to /etudiants', async ({ page }) => {
      await page.locator('.nav-item', { hasText: 'Liste des Étudiants' }).locator('a').click()
      await expect(page).toHaveURL(new RegExp(`${APP_BASE}/etudiants`))
    })

    test('clicking "Gestion des Étudiants" link navigates to /gestion-etudiants', async ({ page }) => {
      await page.locator('.nav-item', { hasText: 'Gestion des Étudiants' }).locator('a').click()
      await expect(page).toHaveURL(new RegExp(`${APP_BASE}/gestion-etudiants`))
    })

    test('ÉMILE sub-menu expands/collapses', async ({ page }) => {
      // Sub-nav should be visible initially (isEmileOpen = true by default)
      const subNav = page.locator('.sub-nav').first()
      await expect(subNav).toBeVisible()

      // Click toggle to collapse
      await page.locator('.nav-item.emile-menu').first().locator('.toggle-btn').click()
      // After animation it should be hidden
      await expect(subNav).toBeHidden()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // 404 page
  // ──────────────────────────────────────────────────────────────
  test.describe('Unknown routes', () => {
    test('renders 404 page for an unmatched route when authenticated', async ({ page }) => {
      await setupApiMocks(page)
      await authenticate(page)
      await page.goto(`${APP_BASE}/this-route-does-not-exist`)

      await expect(page.locator('h1')).toContainText('404')
    })
  })
})
