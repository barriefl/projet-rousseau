<template>
  <div class="emile-dashboard">
    <div class="header">
      <LayoutDashboard :size="28" class="header-icon" />
      <h1>Tableau de Bord É.M.I.L.E.</h1>
    </div>

    <AppLoading v-if="isLoading" message="Récupération des statistiques analytiques..." />

    <AppEmptyState v-else-if="!stats" title="Aucune donnée statistique"
      message="Impossible de charger les données du tableau de bord." action-label="Réessayer" @action="fetchStats" />

    <div v-else>
      <div class="grid-3">
        <div class="card">
          <h3>Total Étudiants</h3>
          <div class="stat-val">{{ stats.total_students }}</div>
          <div class="stat-desc">Ayant passé au moins une dictée</div>
        </div>

        <div class="card">
          <h3>Dictées Traitées</h3>
          <div class="stat-val">{{ stats.total_submissions }}</div>
          <div class="stat-desc">Analysées par É.M.I.L.E.</div>
        </div>

        <div class="card">
          <h3>Moyenne Globale (Malus)</h3>
          <div class="stat-val danger">{{ stats.global_average }} pts</div>
          <div class="stat-desc">Moyenne de toutes les copies</div>
        </div>
      </div>

      <h2 class="section-title">Analyse par Groupe</h2>
      <div class="grid-2">
        <div class="card chart-container">
          <div class="card-header-flex">
            <h3>Répartition des étudiants</h3>
            <select v-model="selectedPromoDist" class="select-filter">
              <option v-for="promo in availablePromos" :key="promo" :value="promo">
                {{ promo }}
              </option>
            </select>
          </div>
          <div class="chart-wrapper">
            <Bar :data="distributionChartData" :options="barOptions" />
          </div>
        </div>

        <div class="card chart-container">
          <h3>Moyenne (Malus) par Groupe</h3>
          <div class="chart-wrapper">
            <Bar :data="averagesChartData" :options="barOptions" />
          </div>
        </div>
      </div>

      <h2 class="section-title">Analyse Pédagogique</h2>
      <div class="grid-2">
        <div class="card chart-container">
          <h3>Comparaison des Promotions</h3>
          <div class="chart-wrapper">
            <Bar :data="promoChartData" :options="barOptions" />
          </div>
        </div>

        <div class="card chart-container">
          <h3>Progrès par méthode de travail</h3>
          <div class="chart-wrapper">
            <Bar :data="motivationChartData" :options="barOptions" />
          </div>
        </div>
      </div>

      <h2 class="section-title">Analyse des Erreurs</h2>
      <div class="card chart-container" style="margin-bottom: 20px;">
        <div class="card-header-flex">
          <h3>Fautes les plus fréquentes (par Typologie et Catégorie)</h3>
          <select v-model="selectedMistakeFilter" class="select-filter">
            <option value="global">Vue Globale (Toutes promos)</option>
            <option v-for="promo in availablePromos" :key="'mistake-' + promo" :value="promo">
              Promotion {{ promo }}
            </option>
          </select>
        </div>
        <div class="chart-wrapper" style="height: 350px;">
          <Bar :data="mistakesChartData" :options="stackedBarOptions" />
        </div>
      </div>

      <h2 class="section-title">Outils & Corrections</h2>
      <div class="grid-2">
        <div class="card chart-container compare-card">
          <h3>Voltaire vs Écri+</h3>
          <div class="chart-wrapper">
            <Bar :data="toolChartData" :options="horizontalBarOptions" />
          </div>
        </div>

        <div class="card chart-container compare-card">
          <h3>Humain vs IA/Outil Automatique</h3>
          <div class="chart-wrapper">
            <Bar :data="humanRobotChartData" :options="horizontalBarOptions" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import api from '@/services/api';

import AppLoading from '@/components/common/AppLoading.vue';
import AppEmptyState from '@/components/common/AppEmptyState.vue';
import { LayoutDashboard } from 'lucide-vue-next';
import type { EmileStatsResponse } from '@/types';

import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement } from 'chart.js';
import { Bar } from 'vue-chartjs';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement);

const isLoading = ref(true);
const stats = ref<EmileStatsResponse | null>(null);

const selectedPromoDist = ref<string>('');
const selectedMistakeFilter = ref<string>('global');

const fetchStats = async () => {
  isLoading.value = true;
  try {
    const res = await api.getEmileDashboardStats();
    stats.value = res;

    if (stats.value?.group_distribution_by_promo) {
      const promos = Object.keys(stats.value.group_distribution_by_promo);
      if (promos.length > 0) {
        selectedPromoDist.value = promos[0] || '';
      }
    }
  } catch (error) {
    console.error("Erreur lors du chargement du tableau de bord :", error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  fetchStats();
});

// Liste de toutes les promos pour les selects
const availablePromos = computed(() => {
  return stats.value?.group_distribution_by_promo ? Object.keys(stats.value.group_distribution_by_promo) : [];
});

// --- DATA POUR LES GRAPHIQUES ---

// 1. Répartition par groupe (Désormais un Bar Chart filtré par Promo)
const distributionChartData = computed(() => {
  const currentStats = stats.value;
  if (!currentStats?.group_distribution_by_promo || !selectedPromoDist.value) return { labels: [], datasets: [] };

  const promoData = currentStats.group_distribution_by_promo[selectedPromoDist.value] || {};

  return {
    labels: Object.keys(promoData),
    datasets: [{
      label: `Étudiants (${selectedPromoDist.value})`,
      data: Object.values(promoData),
      backgroundColor: '#3498db',
      borderRadius: 4
    }]
  };
});

// 2. Moyennes par groupe
const averagesChartData = computed(() => {
  const currentStats = stats.value;
  if (!currentStats?.group_averages) return { labels: [], datasets: [] };
  const labels = Object.keys(currentStats.group_averages);
  return {
    labels: labels,
    datasets: [
      { label: 'Score Initial', data: labels.map(l => currentStats.group_averages[l]?.Initial ?? 0), backgroundColor: '#e74c3c', borderRadius: 4 },
      { label: 'Score Final', data: labels.map(l => currentStats.group_averages[l]?.Final ?? 0), backgroundColor: '#3498db', borderRadius: 4 }
    ]
  };
});

// 3. Moyennes par Promo
const promoChartData = computed(() => {
  const currentStats = stats.value;
  if (!currentStats?.promo_averages) return { labels: [], datasets: [] };
  const labels = Object.keys(currentStats.promo_averages);
  return {
    labels: labels,
    datasets: [
      { label: 'Score Initial', data: labels.map(l => currentStats.promo_averages[l]?.Initial ?? 0), backgroundColor: '#e74c3c', borderRadius: 4 },
      { label: 'Score Final', data: labels.map(l => currentStats.promo_averages[l]?.Final ?? 0), backgroundColor: '#9b59b6', borderRadius: 4 }
    ]
  };
});

// 4. Motivation
const motivationChartData = computed(() => {
  const currentStats = stats.value;
  if (!currentStats?.comparison_motivation) return { labels: [], datasets: [] };
  const labels = Object.keys(currentStats.comparison_motivation);
  return {
    labels: labels,
    datasets: [{
      label: 'Progrès',
      data: labels.map(l => currentStats.comparison_motivation[l] ?? 0),
      backgroundColor: '#2ecc71',
      borderRadius: 4
    }]
  };
});

// 5. Graphique Empilé des Fautes.
const mistakesChartData = computed(() => {
  const currentStats = stats.value;
  if (!currentStats?.mistakes_stats) return { labels: [], datasets: [] };

  const sourceData = selectedMistakeFilter.value === 'global'
    ? currentStats.mistakes_stats.global
    : (currentStats.mistakes_stats.promotions[selectedMistakeFilter.value] || {});

  const typologies = Object.keys(sourceData);
  const datasetsMap: Record<string, number[]> = {};

  typologies.forEach((typo, typoIndex) => {
    const categories = sourceData[typo] || {};
    for (const [catName, count] of Object.entries(categories)) {
      if (!datasetsMap[catName]) {
        datasetsMap[catName] = new Array(typologies.length).fill(0);
      }
      datasetsMap[catName][typoIndex] = count;
    }
  });

  const colors = ['#e74c3c', '#3498db', '#f1c40f', '#2ecc71', '#9b59b6', '#e67e22', '#1abc9c', '#34495e', '#7f8c8d', '#d35400'];

  const datasets = Object.keys(datasetsMap).map((catName, index) => ({
    label: catName,
    data: datasetsMap[catName] ?? [],
    backgroundColor: colors[index % colors.length] ?? '#34495e'
  }));

  return {
    labels: typologies,
    datasets
  };
});

// 6 & 7. Outils & Humain vs Robot
const toolChartData = computed(() => {
  const currentStats = stats.value;
  if (!currentStats?.comparison_tool) return { labels: [], datasets: [] };
  const labels = Object.keys(currentStats.comparison_tool);
  return {
    labels: labels,
    datasets: [
      { label: 'Score Initial', data: labels.map(l => currentStats.comparison_tool[l]?.Initial ?? 0), backgroundColor: '#e74c3c', borderRadius: 4 },
      { label: 'Score Final', data: labels.map(l => currentStats.comparison_tool[l]?.Final ?? 0), backgroundColor: '#2ecc71', borderRadius: 4 }
    ]
  };
});

const humanRobotChartData = computed(() => {
  const currentStats = stats.value;
  if (!currentStats?.comparison_human_robot) return { labels: [], datasets: [] };
  const labels = Object.keys(currentStats.comparison_human_robot);
  return {
    labels: labels,
    datasets: [
      { label: 'Score Initial', data: labels.map(l => currentStats.comparison_human_robot[l]?.Initial ?? 0), backgroundColor: '#e74c3c', borderRadius: 4 },
      { label: 'Score Final', data: labels.map(l => currentStats.comparison_human_robot[l]?.Final ?? 0), backgroundColor: '#34495e', borderRadius: 4 }
    ]
  };
});

// --- OPTIONS DES GRAPHIQUES ---

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: true, position: 'bottom' as const } },
  scales: { y: { beginAtZero: true, title: { display: true, text: 'Points' } } }
};

const horizontalBarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y' as const,
  plugins: { legend: { display: true, position: 'bottom' as const } },
  scales: { x: { beginAtZero: true, title: { display: true, text: 'Points de Malus' } } }
};

// Options spécifiques pour le graphique empilé (Stacked Bar)
const stackedBarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    // On cache la légende si elle est trop grosse, le tooltip suffira pour lire la donnée
    legend: { display: false },
    tooltip: { mode: 'index' as const, intersect: false }
  },
  scales: {
    x: { stacked: true },
    y: { stacked: true, beginAtZero: true, title: { display: true, text: "Nombre d'erreurs commises" } }
  }
};
</script>

<style scoped>
/* En-tête */
.header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 30px;
}

.header-icon {
  color: var(--primary);
}

.header h1 {
  font-size: 1.6rem;
  color: var(--primary);
  margin: 0;
}

/* Nouvel en-tête de carte pour aligner le titre et le dropdown */
.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  border-bottom: 2px solid var(--light);
  padding-bottom: 8px;
}

.card-header-flex h3 {
  margin: 0;
  border-bottom: none;
  padding-bottom: 0;
}

.select-filter {
  padding: 5px 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.9rem;
  outline: none;
  cursor: pointer;
}

/* État vide (Empty State) */
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e1e8ed;
}

.empty-content {
  text-align: center;
  color: #7f8c8d;
}

.empty-icon {
  color: #bdc3c7;
  margin-bottom: 15px;
}

.empty-content p {
  margin-bottom: 20px;
  font-size: 1.1rem;
}

/* Boutons */
.btn {
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  border: none;
  transition: 0.2s;
}

.btn-outline {
  background: transparent;
  border: 1px solid #ccc;
  color: var(--text);
}

.btn-outline:hover {
  background: #f8f9fa;
  border-color: var(--primary);
}

.btn-with-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

/* Titres de section */
.section-title {
  font-size: 1.2rem;
  color: #7f8c8d;
  border-bottom: 2px solid #eee;
  padding-bottom: 5px;
  margin-top: 30px;
  margin-bottom: 15px;
}

/* Grilles */
.grid-3 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

/* Cartes */
.card {
  background: white;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.02);
  border: 1px solid #e1e8ed;
}

.card h3 {
  font-size: 1rem;
  color: var(--primary);
  margin-top: 0;
  margin-bottom: 15px;
  border-bottom: 2px solid var(--light);
  padding-bottom: 8px;
}

/* KPIs */
.stat-val {
  font-size: 2.2rem;
  font-weight: bold;
  color: var(--accent);
  margin-top: 10px;
}

.stat-val.danger {
  color: var(--danger);
}

.stat-desc {
  font-size: 0.85rem;
  color: #7f8c8d;
  margin-top: 5px;
}

/* Chart.js */
.chart-container {
  display: flex;
  flex-direction: column;
}

.chart-wrapper {
  position: relative;
  height: 260px;
  width: 100%;
  display: flex;
  justify-content: center;
}

.compare-card .chart-wrapper {
  height: 200px;
}
</style>