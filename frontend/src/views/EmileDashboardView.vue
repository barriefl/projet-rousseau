<template>
  <div class="emile-dashboard">
    <div class="header">
      <h1>📊 Tableau de Bord É.M.I.L.E.</h1>
    </div>
    
    <div v-if="isLoading" class="loading">
      ⏳ Récupération des statistiques analytiques...
    </div>

    <div v-else-if="stats">
      <div class="grid-3">
        <div class="card">
          <h3>Total Étudiants Inscrits</h3>
          <div class="stat-val">{{ stats.total_students }}</div>
          <div class="stat-desc">Ayant passé au moins une dictée</div>
        </div>
        
        <div class="card">
          <h3>Dictées Traitées</h3>
          <div class="stat-val">{{ stats.total_submissions }}</div>
          <div class="stat-desc">Analysées par l'outil</div>
        </div>
        
        <div class="card">
          <h3>Moyenne Globale (Malus)</h3>
          <div class="stat-val danger">{{ stats.global_average }} pts</div>
          <div class="stat-desc">Moyenne de toutes les copies finales</div>
        </div>
      </div>
      
      <h2 class="section-title">Analyse par Groupe</h2>
      <div class="grid-2">
        <div class="card chart-container">
          <h3>Répartition des étudiants</h3>
          <div class="chart-wrapper">
            <Pie :data="distributionChartData" :options="pieOptions" />
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
          <h3>Impact de la méthode de travail</h3>
          <div class="chart-wrapper">
            <Bar :data="motivationChartData" :options="barOptions" />
          </div>
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

// --- IMPORT CHART.JS. ---
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement } from 'chart.js';
import { Bar, Pie } from 'vue-chartjs';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement);

// --- ÉTATS. ---
const isLoading = ref(true);
const stats = ref<any>(null);

// --- CHARGEMENT. ---
onMounted(async () => {
  try {
    const res = await api.getEmileDashboardStats();
    stats.value = res.data;
  } catch (error) {
    console.error("Erreur lors du chargement du tableau de bord :", error);
  } finally {
    isLoading.value = false;
  }
});

// --- DATA POUR LES GRAPHIQUES. ---

// 1. Répartition par groupe (Camembert).
const distributionChartData = computed(() => {
  if (!stats.value?.group_distribution) return { labels: [], datasets: [] };
  return {
    labels: Object.keys(stats.value.group_distribution),
    datasets: [{
      label: 'Étudiants',
      data: Object.values(stats.value.group_distribution) as number[],
      backgroundColor: ['#3498db', '#e74c3c', '#f1c40f', '#2ecc71', '#9b59b6', '#e67e22', '#1abc9c'],
      borderWidth: 1
    }]
  };
});

// 2. Moyennes par groupe.
const averagesChartData = computed(() => {
  if (!stats.value?.group_averages) return { labels: [], datasets: [] };
  return {
    labels: Object.keys(stats.value.group_averages),
    datasets: [{
      label: 'Malus moyen',
      data: Object.values(stats.value.group_averages) as number[],
      backgroundColor: '#3498db',
      borderRadius: 4
    }]
  };
});

// 3. Moyennes par Promo.
const promoChartData = computed(() => {
  if (!stats.value?.promo_averages) return { labels: [], datasets: [] };
  return {
    labels: Object.keys(stats.value.promo_averages),
    datasets: [{
      label: 'Malus moyen',
      data: Object.values(stats.value.promo_averages) as number[],
      backgroundColor: ['#9b59b6', '#8e44ad'],
      borderRadius: 4
    }]
  };
});

// 4. Motivation (Autonomie vs Jalons).
const motivationChartData = computed(() => {
  if (!stats.value?.comparison_motivation) return { labels: [], datasets: [] };
  return {
    labels: Object.keys(stats.value.comparison_motivation),
    datasets: [{
      label: 'Malus moyen',
      data: Object.values(stats.value.comparison_motivation) as number[],
      backgroundColor: ['#e67e22', '#d35400', '#f39c12'],
      borderRadius: 4
    }]
  };
});

// 5. Outils (Voltaire vs Écri+).
const toolChartData = computed(() => {
  if (!stats.value?.comparison_tool) return { labels: [], datasets: [] };
  return {
    labels: Object.keys(stats.value.comparison_tool),
    datasets: [{
      label: 'Malus moyen',
      data: Object.values(stats.value.comparison_tool) as number[],
      backgroundColor: ['#2ecc71', '#27ae60'],
      borderRadius: 4
    }]
  };
});

// 6. Humain vs Robot.
const humanRobotChartData = computed(() => {
  if (!stats.value?.comparison_human_robot) return { labels: [], datasets: [] };
  return {
    labels: Object.keys(stats.value.comparison_human_robot),
    datasets: [{
      label: 'Malus moyen',
      data: Object.values(stats.value.comparison_human_robot) as number[],
      backgroundColor: ['#34495e', '#2c3e50'],
      borderRadius: 4
    }]
  };
});

// --- OPTIONS DES GRAPHIQUES. ---
const pieOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { 
    legend: { 
      position: 'bottom' as const 
    } 
  }
};

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { 
    legend: { 
      display: false 
    } 
  },
  scales: { 
    y: { 
      beginAtZero: true, 
      title: { 
        display: true, 
        text: 'Points de Malus' 
      } 
    } 
  }
};

// Options pour graphiques en barres horizontales.
const horizontalBarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y' as const, 
  plugins: { 
    legend: { 
      display: false 
    } 
  },
  scales: { 
    x: { 
      beginAtZero: true, 
      title: { 
        display: true, 
        text: 'Points de Malus' 
      } 
    } 
  }
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

.section-title { 
  font-size: 1.2rem; 
  color: #7f8c8d; 
  border-bottom: 2px solid #eee; 
  padding-bottom: 5px; 
  margin-top: 30px; 
  margin-bottom: 15px; 
}

/* Grilles. */
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

/* Cartes. */
.card { 
  background: white; 
  padding: 25px; 
  border-radius: 8px; 
  box-shadow: 0 2px 5px rgba(0,0,0,0.02); 
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

/* KPIs. */
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

/* Chart.js. */
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
  height: 160px; 
}
</style>