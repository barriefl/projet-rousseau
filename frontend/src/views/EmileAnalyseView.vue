<template>
  <div class="analyse-view">
    <div class="page-header">
      <button class="btn btn-outline" @click="router.push('/gestion')">← Retour</button>
      <h1>Analyse des travaux</h1>
    </div>

    <AppLoading v-if="isLoading" message="Chargement des étudiants et de leur progrès..." />

    <div v-else>
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-title">Étudiants évalués</div>
          <div class="kpi-value">{{ totalStudents }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-title">Moyenne Initiale (Malus)</div>
          <div class="kpi-value text-primary">{{ avgInitial }} pts</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-title">Moyenne Finale (Malus)</div>
          <div class="kpi-value text-primary">{{ avgFinal }} pts</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-title">Progression Moyenne</div>
          <div class="kpi-value" :class="avgProgress < 0 ? 'text-success' : 'text-danger'">
            {{ avgProgress > 0 ? '+' : '' }}{{ avgProgress }} pts
          </div>
        </div>
      </div>

      <div class="table-container">
        <div class="table-header">
          <h3>Détail par étudiant</h3>
          <div class="search-box">
            <input type="text" v-model="searchQuery" placeholder="Rechercher un étudiant ou un groupe...">
          </div>
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th>Étudiant</th>
              <th>Groupe</th>
              <th>Dictée Initiale</th>
              <th>Dictée Finale</th>
              <th>Évolution</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="student in filteredStudents" :key="student.id">
              <td><strong>{{ student.last_name }} {{ student.first_name }}</strong></td>
              <td><span class="badge-group">{{ student.group_display || '-' }}</span></td>

              <td>
                <span v-if="student.score_initial !== null">{{ student.score_initial }} pts</span>
                <span v-else class="text-muted">Non passée</span>
              </td>

              <td>
                <span v-if="student.score_final !== null">{{ student.score_final }} pts</span>
                <span v-else class="text-muted">Non passée</span>
              </td>

              <td>
                <span v-if="typeof student.progress === 'number'" class="badge-progress"
                  :class="student.progress < 0 ? 'bg-success' : (student.progress > 0 ? 'bg-danger' : 'bg-neutral')">
                  {{ student.progress > 0 ? '+' : '' }}{{ student.progress }}
                </span>
                <span v-else class="text-muted">-</span>
              </td>
            </tr>
            <tr>
              <td colspan="5" v-if="filteredStudents.length === 0">
                <AppEmptyState title="Aucun étudiant" message="Essayez de modifier vos filtres de recherche." />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';

import type { StudentProgression } from '@/types';

import AppLoading from '@/components/common/AppLoading.vue';
import AppEmptyState from '@/components/common/AppEmptyState.vue';

const router = useRouter();

// --- ÉTATS. ---
const isLoading = ref(true);
const studentsStats = ref<StudentProgression[]>([]);
const searchQuery = ref('');

// --- CHARGEMENT. ---
onMounted(async () => {
  try {
    const res = await api.getStudentProgression();
    studentsStats.value = res.sort((a: StudentProgression, b: StudentProgression) =>
      a.last_name.localeCompare(b.last_name, 'fr')
    );
  } catch (error) {
    console.error("Erreur de chargement des statistiques :", error);
  } finally {
    isLoading.value = false;
  }
});

// --- RECHERCHE. ---
const filteredStudents = computed(() => {
  if (!searchQuery.value) return studentsStats.value;
  const q = searchQuery.value.toLowerCase();
  return studentsStats.value.filter(s =>
    s.last_name.toLowerCase().includes(q) ||
    s.first_name.toLowerCase().includes(q) ||
    (s.group_name && s.group_name.toLowerCase().includes(q))
  );
});

// --- CALCUL DES KPIs. ---
const totalStudents = computed(() => studentsStats.value.length);

const avgInitial = computed(() => {
  const withInitial = studentsStats.value.filter(s => s.score_initial !== null);
  if (withInitial.length === 0) return 0;
  const sum = withInitial.reduce((acc, s) => acc + (s.score_initial || 0), 0);
  return Number((sum / withInitial.length).toFixed(1));
});

const avgFinal = computed(() => {
  const withFinal = studentsStats.value.filter(s => s.score_final !== null);
  if (withFinal.length === 0) return 0;
  const sum = withFinal.reduce((acc, s) => acc + (s.score_final || 0), 0);
  return Number((sum / withFinal.length).toFixed(1));
});

const avgProgress = computed(() => {
  const withProgress = studentsStats.value.filter(s => s.progress !== null);
  if (withProgress.length === 0) return 0;
  const sum = withProgress.reduce((acc, s) => acc + (s.progress || 0), 0);
  return Number((sum / withProgress.length).toFixed(1));
});
</script>

<style scoped>
/* ==========================================================================
     KPIs.
     ========================================================================== */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.kpi-card {
  background: white;
  padding: 25px;
  border-radius: 8px;
  border: 1px solid #e1e8ed;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

.kpi-title {
  color: #7f8c8d;
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 10px;
}

.kpi-value {
  font-size: 2rem;
  font-weight: bold;
  color: var(--text);
}

.text-success {
  color: var(--success);
}

.text-warning {
  color: var(--warning);
}

.text-danger {
  color: var(--danger);
}

.text-muted {
  color: #bdc3c7;
  font-style: italic;
}

/* ==========================================================================
     TABLE.
     ========================================================================== */

.table-header {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e1e8ed;
  background: #fafafa;
}

.table-header h3 {
  margin: 0;
}

/* ==========================================================================
     RECHERCHE.
     ========================================================================== */

.search-box input {
  padding: 8px 15px;
  border: 1px solid #ccc;
  border-radius: 20px;
  outline: none;
  width: 300px;
}

.search-box input:focus {
  border-color: var(--accent);
}

/* ==========================================================================
     BADGES.
     ========================================================================== */
.badge-group {
  background: #ecf0f1;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.85rem;
  color: #2c3e50;
  font-weight: bold;
}

.badge-progress {
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 0.9rem;
  color: white;
  display: inline-block;
  min-width: 50px;
  text-align: center;
}

.bg-success {
  background-color: var(--success);
}

.bg-danger {
  background-color: var(--danger);
}

.bg-neutral {
  background-color: var(--neutral);
}
</style>