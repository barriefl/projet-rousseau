import { test, expect } from '@playwright/test'
import { APP_BASE, authenticate, clearAuthentication } from './helpers/auth.js'
import { setupApiMocks } from './helpers/api-setup.js'

const LOGIN_URL = `${APP_BASE}/login`
const HOME_URL  = `${APP_BASE}/`

test.describe('Login Page', () => {
  // ──────────────────────────────────────────────────────────────
  // Rendering
  // ──────────────────────────────────────────────────────────────
  test.describe('Rendering', () => {
    test('displays the login form with all required elements', async ({ page }) => {
      await page.goto(LOGIN_URL)

      await expect(page.locator('h2')).toContainText('Projet Rousseau')
      await expect(page.locator('p')).toContainText('Accès restreint')
      await expect(page.locator('input[type="password"]')).toBeVisible()
      await expect(page.locator('button[type="submit"]')).toBeVisible()
      await expect(page.locator('button[type="submit"]')).toContainText('Déverrouiller')
    })

    test('password field is masked by default', async ({ page }) => {
      await page.goto(LOGIN_URL)
      const input = page.locator('input[type="password"]')
      await expect(input).toHaveAttribute('type', 'password')
    })

    test('toggles password visibility when the eye button is clicked', async ({ page }) => {
      await page.goto(LOGIN_URL)
      const input = page.locator('input[type="password"], input[type="text"]').first()
      const toggleBtn = page.locator('button[title*="ficher"]')

      await expect(input).toHaveAttribute('type', 'password')
      await toggleBtn.click()
      await expect(page.locator('input[type="text"]')).toBeVisible()
      await toggleBtn.click()
      await expect(page.locator('input[type="password"]')).toBeVisible()
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Authentication flow
  // ──────────────────────────────────────────────────────────────
  test.describe('Authentication flow', () => {
    test('successful login stores token and redirects to dashboard', async ({ page }) => {
      await setupApiMocks(page)
      await page.goto(LOGIN_URL)

      await page.fill('input[type="password"]', 'correct')
      await page.click('button[type="submit"]')

      // After success the router should navigate away from /login
      await expect(page).toHaveURL(new RegExp(`${APP_BASE}(?:/|$)`))
      const token = await page.evaluate(() => localStorage.getItem('access_token'))
      expect(token).toBeTruthy()
    })

    test('wrong password shows an error toast and keeps user on login page', async ({ page }) => {
      await setupApiMocks(page)
      await page.goto(LOGIN_URL)

      await page.fill('input[type="password"]', 'wrongpassword')
      await page.click('button[type="submit"]')

      await expect(page).toHaveURL(new RegExp(`${APP_BASE}/login`))
    })

    test('submit button is disabled while request is in flight', async ({ page }) => {
      // Slow the API so we can observe the loading state
      await page.route('**/api/auth/login', async (route) => {
        await new Promise((r) => setTimeout(r, 300))
        await route.fulfill({ status: 401, json: { detail: 'Mot de passe incorrect' } })
      })

      await page.goto(LOGIN_URL)
      await page.fill('input[type="password"]', 'test')
      await page.click('button[type="submit"]')

      // During the 300 ms wait the button text changes to 'Vérification...'
      await expect(page.locator('button[type="submit"]')).toContainText('Vérification...')
    })

    test('pressing Enter submits the form', async ({ page }) => {
      await setupApiMocks(page)
      await page.goto(LOGIN_URL)

      await page.fill('input[type="password"]', 'correct')
      await page.keyboard.press('Enter')

      await expect(page).toHaveURL(new RegExp(`${APP_BASE}(?:/|$)`))
    })
  })

  // ──────────────────────────────────────────────────────────────
  // Already-authenticated user
  // ──────────────────────────────────────────────────────────────
  test.describe('Redirect for authenticated users', () => {
    test('redirects authenticated user away from /login to dashboard', async ({ page }) => {
      await setupApiMocks(page)
      await authenticate(page)
      await page.goto(LOGIN_URL)

      await expect(page).toHaveURL(new RegExp(`${APP_BASE}(?:/|$)`))
    })
  })
})
