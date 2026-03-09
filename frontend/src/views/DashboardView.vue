<template>
  <div class="dashboard-etude">
    <div class="page-header">
      <h1>Étude Rousseau : Analyses et Conclusions</h1>
    </div>

    <AppLoading v-if="isLoading" message="Chargement des graphiques..." />

    <AppEmptyState v-else-if="!stats" title="Aucune donnée statistique"
      message="Impossible de charger les données de l'étude." :showRetry="true" :loading="isLoading"
      @retry="fetchStudy" />

    <div v-else>

      <h2 class="section-title">Hypothèse 1 : Dictées (Var. Principale) vs Outils (Var. Secondaire)</h2>
      <div class="grid-2">
        <div class="card chart-container">
          <h3>Progression des dictées (en %)</h3>
          <p class="chart-desc">Précision moyen (%) par promotion (Initial vs Final)</p>
          <div class="chart-wrapper">
            <Bar :data="h1DictationChartData" :options="verticalDictationOptions" />
          </div>
        </div>

        <div class="card chart-container">
          <h3>Progression sur les outils (en %)</h3>
          <p class="chart-desc">Score moyen (%) sur Voltaire / Ecri+ (Initial vs Final)</p>
          <div class="chart-wrapper">
            <Bar :data="h1ToolsChartData" :options="verticalToolsOptions" />
          </div>
        </div>
      </div>

      <h2 class="section-title">Hypothèse 2 : Équivalence Projet Voltaire vs Ecri+ (G2 vs G5)</h2>
      <div class="grid-1">

        <div class="card chart-container">
          <h3>Distribution des scores (tous les groupes)</h3>
          <p class="chart-desc">Médiane, quartiles et valeurs extrêmes</p>
          <div class="chart-wrapper">
            <Chart type="boxplot" :data="h2BoxplotChartData" :options="boxplotOptions" />
          </div>
        </div>

        <div class="card chart-container">
          <h3>Comparaison Globale</h3>
          <p class="chart-desc">Score Final (Barres pleines) et Progrès (Barres claires) en %</p>
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
          <label><input type="checkbox" value="Initial" v-model="h4Metrics"> Score Initial (%)</label>
          <label><input type="checkbox" value="Progress" v-model="h4Metrics"> Progression (%)</label>
        </div>

        <div class="h4-advanced-controls">
          <div class="sort-group">
            <span class="control-label">Trier par :</span>
            <div class="btn-toggle-group">
              <button :class="{ active: h4SortBy === 'Initial' }" @click="h4SortBy = 'Initial'">Score Initial</button>
              <button :class="{ active: h4SortBy === 'Progress' }" @click="h4SortBy = 'Progress'">Progression</button>
              <button :class="{ active: h4SortBy === 'Effectif' }" @click="h4SortBy = 'Effectif'">Effectif</button>
            </div>
          </div>

          <label class="toggle-thickness">
            <input type="checkbox" v-model="useThicknessScaling">
            <span>Épaisseur proportionnelle à l'effectif</span>
          </label>
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
import type { ChartData, ChartOptions, ChartDataset, TooltipItem } from 'chart.js';
import { Bar, Chart } from 'vue-chartjs';
import { BoxPlotController, BoxAndWiskers } from '@sgratzl/chartjs-chart-boxplot';

import AppLoading from '@/components/common/AppLoading.vue';
import AppEmptyState from '@/components/common/AppEmptyState.vue';

import type { CustomDataset, CustomBarElement, RousseauStats } from '@/types';

const variableThicknessPlugin = {
  id: 'variableThickness',

  beforeDatasetsDraw(chart: ChartJS) {
    chart.data.datasets.forEach((baseDataset, di: number) => {
      const dataset = baseDataset as typeof baseDataset & CustomDataset;
      const meta = chart.getDatasetMeta(di);

      const effectifData = dataset.effectifData;

      if (!meta?.data?.length || !effectifData || !dataset.useScaling) return;

      meta.data.forEach((element, i: number) => {
        const bar = element as BarElement & CustomBarElement;

        if (bar._originalHeight === undefined || bar.height > bar._originalHeight) {
          bar._originalHeight = bar.height;
        }

        const n = effectifData[i] ?? 1;
        const maxN = dataset.maxEffectif ?? 1;
        const ratio = Math.sqrt(n) / Math.sqrt(maxN);
        bar.height = Math.max(bar._originalHeight * 0.15, bar._originalHeight * ratio * 0.9);
      });
    });
  }
};

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, BoxPlotController, BoxAndWiskers, variableThicknessPlugin);

// --- ÉTATS. ---
const isLoading = ref(true);
const stats = ref<RousseauStats | null>(null);
const h4Metrics = ref<string[]>(['Initial', 'Progress']);
const selectedH4 = reactive<Record<string, string>>({});
const h4SortBy = ref<'Initial' | 'Progress' | 'Effectif'>('Effectif');
const useThicknessScaling = ref(true);

const fetchStudy = async () => {
  isLoading.value = true;
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
};

onMounted(() => {
  fetchStudy();
})

// --- LOGIQUE H1. ---
const h1DictationChartData = computed<ChartData<'bar'>>(() => {
  const s = stats.value?.h1_summary;
  if (!s) return { labels: [], datasets: [] };

  const labelsWithN = s.labels.map((label, i) => `${label} (${s.effectif[i]})`);

  return {
    labels: labelsWithN,
    datasets: [
      { label: 'Dictée Initiale (%)', data: s.dictation_initial, backgroundColor: '#e74c3c', borderRadius: 4 },
      { label: 'Dictée Finale (%)', data: s.dictation_final, backgroundColor: '#c0392b', borderRadius: 4 }
    ]
  };
});

const h1ToolsChartData = computed<ChartData<'bar'>>(() => {
  const s = stats.value?.h1_summary;
  if (!s) return { labels: [], datasets: [] };

  const labelsWithN = s.labels.map((label, i) => `${label} (${s.effectif[i]})`);

  return {
    labels: labelsWithN,
    datasets: [
      { label: 'Outil Initial (%)', data: s.tools_initial.map(v => v * 100), backgroundColor: '#3498db', borderRadius: 4 },
      { label: 'Outil Final (%)', data: s.tools_final.map(v => v * 100), backgroundColor: '#2980b9', borderRadius: 4 }
    ]
  };
});

const getOptionsWithEffectif = (axisTitle: string, effectifArrayKey: 'h1_summary' | 'h2_equivalence'): ChartOptions<'bar'> => ({
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' },
    tooltip: {
      callbacks: {
        afterLabel: function (context) {
          const index = context.dataIndex;
          const effectif = stats.value?.[effectifArrayKey]?.effectif?.[index] || 0;
          return `Effectif total de la promo : ${effectif} étudiants`;
        }
      }
    }
  },
  scales: { y: { beginAtZero: true, title: { display: true, text: axisTitle } } }
});

const verticalDictationOptions = computed(() => getOptionsWithEffectif('Précision (%)', 'h1_summary'));
const verticalToolsOptions = computed(() => getOptionsWithEffectif('Score Outils (%)', 'h1_summary'));

// --- LOGIQUE H2. ---
const h2ChartData = computed<ChartData<'bar'>>(() => {
  const s = stats.value?.h2_equivalence;
  if (!s) return { labels: [], datasets: [] };

  const labelsWithN = s.labels.map((label, i) => `${label} (${s.effectif[i]})`);

  return {
    labels: labelsWithN,
    datasets: [
      { label: 'Voltaire Final (%)', data: s.g2_final, backgroundColor: '#3498db', borderRadius: 4 },
      { label: 'Voltaire Progrès (%)', data: s.g2_progress, backgroundColor: '#85c1e9', borderRadius: 4 },
      { label: 'Ecri+ Final (%)', data: s.g5_final, backgroundColor: '#9b59b6', borderRadius: 4 },
      { label: 'Ecri+ Progrès (%)', data: s.g5_progress, backgroundColor: '#c39bd3', borderRadius: 4 },
    ]
  };
});

const barOptions = computed(() => getOptionsWithEffectif('Précision / Score (%)', 'h2_equivalence'));

const h2BoxplotChartData = computed<ChartData<'boxplot'>>(() => {
  const boxData = stats.value?.h2_boxplots;
  if (!boxData) return { labels: [], datasets: [] };

  const entries = Object.entries(boxData).sort((a, b) => a[0].localeCompare(b[0]));

  const groups = entries.map(e => e[0]);

  return {
    labels: groups,
    datasets: [
      {
        label: 'Score Initial',
        backgroundColor: 'rgba(231, 76, 60, 0.5)',
        borderColor: '#c0392b',
        borderWidth: 1,
        outlierBackgroundColor: '#c0392b',
        data: entries.map(e => e[1].initial)
      },
      {
        label: 'Score Final',
        backgroundColor: 'rgba(52, 152, 219, 0.5)',
        borderColor: '#2980b9',
        borderWidth: 1,
        outlierBackgroundColor: '#2980b9',
        data: entries.map(e => e[1].final)
      },
      {
        label: 'Progression (Delta)',
        backgroundColor: 'rgba(46, 204, 113, 0.5)',
        borderColor: '#27ae60',
        borderWidth: 1,
        outlierBackgroundColor: '#27ae60',
        data: entries.map(e => e[1].delta)
      }
    ]
  };
});

const boxplotOptions = computed<ChartOptions<'boxplot'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' },
    tooltip: {
    }
  },
  scales: {
    y: {
      title: { display: true, text: 'Précision (%) / Delta' }
    }
  }
}));

// --- LOGIQUE H3. ---
const h3Data = computed<ChartData<'bar'>>(() => {
  const teacherStats = stats.value?.h3_teacher || {};

  const labelsWithN = Object.entries(teacherStats).map(([key, val]) => `${key} (${val.effectif})`);
  const dataScores = Object.values(teacherStats).map(t => t.score);

  return {
    labels: labelsWithN,
    datasets: [{
      label: 'Score Final (%)',
      data: dataScores,
      backgroundColor: ['#f39c12', '#e67e22'],
      borderRadius: 6, barPercentage: 0.4, categoryPercentage: 0.6
    }]
  };
});

const h3Options = computed<ChartOptions<'bar'>>(() => ({
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        afterLabel: function (context) {
          const key = context.label;
          const effectif = stats.value?.h3_teacher?.[key]?.effectif || 0;
          return `Effectif : ${effectif} étudiants`;
        }
      }
    }
  },
  scales: { y: { beginAtZero: true, title: { display: true, text: 'Précision (%)' } } }
}));

// --- LOGIQUE H4. ---
const getH4Data = (fam: string): ChartData<'bar'> => {
  if (!stats.value?.h4_sociocultural) return { labels: [], datasets: [] };

  const familyData = stats.value.h4_sociocultural[fam];
  const currentSubCategory = selectedH4[fam];

  if (!familyData || !currentSubCategory || !familyData[currentSubCategory]) {
    return { labels: [], datasets: [] };
  }

  const items = Object.entries(familyData[currentSubCategory])
    .map(([label, val]) => ({ label, ...val }))
    .sort((a, b) => {
      const valA = a[h4SortBy.value] ?? 0;
      const valB = b[h4SortBy.value] ?? 0;
      return valB - valA;
    });

  const maxN = Math.max(...items.map(i => i.Effectif), 1);

  const datasets: (ChartDataset<'bar'> & CustomDataset)[] = [];

  if (h4Metrics.value.includes('Initial')) {
    datasets.push({
      label: 'Initial (%)',
      data: items.map(i => i.Initial),
      backgroundColor: '#34495e',
      borderRadius: 4,
      categoryPercentage: 0.8,
      barPercentage: 0.9,
      effectifData: items.map(i => i.Effectif),
      maxEffectif: maxN,
      useScaling: useThicknessScaling.value,
    });
  }

  if (h4Metrics.value.includes('Progress')) {
    datasets.push({
      label: 'Progression (%)',
      data: items.map(i => i.Progress),
      backgroundColor: '#1abc9c',
      borderRadius: 4,
      categoryPercentage: 0.8,
      barPercentage: 0.9,
      effectifData: items.map(i => i.Effectif),
      maxEffectif: maxN,
      useScaling: useThicknessScaling.value,
    });
  }

  return {
    labels: items.map(i => `${i.label} (${i.Effectif})`),
    datasets
  };
};

const horizontalOptions: ChartOptions<'bar'> = {
  indexAxis: 'y' as const,
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' },
    tooltip: {
      callbacks: {
        label: (context: TooltipItem<'bar'>) => `${context.dataset.label}: ${context.raw}%`
      }
    }
  },
  scales: {
    x: { beginAtZero: true, max: 100 },
    y: {
      grid: { display: false },
      ticks: { font: { size: 11 }, autoSkip: false }
    }
  }
};
</script>

<style scoped>
/* ==========================================================================
     STYLE GRAPHIQUES..
     ========================================================================== */
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

.chart-desc {
  font-size: 0.9rem;
  color: #95a5a6;
  margin-bottom: 10px;
}

/* ==========================================================================
     STYLE H4.
     ========================================================================== */
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

.h4-advanced-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-with-select {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.sort-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* ==========================================================================
     BOUTONS.
     ========================================================================== */
.btn-toggle-group {
  display: flex;
  background: #e2e8f0;
  padding: 3px;
  border-radius: 8px;
}

.btn-toggle-group button {
  border: none;
  background: transparent;
  padding: 6px 14px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #4a5568;
  cursor: pointer;
  border-radius: 6px;
  transition: 0.2s;
}

.btn-toggle-group button.active {
  background: white;
  color: #2d3748;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.toggle-thickness {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #4a5568;
  cursor: pointer;
  font-weight: 500;
}
</style>