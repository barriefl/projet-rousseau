import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import EmileDashboardView from '@/views/EmileDashboardView.vue'
import EmileGestionView from '@/views/EmileGestionView.vue'
import CorrectionView from '@/views/CorrectionView.vue'
import ImportDicteeView from '@/views/ImportDicteeView.vue'
import ReferenceDicteeView from '@/views/ReferenceDicteeView.vue'
import EmileAnalyseView from '@/views/EmileAnalyseView.vue'
import EmileReglesView from '@/views/EmileReglesView.vue'
import EtudiantsView from '@/views/EtudiantsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView
    },
    {
      path: '/emile',
      name: 'emile-dashboard',
      component: EmileDashboardView
    },
    {
      path: '/gestion',
      name: 'gestion',
      component: EmileGestionView
    },
    {
      path: '/correction',
      name: 'correction',
      component: CorrectionView
    },
    {
      path: '/import-dictee',
      name: 'import-dictee',
      component: ImportDicteeView
    },
    {
      path: '/dictee-referente',
      name: 'dictee-referente',
      component: ReferenceDicteeView
    },
    {
      path: '/analyse',
      name: 'analyse',
      component: EmileAnalyseView
    },
    {
      path: '/regles',
      name: 'regles',
      component: EmileReglesView
    },
    {
      path: '/etudiants',
      name: 'etudiants',
      component: EtudiantsView
    }
  ],
})

export default router
