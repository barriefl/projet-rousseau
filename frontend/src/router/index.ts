import { createRouter, createWebHistory } from 'vue-router'

// LES 4 RUBRIQUES PRINCIPALES.
import DashboardView from '../views/DashboardView.vue'
import EmileDashboardView from '@/views/EmileDashboardView.vue'
import EtudiantsView from '@/views/EtudiantsView.vue'
import GestionEtudiantsView from '@/views/GestionEtudiantsView.vue'

// SOUS-RUBRIQUES DE 'ÉTUDE ROUSSEAU' (DashboardView).
import ImportEtudeView from '@/views/ImportEtudeView.vue'
import ImportResultats from '@/views/ImportResultats.vue'

// SOUS-RUBRIQUES DE 'EMILE DASHBOARD' (DashboardView).
import EmileGestionView from '@/views/EmileGestionView.vue'
import EmileAnalyseView from '@/views/EmileAnalyseView.vue'
import EmileReglesView from '@/views/EmileReglesView.vue'

// PAGES DE 'GESTION DES DICTÉES' (EmileGestionView).
import CorrectionView from '@/views/CorrectionView.vue'
import ImportDicteeView from '@/views/ImportDicteeView.vue'
import ReferenceDicteeView from '@/views/ReferenceDicteeView.vue'

// PAGE DE LOGIN.
import LoginView from '@/views/LoginView.vue'

// PAGE NOT FOUND.
import NotFound from '@/views/NotFoundView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView,
    },
    {
      path: '/import-etude',
      name: 'import-etude',
      component: ImportEtudeView,
    },
    {
      path: '/import-resultats',
      name: 'import-resultats',
      component: ImportResultats,
    },
    {
      path: '/emile',
      name: 'emile-dashboard',
      component: EmileDashboardView,
    },
    {
      path: '/gestion',
      name: 'gestion',
      component: EmileGestionView,
    },
    {
      path: '/correction',
      name: 'correction',
      component: CorrectionView,
    },
    {
      path: '/import-dictee',
      name: 'import-dictee',
      component: ImportDicteeView,
    },
    {
      path: '/dictee-referente',
      name: 'dictee-referente',
      component: ReferenceDicteeView,
    },
    {
      path: '/analyse',
      name: 'analyse',
      component: EmileAnalyseView,
    },
    {
      path: '/regles',
      name: 'regles',
      component: EmileReglesView,
    },
    {
      path: '/etudiants',
      name: 'etudiants',
      component: EtudiantsView,
    },
    {
      path: '/gestion-etudiants',
      name: 'gestion-etudiants',
      component: GestionEtudiantsView,
    },
    {
      path: '/:pathMatch(.*)*', 
      name: 'not-found',
      component: NotFound,
      meta: { requiresAuth: false }
    }
  ],
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('access_token')

  if (to.name !== 'login' && !isAuthenticated) {
    next({ name: 'login' })
  } else if (to.name === 'login' && isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router
