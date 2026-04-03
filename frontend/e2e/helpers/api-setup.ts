import type { Page, Route } from '@playwright/test'
import * as data from './mock-data.js'

const API = 'http://localhost:8000/api'

type MockOverrides = {
  promotions?: unknown
  tools?: unknown
  groups?: unknown
  students?: unknown
  studentsWithScores?: unknown
  studentsProgression?: unknown
  dictations?: unknown
  submissions?: unknown
  categories?: unknown
  rousseauStats?: unknown
  emileStats?: unknown
}

/**
 * Registers Playwright route handlers for all backend API endpoints.
 * Returns sensible default mock data; individual tests can override via `overrides`.
 */
export async function setupApiMocks(page: Page, overrides: MockOverrides = {}): Promise<void> {
  await page.route(`${API}/**`, async (route: Route) => {
    const url = route.request().url()
    const method = route.request().method()

    // ── AUTH ─────────────────────────────────────────────────
    if (url.includes('/auth/login') && method === 'POST') {
      const body = route.request().postDataJSON() as { password?: string } | null
      const formBody = route.request().postData() ?? ''
      const isCorrectPwd = formBody.includes('correct') || formBody.includes('password')
      if (isCorrectPwd) {
        return route.fulfill({ status: 200, json: data.mockAuthResponse })
      }
      return route.fulfill({ status: 401, json: { detail: 'Mot de passe incorrect' } })
    }

    // ── PROMOTIONS ────────────────────────────────────────────
    if (url.match(/\/api\/promotions\/?$/) && method === 'GET') {
      return route.fulfill({ json: overrides.promotions ?? data.mockPromotions })
    }
    if (url.match(/\/api\/promotions\/?$/) && method === 'POST') {
      const body = route.request().postDataJSON() as { name?: string }
      return route.fulfill({ status: 201, json: { id: 99, name: body?.name ?? 'New Promo' } })
    }
    if (url.match(/\/api\/promotions\/\d+/) && method === 'PATCH') {
      const body = route.request().postDataJSON() as { name?: string }
      return route.fulfill({ json: { id: 1, name: body?.name ?? 'Updated Promo' } })
    }
    if (url.match(/\/api\/promotions\/\d+/) && method === 'DELETE') {
      return route.fulfill({ status: 204 })
    }
    if (url.match(/\/api\/promotions\/\d+/) && method === 'GET') {
      return route.fulfill({ json: data.mockPromotions[0] })
    }

    // ── TOOLS ─────────────────────────────────────────────────
    if (url.match(/\/api\/tools\/?$/) && method === 'GET') {
      return route.fulfill({ json: overrides.tools ?? data.mockTools })
    }
    if (url.match(/\/api\/tools\/?$/) && method === 'POST') {
      const body = route.request().postDataJSON() as { name?: string; full_name?: string }
      return route.fulfill({ status: 201, json: { id: 99, name: body?.name, full_name: body?.full_name } })
    }
    if (url.match(/\/api\/tools\/\d+/) && method === 'PATCH') {
      const body = route.request().postDataJSON() as { name?: string; full_name?: string }
      return route.fulfill({ json: { id: 1, name: body?.name ?? 'PV', full_name: body?.full_name ?? 'Projet Voltaire' } })
    }
    if (url.match(/\/api\/tools\/\d+/) && method === 'DELETE') {
      return route.fulfill({ status: 204 })
    }

    // ── GROUPS ────────────────────────────────────────────────
    if (url.match(/\/api\/groups\/?$/) && method === 'GET') {
      return route.fulfill({ json: overrides.groups ?? data.mockGroups })
    }
    if (url.match(/\/api\/groups\/?$/) && method === 'POST') {
      const body = route.request().postDataJSON() as { name?: string; description?: string }
      return route.fulfill({ status: 201, json: { id: 99, name: body?.name, description: body?.description } })
    }
    if (url.match(/\/api\/groups\/\d+/) && method === 'PATCH') {
      const body = route.request().postDataJSON() as { name?: string }
      return route.fulfill({ json: { id: 1, name: body?.name ?? 'G0' } })
    }
    if (url.match(/\/api\/groups\/\d+/) && method === 'DELETE') {
      return route.fulfill({ status: 204 })
    }

    // ── STUDENTS ──────────────────────────────────────────────
    if (url.includes('/students/with-scores') && method === 'GET') {
      return route.fulfill({ json: overrides.studentsWithScores ?? data.mockStudentsWithScores })
    }
    if (url.includes('/students/stats/progression') && method === 'GET') {
      return route.fulfill({ json: overrides.studentsProgression ?? data.mockStudentsProgression })
    }
    if (url.match(/\/api\/students\/?$/) && method === 'GET') {
      return route.fulfill({ json: overrides.students ?? data.mockStudents })
    }
    if (url.match(/\/api\/students\/?$/) && method === 'POST') {
      return route.fulfill({ status: 201, json: { ...data.mockStudents[0], id: 'new-uuid-99' } })
    }
    if (url.match(/\/api\/students\/[a-z0-9-]+/) && method === 'GET') {
      return route.fulfill({ json: data.mockStudents[0] })
    }
    if (url.match(/\/api\/students\/[a-z0-9-]+/) && method === 'PATCH') {
      return route.fulfill({ json: data.mockStudents[0] })
    }
    if (url.match(/\/api\/students\/[a-z0-9-]+/) && method === 'DELETE') {
      return route.fulfill({ status: 204 })
    }

    // ── DICTATIONS ────────────────────────────────────────────
    if (url.match(/\/api\/dictations\/?$/) && method === 'GET') {
      return route.fulfill({ json: overrides.dictations ?? data.mockDictations })
    }
    if (url.match(/\/api\/dictations\/?$/) && method === 'POST') {
      return route.fulfill({ status: 201, json: { id: 99, title: 'New Dictation', content_reference: 'Text' } })
    }
    if (url.includes('/dictations/recalculate') && method === 'POST') {
      return route.fulfill({ json: { detail: 'Toutes les copies ont été recalculées.' } })
    }

    // ── SUBMISSIONS ───────────────────────────────────────────
    if (url.includes('/submissions/bulk') && method === 'POST') {
      return route.fulfill({ status: 201, json: [data.mockSubmissions[0]] })
    }
    if (url.match(/\/api\/submissions\/\d+/) && method === 'GET') {
      return route.fulfill({ json: data.mockSubmissionDetails })
    }
    if (url.match(/\/api\/submissions\/?$/) && method === 'GET') {
      return route.fulfill({ json: overrides.submissions ?? data.mockSubmissions })
    }
    if (url.match(/\/api\/submissions\/?$/) && method === 'POST') {
      return route.fulfill({ status: 201, json: data.mockSubmissions[0] })
    }

    // ── CATEGORIES ────────────────────────────────────────────
    if (url.match(/\/api\/categories\/?/) && method === 'GET') {
      return route.fulfill({ json: overrides.categories ?? data.mockCategories })
    }
    if (url.match(/\/api\/categories\/\d+/) && method === 'PATCH') {
      return route.fulfill({ json: data.mockCategories[0] })
    }

    // ── RULES ─────────────────────────────────────────────────
    if (url.match(/\/api\/rules\/\d+/) && method === 'PATCH') {
      return route.fulfill({ json: { id: 1, is_active: true } })
    }

    // ── STATS ─────────────────────────────────────────────────
    if (url.includes('/stats/rousseau') && method === 'GET') {
      return route.fulfill({ json: overrides.rousseauStats ?? data.mockRousseauStats })
    }
    if (url.includes('/stats/emile') && method === 'GET') {
      return route.fulfill({ json: overrides.emileStats ?? data.mockEmileStats })
    }

    // ── IMPORT ────────────────────────────────────────────────
    if (url.includes('/import/preview') && !url.includes('assessments') && method === 'POST') {
      return route.fulfill({ json: data.mockImportPreview })
    }
    if (url.includes('/import/execute') && !url.includes('assessments') && method === 'POST') {
      return route.fulfill({ json: { status: 'success', created: 1, updated: 1 } })
    }
    if (url.includes('/import/assessments/preview') && method === 'POST') {
      return route.fulfill({ json: data.mockAssessmentPreview })
    }
    if (url.includes('/import/assessments/execute') && method === 'POST') {
      return route.fulfill({ json: { status: 'success', created: 1, updated: 0 } })
    }

    // Fallback: let unhandled routes fail loudly so we can catch missing mocks
    console.warn(`[API MOCK] Unhandled: ${method} ${url}`)
    return route.fulfill({ status: 404, json: { detail: 'Not mocked' } })
  })
}
