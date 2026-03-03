<template>
  <div class="dashboard-etude">
    <div class="header">
      <h1>Étude Rousseau : Analyses et Conclusions</h1>
    </div>

    <AppLoading v-if="isLoading" message="Chargement des graphiques..." />

    <div v-else-if="stats">

      <h2 class="section-title">Hypothèse 1 : Dictées (Var. Principale) vs Outils (Var. Secondaire)</h2>
      <div class="grid-2">
        <div class="card chart-container">
          <h3>Résultats des Dictées (Points)</h3>
          <p class="chart-desc">Malus moyen par promotion (Initial vs Final)</p>
          <div class="chart-wrapper">
            <Bar :data="h1DictationChartData" :options="verticalDictationOptions" />
          </div>
        </div>

        <div class="card chart-container">
          <h3>Progression sur les Outils (%)</h3>
          <p class="chart-desc">Score moyen sur Voltaire / Ecri+ (Initial vs Final)</p>
          <div class="chart-wrapper">
            <Bar :data="h1ToolsChartData" :options="verticalToolsOptions" />
          </div>
        </div>
      </div>

      <h2 class="section-title">Hypothèse 2 : Équivalence Projet Voltaire vs Ecri+ (G2 vs G5)</h2>
      <div class="grid-1">
        <div class="card chart-container">
          <h3>Comparaison Globale par Promotion</h3>
          <p class="chart-desc">Score Final (Barres pleines) et Progrès (Barres claires)</p>
          <div class="chart-wrapper">
            <Bar :data="h2ChartData" :options="barOptions" />
          </div>
        </div>
      </div>

      <h2 class="section-title">Hypothèse 3 : Impact de l'Encadrement</h2>
      <div class="grid-1">
        <div class="card chart-container">
          <h3>Facteur Enseignant (G4 vs G2, G3, G5)</h3>
          <div class="chart-wrapper">
            <Bar :data="h3Data" :options="h3Options" />
          </div>
        </div>
      </div>

      <div class="h4-section-header">
        <h2 class="section-title">Hypothèse 4 : Variables Socioculturelles</h2>
        <div class="h4-controls">
          <label><input type="checkbox" value="Initial" v-model="h4Metrics"> Score Initial</label>
          <label><input type="checkbox" value="Progress" v-model="h4Metrics"> Progression</label>
        </div>
      </div>

      <div class="grid-2">
        <div class="card chart-container" v-for="(cats, fam) in stats.h4_sociocultural" :key="fam">
          <div class="header-with-select">
            <h3>{{ fam }}</h3>
            <select v-model="selectedH4[fam]" class="socio-select min-select">
              <option v-for="cat in Object.keys(cats)" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>
          <div class="chart-wrapper">
            <Bar :data="getH4Data(fam)" :options="horizontalOptions" />
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import api from '@/services/api';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';
import type { ChartData, ChartOptions } from 'chart.js';
import { Bar } from 'vue-chartjs';
import AppLoading from '@/components/common/AppLoading.vue';
import type { RousseauStats } from '@/types';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

// --- ÉTATS. ---
const isLoading = ref(true);
const stats = ref<RousseauStats | null>(null);
const h4Metrics = ref<string[]>(['Initial', 'Progress']);
const selectedH4 = reactive<Record<string, string>>({});

onMounted(async () => {
  try {
    const res = await api.getRousseauStats();
    const fetchedData = res as RousseauStats;
    stats.value = fetchedData;

    if (fetchedData.h4_sociocultural) {
      Object.keys(fetchedData.h4_sociocultural).forEach(f => {
        const categories = fetchedData.h4_sociocultural[f];
        if (categories) {
          selectedH4[f] = Object.keys(categories)[0] ?? "";
        }
      });
    }
  } catch (error) {
    console.error("Erreur API:", error);
  } finally {
    isLoading.value = false;
  }
});

// --- LOGIQUE H1. ---
const h1DictationChartData = computed<ChartData<'bar'>>(() => {
  const s = stats.value?.h1_summary;
  if (!s) return { labels: [], datasets: [] };
  return {
    labels: s.labels,
    datasets: [
      { label: 'Dictée Initiale', data: s.dictation_initial, backgroundColor: '#e74c3c', borderRadius: 4 },
      { label: 'Dictée Finale', data: s.dictation_final, backgroundColor: '#c0392b', borderRadius: 4 }
    ]
  };
});

const h1ToolsChartData = computed<ChartData<'bar'>>(() => {
  const s = stats.value?.h1_summary;
  if (!s) return { labels: [], datasets: [] };
  return {
    labels: s.labels,
    datasets: [
      { label: 'Outil Initial', data: s.tools_initial.map(v => v * 100), backgroundColor: '#3498db', borderRadius: 4 },
      { label: 'Outil Final', data: s.tools_final.map(v => v * 100), backgroundColor: '#2980b9', borderRadius: 4 }
    ]
  };
});

const verticalDictationOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' } },
  scales: { y: { beginAtZero: true, title: { display: true, text: 'Points de Malus' } } }
};

const verticalToolsOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' } },
  scales: { y: { min: 0, max: 100, title: { display: true, text: 'Score Outils (%)' } } }
};

// --- LOGIQUE H2. ---
const h2ChartData = computed<ChartData<'bar'>>(() => {
  const s = stats.value?.h2_equivalence;
  if (!s) return { labels: [], datasets: [] };
  return {
    labels: s.labels,
    datasets: [
      { label: 'Voltaire Final', data: s.g2_final, backgroundColor: '#3498db', borderRadius: 4 },
      { label: 'Voltaire Progrès', data: s.g2_progress, backgroundColor: '#85c1e9', borderRadius: 4 },
      { label: 'Ecri+ Final', data: s.g5_final, backgroundColor: '#9b59b6', borderRadius: 4 },
      { label: 'Ecri+ Progrès', data: s.g5_progress, backgroundColor: '#c39bd3', borderRadius: 4 },
    ]
  };
});

// --- LOGIQUE H3. ---
const h3Data = computed<ChartData<'bar'>>(() => ({
  labels: Object.keys(stats.value?.h3_teacher || {}),
  datasets: [{
    label: 'Malus Final',
    data: Object.values(stats.value?.h3_teacher || {}),
    backgroundColor: ['#f39c12', '#e67e22'],
    borderRadius: 6,
    barPercentage: 0.4,
    categoryPercentage: 0.6
  }]
}));

const h3Options: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true, title: { display: true, text: 'Points de Malus' } } }
};

// --- LOGIQUE H4. ---
const getH4Data = (fam: string): ChartData<'bar'> => {
  if (!stats.value?.h4_sociocultural) return { labels: [], datasets: [] };

  const familyData = stats.value.h4_sociocultural[fam];
  const currentSubCategory = selectedH4[fam];

  if (!familyData || !currentSubCategory || !familyData[currentSubCategory]) {
    return { labels: [], datasets: [] };
  }

  const d = familyData[currentSubCategory];
  const datasets = [];

  if (h4Metrics.value.includes('Initial')) {
    datasets.push({ label: 'Initial', data: Object.values(d).map(v => v.Initial), backgroundColor: '#34495e', borderRadius: 4 });
  }
  if (h4Metrics.value.includes('Progress')) {
    datasets.push({ label: 'Progression', data: Object.values(d).map(v => v.Progress), backgroundColor: '#1abc9c', borderRadius: 4 });
  }
  return { labels: Object.keys(d), datasets };
};

const barOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' } }
};

const horizontalOptions: ChartOptions<'bar'> = {
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' } }
};
</script>

<style scoped>
.header {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.section-title {
  font-size: 1.2rem;
  color: #7f8c8d;
  border-bottom: 2px solid #eee;
  padding-bottom: 5px;
  margin-top: 40px;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 20px;
}

.grid-1 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.card {
  background: white;
  padding: 30px;
  border-radius: 8px;
  border: 1px solid #e1e8ed;
  margin-top: 15px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

.chart-wrapper {
  height: 320px;
  position: relative;
  margin-top: 10px;
}

.socio-select {
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #ddd;
  background: #f8f9fa;
}

.h4-section-header {
  margin-top: 40px;
  margin-bottom: 20px;
}

.h4-section-header .section-title {
  border-bottom: none;
  margin-bottom: 5px;
}

.h4-controls {
  display: flex;
  gap: 25px;
  padding-bottom: 20px;
  margin-bottom: 25px;
  border-bottom: 2px solid #eee;
}

.h4-controls label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #7f8c8d;
  font-weight: 500;
  font-size: 0.95rem;
}

.h4-controls input {
  width: 16px;
  height: 16px;
}

.header-with-select {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.chart-desc {
  font-size: 0.9rem;
  color: #95a5a6;
  margin-bottom: 10px;
}
</style>