<template>
  <div class="dashboard">
    <h1>Tableau de Bord Rousseau</h1>
    
    <div v-if="loading">Chargement des données...</div>
    
    <div v-else-if="stats" class="stats-grid">
      <div class="card">
        <h3>Total Étudiants</h3>
        <p class="big-number">{{ stats.total_students }}</p>
      </div>

      <div class="card">
        <h3>Dictées (Progression)</h3>
        <p>Moyenne Initiale : {{ stats.submissions.avg_init }}</p>
        <p>Moyenne Finale : {{ stats.submissions.avg_final }}</p>
        <p :class="getClass(stats.submissions.progression)">
            {{ stats.submissions.progression > 0 ? '+' : ''}}{{ stats.submissions.progression }}
        </p>
      </div>
      
      <div class="card">
        <h3>Comparatif Outils</h3>
        <p>Voltaire Progression: {{ stats.voltaire.progression }}</p>
        <p>Ecri+ Progression: {{ stats.ecriplus.progression }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import api from '@/services/api';
import type { GlobalStats } from '@/types';

const stats = ref<GlobalStats | null>(null);
const loading = ref(true);

const getClass = (val: number) => (val >= 0 ? 'positive' : 'negative');

onMounted(async () => {
  try {
    const response = await api.getGlobalStats();
    stats.value = response.data;
  } catch (error) {
    console.error("Erreur API", error);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.card { border: 1px solid #ddd; padding: 20px; border-radius: 8px; }
.positive { color: green; font-weight: bold; }
.negative { color: red; font-weight: bold; }
.big-number { font-size: 2em; font-weight: bold; color: #2c3e50; }
</style>