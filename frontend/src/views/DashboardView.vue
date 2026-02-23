<template>
  <div class="dashboard-etude">
    <div class="header">
      <h1>📈 Étude Rousseau : Analyses et Conclusions</h1>
    </div>

    <div v-if="isLoading" class="loading">
      ⏳ Chargement des conclusions de l'étude...
    </div>

    <div v-else-if="stats" class="grid-2">
      <div class="card chart-container">
        <h3>Outils (Var. Secondaire) vs Dictée (Var. Principale)</h3>
        <p class="chart-desc">Comparaison des scores initiaux et finaux</p>
        <div class="chart-wrapper">
          <Bar :data="toolsChartData" :options="groupedBarOptions" />
        </div>
      </div>

      <div class="card chart-container">
        <h3>Performance Comparée : Projet Voltaire vs Ecri+</h3>
        <p class="chart-desc">Vérification de la non-infériorité de l'outil gratuit (Malus final)</p>
        <div class="chart-wrapper">
          <Bar :data="equivalenceChartData" :options="barOptions" />
        </div>
      </div>

      <div class="card chart-container">
        <h3>Impact de l'Accompagnement Enseignant</h3>
        <p class="chart-desc">Malus final selon l'encadrement (G4) vs Autonomie (G2, G3, G5)</p>
        <div class="chart-wrapper">
          <Bar :data="teacherFactorChartData" :options="barOptions" />
        </div>
      </div>

      <div class="card chart-container">
        <div class="header-with-select">
          <h3>Poids des Variables Socioculturelles</h3>
          <select v-model="selectedSocioCategory" class="socio-select">
            <option v-for="cat in socioCategories" :key="cat" :value="cat">
              {{ cat }}
            </option>
          </select>
        </div>
        <p class="chart-desc">Progression moyenne (valeur négative = baisse du malus = amélioration)</p>
        <div class="chart-wrapper">
          <Bar :data="socioculturalChartData" :options="horizontalBarOptions" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import api from '@/services/api';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';
import { Bar } from 'vue-chartjs';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

// --- ÉTATS. ---
const isLoading = ref(true);
const stats = ref<any>(null);
const selectedSocioCategory = ref<string>('');

// --- CHARGEMENT. ---
onMounted(async () => {
  try {
    const res = await api.getRousseauStats();
    stats.value = res.data;
    if (stats.value?.sociocultural_impact) {
      selectedSocioCategory.value = Object.keys(stats.value.sociocultural_impact)[0] || '';
    }
  } catch (error) {
    console.error("Erreur lors du chargement de l'étude Rousseau :", error);
  } finally {
    isLoading.value = false;
  }
});

// --- DATA POUR LES GRAPHIQUES. ---

// 1. Outils vs Dictées (Grouped Bar Chart).
const toolsChartData = computed(() => {
  if (!stats.value?.tools_vs_dictation) return { labels: [], datasets: [] };
  
  const labels = Object.keys(stats.value.tools_vs_dictation);
  const initialData = labels.map(l => stats.value.tools_vs_dictation[l].Initial);
  const finalData = labels.map(l => stats.value.tools_vs_dictation[l].Final);

  return {
    labels: labels,
    datasets: [
      { label: 'Score Initial', data: initialData, backgroundColor: '#e74c3c', borderRadius: 4 },
      { label: 'Score Final', data: finalData, backgroundColor: '#2ecc71', borderRadius: 4 }
    ]
  };
});

// 2. Équivalence G2 vs G5.
const equivalenceChartData = computed(() => {
  if (!stats.value?.equivalence_g2_g5) return { labels: [], datasets: [] };
  return {
    labels: Object.keys(stats.value.equivalence_g2_g5),
    datasets: [{
      label: 'Malus Final',
      data: Object.values(stats.value.equivalence_g2_g5) as number[],
      backgroundColor: ['#3498db', '#9b59b6'],
      borderRadius: 4
    }]
  };
});

// 3. Facteur Enseignant.
const teacherFactorChartData = computed(() => {
  if (!stats.value?.teacher_factor) return { labels: [], datasets: [] };
  return {
    labels: Object.keys(stats.value.teacher_factor),
    datasets: [{
      label: 'Malus Final',
      data: Object.values(stats.value.teacher_factor) as number[],
      backgroundColor: ['#f39c12', '#e67e22'],
      borderRadius: 4
    }]
  };
});

// 4. Variables Socioculturelles (Dynamique).
const socioCategories = computed(() => {
  return stats.value?.sociocultural_impact ? Object.keys(stats.value.sociocultural_impact) : [];
});

const socioculturalChartData = computed(() => {
  if (!stats.value?.sociocultural_impact || !selectedSocioCategory.value) return { labels: [], datasets: [] };
  
  const currentData = stats.value.sociocultural_impact[selectedSocioCategory.value];
  return {
    labels: Object.keys(currentData),
    datasets: [{
      label: 'Évolution du score',
      data: Object.values(currentData) as number[],
      backgroundColor: '#1abc9c',
      borderRadius: 4
    }]
  };
});


// --- OPTIONS DES GRAPHIQUES. ---
const groupedBarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' as const } }
};

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true } }
};

const horizontalBarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y' as const,
  plugins: { legend: { display: false } }
};
</script>

<style scoped>
.header { 
  margin-bottom: 30px; 
}
.header h1 { 
  font-size: 1.6rem; 
  color: var(--primary); 
  margin: 0; 
}
.loading { 
  padding: 40px; 
  text-align: center; 
  color: #7f8c8d; 
  font-size: 1.1rem; 
}

/* Grille principale. */
.grid-2 { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); 
  gap: 20px; 
  margin-bottom: 20px; 
}

/* Cartes et Graphiques. */
.card { 
  background: white; 
  padding: 25px; 
  border-radius: 8px; 
  box-shadow: 0 2px 5px rgba(0,0,0,0.02); 
  border: 1px solid #e1e8ed; 
  display: flex; 
  flex-direction: column; 
}
.card h3 { 
  font-size: 1.1rem; 
  color: var(--primary); 
  margin-top: 0; 
  margin-bottom: 5px; 
}
.chart-desc { 
  font-size: 0.85rem; 
  color: #7f8c8d; 
  margin-bottom: 15px; 
  border-bottom: 2px solid var(--light); 
  padding-bottom: 10px; 
}

.chart-wrapper { 
  position: relative; 
  height: 300px; 
  width: 100%; 
  flex-grow: 1; 
}

/* Sélecteur dynamique (Socioculturel). */
.header-with-select { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  flex-wrap: wrap; 
  gap: 10px; 
  margin-bottom: 5px; 
}
.header-with-select h3 { 
  margin: 0; 
  border: none; 
  padding: 0; 
}
.socio-select { 
  padding: 6px 10px; 
  border-radius: 6px; 
  border: 1px solid #ccc; 
  font-size: 0.9rem; 
  outline: none; 
  background-color: #f8f9fa; 
  cursor: pointer; 
  max-width: 250px; 
}
.socio-select:focus { 
  border-color: var(--accent); 
}
</style>