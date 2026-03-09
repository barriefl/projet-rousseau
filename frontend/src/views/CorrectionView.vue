<template>
  <div class="emile-workspace">
    <div class="page-header">
      <button class="btn btn-outline" style="margin-right: 15px;" @click="router.push('/gestion')">← Retour</button>
      <h1 style="display: inline-block;">É.M.I.L.E.</h1>
    </div>

    <div class="search-container">
      <input type="text" class="search-input" v-model="searchQuery" placeholder="Rechercher un étudiant par nom...">
    </div>

    <AppLoading v-if="isLoadingStudents" message="Chargement des étudiants..." />

    <AppEmptyState v-else-if="students.length === 0" title="Aucun étudiant"
      message="Impossible de charger les étudiants." :showRetry="true" :loading="isLoadingStudents"
      @retry="fetchStudentsWithScores" />

    <div class="student-scroll-list" v-else>
      <div v-for="student in filteredStudents" :key="student.id" class="student-card"
        :class="{ 'selected': selectedStudent?.id === student.id }" @click="selectStudent(student)">
        <div class="student-info">
          <h4 style="color: var(--primary); margin: 0 0 5px 0;">{{ student.last_name }} {{ student.first_name }}</h4>
          <p style="margin: 0 0 10px 0; color: #555; font-size: 0.9rem;">
            ({{ student.promotion_name || 'Sans promo' }}) ({{ student.group_name || 'Sans groupe' }})
          </p>
        </div>

        <div class="student-scores">
          <span class="score-badge" :class="getScoreColorClass(student.initial_score, 'initial')">
            I : {{ formatScore(student.initial_score) }}
          </span>
          <span class="score-badge" :class="getScoreColorClass(student.final_score, 'final')">
            F : {{ formatScore(student.final_score) }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="selectedStudent" class="dictation-selector">
      <h4 style="margin-bottom: 15px; color: var(--primary);">Dictées de {{ selectedStudent.last_name }} {{
        selectedStudent.first_name }} :</h4>

      <div v-if="isLoadingSubmissions" style="color: #7f8c8d; font-size: 0.9rem;">Recherche des dictées en cours...
      </div>

      <div v-else-if="studentSubmissions.length > 0">
        <button v-for="sub in studentSubmissions" :key="sub.id" class="btn dictation-btn"
          :class="{ 'active': selectedSubmission?.id === sub.id }" @click="loadSubmissionDetails(sub)">
          Dictée {{ sub.assessment_type === 'Initiale' ? 'Initiale' : 'Finale' }} ({{ new
            Date(sub.created_at).toLocaleDateString('fr-FR', { year: 'numeric' }) }})
        </button>
      </div>

      <div v-else
        style="color: var(--danger); font-size: 0.9rem; padding: 10px; background: #fff5f5; border-radius: 5px;">
        Aucune dictée trouvée pour cet étudiant.
      </div>
    </div>

    <AppLoading v-if="isLoadingDetails" message="Analyse du texte et génération de la correction..."
      style="text-align: center; padding: 40px; color: #7f8c8d;" />

    <div v-else-if="submissionDetails" class="atelier-container">

      <div class="text-editor" @mouseover="handleMouseOver" @mouseout="handleMouseOut">
        <h3
          style="margin-top: 0; color: #7f8c8d; font-size: 1rem; border-bottom: 1px solid #eee; padding-bottom: 10px;">
          Texte analysé
        </h3>

        <div class="content-html" v-html="submissionDetails.html_text"></div>

        <div v-show="tooltip.visible" class="reverso-tooltip"
          :style="{ top: tooltip.y + 'px', left: tooltip.x + 'px' }">
          <h5>Type '{{ tooltip.type }}' <span style="color:#e74c3c">+{{ tooltip.malus }} pt</span></h5>
          <div v-if="tooltip.ruleId"
            style="font-size: 0.75rem; color: #95a5a6; margin-bottom: 4px; font-family: monospace;">
            Règle : {{ tooltip.ruleId }}
          </div>
          <div class="correction">{{ tooltip.corr || 'Aucune suggestion' }}</div>
          <div class="desc">{{ tooltip.desc }}</div>
        </div>
      </div>

      <div class="panel">
        <div class="score-display">
          <small style="color: #333; font-size: 0.85rem;">Total des pénalités</small>
          <span>{{ submissionDetails.final_score }} pts</span>
          <small style="color: #7f8c8d; font-size: 0.75rem;">(0 = Parfait)</small>
        </div>

        <h3 style="font-size: 1rem; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;">
          Bilan des fautes ({{ submissionDetails.mistakes?.length || 0 }})
        </h3>

        <div v-if="submissionDetails.scores && Object.keys(submissionDetails.scores).length > 0"
          style="margin-bottom: 15px; font-size: 0.85rem;">
          <div v-for="(val, cat) in submissionDetails.scores" :key="cat"
            style="display: flex; justify-content: space-between; margin-bottom: 3px;">
            <span style="color: #555;">{{ cat }}</span>
            <strong style="color: var(--danger);">+{{ val }}</strong>
          </div>
        </div>

        <div class="error-list">
          <div v-for="(mistake, index) in sortedMistakes" :key="index" class="error-item"
            :data-type="mistake.type_rousseau">

            <strong>{{ mistake.student_word || '[Oubli]' }}</strong><br>
            <div style="font-size: 0.75rem; color: #95a5a6; font-family: monospace; margin: 2px 0;">
              Règle : {{ mistake.rule_id_lt || 'Non spécifiée' }}
            </div>
            <span style="color: #555;">Correction : {{ mistake.correct_word || '-' }} (+{{ mistake.malus_applied
            }})</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';

import type { Student, StudentSubmission, StudentWithScores, SubmissionDetails } from '@/types';

import AppLoading from '@/components/common/AppLoading.vue';
import AppEmptyState from '@/components/common/AppEmptyState.vue';

import { useUiStore } from '@/stores/ui';

const ui = useUiStore();

const router = useRouter();

// --- ÉTATS. ---
const students = ref<StudentWithScores[]>([]);
const searchQuery = ref('');
const isLoadingStudents = ref(true);
const isLoadingSubmissions = ref(false);
const isLoadingDetails = ref(false);

const selectedStudent = ref<StudentWithScores | null>(null);
const studentSubmissions = ref<StudentSubmission[]>([]);
const selectedSubmission = ref<StudentSubmission | null>(null);
const submissionDetails = ref<SubmissionDetails | null>(null);

const tooltip = ref({ visible: false, x: 0, y: 0, type: '', malus: '', corr: '', desc: '', ruleId: '' });

// --- CHARGEMENT INITIAL. ---
const fetchStudentsWithScores = async () => {
  isLoadingStudents.value = true;
  try {
    const data = await api.getStudentsWithScores();
    students.value = data.sort((a: Student, b: Student) => a.last_name.localeCompare(b.last_name, 'fr'));
  } catch (error) {
    console.error("Erreur chargement étudiants :", error);
    ui.notify("Erreur lors de la récupération des étudiants et des scores.", "error");
  } finally {
    isLoadingStudents.value = false;
  }
};

onMounted(() => {
  fetchStudentsWithScores();
})

// --- COMPUTED (Recherche). ---
const filteredStudents = computed(() => {
  return students.value.filter(s =>
    s.last_name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    s.first_name.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

const sortedMistakes = computed(() => {
  if (!submissionDetails.value?.mistakes) return [];
  return [...submissionDetails.value.mistakes].sort((a, b) => a.position_index - b.position_index);
});

// --- LOGIQUE DES BADGES DE SCORE. ---
const formatScore = (score: number | null) => {
  return score !== null ? `${score}` : '-';
};

// --- CALCUL DYNAMIQUE DES QUARTILES. ---
const scoreThresholds = computed(() => {
  const getQuartiles = (type: 'initial_score' | 'final_score') => {
    const scores = students.value
      .map(s => s[type])
      .filter((score): score is number => score !== null && score !== undefined);

    if (scores.length === 0) return { q1: 5, q3: 15 };
    if (scores.length === 1) return { q1: scores[0], q3: scores[0] };

    scores.sort((a, b) => a - b);

    const q1Index = Math.floor((scores.length - 1) * 0.25);
    const q3Index = Math.floor((scores.length - 1) * 0.75);

    return {
      q1: scores[q1Index],
      q3: scores[q3Index]
    };
  };

  return {
    initial: getQuartiles('initial_score'),
    final: getQuartiles('final_score')
  };
});

const getScoreColorClass = (score: number | null | undefined, type: 'initial' | 'final') => {
  if (score === null || score === undefined) return 'badge-empty';

  const thresholds = scoreThresholds.value[type];

  if (!thresholds || thresholds.q1 === undefined || thresholds.q3 === undefined) {
    if (score <= 5) return 'badge-good';
    if (score <= 15) return 'badge-medium';
    return 'badge-bad';
  }

  if (score <= thresholds.q1) return 'badge-good';
  if (score <= thresholds.q3) return 'badge-medium';

  return 'badge-bad';
};

// --- ACTIONS. ---
const selectStudent = async (student: StudentWithScores) => {
  selectedStudent.value = student;
  selectedSubmission.value = null;
  submissionDetails.value = null;
  studentSubmissions.value = [];
  isLoadingSubmissions.value = true;

  try {
    const res = await api.getStudentSubmissions(student.id);

    studentSubmissions.value = res.sort((a, b) => {
      const typeA = a.assessment_type?.toUpperCase() || '';
      const typeB = b.assessment_type?.toUpperCase() || '';

      if (typeA.includes('INITIAL')) return -1;
      if (typeB.includes('INITIAL')) return 1;
      return 0;
    });
  } catch (error) {
    console.error("Erreur dictées :", error);
    ui.notify("Impossible de récupérer les dictées de l'étudiant.", "error");
  } finally {
    isLoadingSubmissions.value = false;
  }
};

const loadSubmissionDetails = async (sub: StudentSubmission) => {
  selectedSubmission.value = sub;
  submissionDetails.value = null;
  isLoadingDetails.value = true;

  try {
    const res = await api.getSubmissionDetails(sub.id);
    submissionDetails.value = res;
  } catch (error) {
    console.error("Erreur détails :", error);
    ui.notify("Impossible de charger le contenu détaillé de la dictée.", "error");
  } finally {
    isLoadingDetails.value = false;
  }
};

// --- GESTION DE L'INFOBULLE. ---
const handleMouseOver = (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  if (target.classList.contains('faute')) {
    tooltip.value = {
      visible: true,
      x: target.offsetLeft,
      y: target.offsetTop + 25,
      type: target.getAttribute('data-type') || 'Inconnu',
      malus: target.getAttribute('data-malus') || '0',
      corr: target.getAttribute('data-corr') || '',
      desc: target.getAttribute('data-desc') || '',
      ruleId: target.getAttribute('data-rule-id') || ''
    };
  }
};

const handleMouseOut = (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  if (target.classList.contains('faute')) {
    tooltip.value.visible = false;
  }
};
</script>

<style scoped>
/* ==========================================================================
     BARRE DE RECHERCHE.
     ========================================================================== */
.search-container {
  margin-bottom: 15px;
}

.search-input {
  width: 100%;
  max-width: 400px;
  padding: 10px 15px;
  border-radius: 8px;
  border: 1px solid #ccc;
  font-size: 1rem;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent);
}

/* ==========================================================================
     LISTE DES ÉTUDIANTS.
     ========================================================================== */
.student-scroll-list {
  display: flex;
  gap: 15px;
  overflow-x: auto;
  padding-bottom: 15px;
  margin-bottom: 20px;
}

.student-scroll-list::-webkit-scrollbar {
  height: 8px;
}

.student-scroll-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.student-scroll-list::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 4px;
}

.student-scroll-list::-webkit-scrollbar-thumb:hover {
  background: #bbb;
}

.student-card {
  min-width: 200px;
  background: white;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #e1e8ed;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.student-scores {
  display: flex;
  gap: 8px;
  margin-top: auto;
}

.score-badge {
  font-size: 0.75rem;
  padding: 4px 8px;
  border-radius: 12px;
  font-weight: 700;
  display: inline-block;
  min-width: 45px;
  text-align: center;
}

.student-card:hover {
  transform: translateY(-2px);
  border-color: var(--accent);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.student-card.selected {
  border: 2px solid var(--accent);
  background-color: #f0f8ff;
}

/* ==========================================================================
     DICTÉES.
     ========================================================================== */
.dictation-selector {
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e1e8ed;
}

.dictation-btn {
  padding: 10px 15px;
  background: var(--light);
  border: 1px solid #ccc;
  border-radius: 6px;
  cursor: pointer;
  margin-right: 10px;
  font-size: 0.95rem;
  font-weight: 500;
  transition: 0.2s;
}

.dictation-btn:hover {
  background: #e2e6ea;
}

.dictation-btn.active {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

/* ==========================================================================
     ZONE DU TEXTE.
     ========================================================================== */
.atelier-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  align-items: start;
}

.text-editor {
  background: white;
  padding: 30px;
  border-radius: 8px;
  border: 1px solid #e1e8ed;
  font-size: 1.15rem;
  min-height: 400px;
  position: relative;
  line-height: 2;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

.content-html {
  white-space: pre-wrap;
}

:deep(.faute) {
  cursor: pointer;
  border-bottom: 2px dashed;
  padding-bottom: 1px;
  font-weight: 600;
  transition: 0.2s;
  background-color: rgba(255, 200, 200, 0.1);
}

:deep(.faute:hover) {
  background-color: rgba(0, 0, 0, 0.08);
}

:deep(.faute[data-type="Dessin"]) {
  border-color: #e67e22;
  color: #e67e22;
}

:deep(.faute[data-type="Règle"]) {
  border-color: #e74c3c;
  color: #e74c3c;
}

:deep(.faute[data-type="Sens"]) {
  border-color: #3498db;
  color: #3498db;
}

:deep(.faute[data-type="Autre"]) {
  border-color: #9b59b6;
  color: #9b59b6;
}

/* ==========================================================================
     INFOBULLE.
     ========================================================================== */
.reverso-tooltip {
  position: absolute;
  background: white;
  border: 1px solid #ccc;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  padding: 15px;
  width: 280px;
  z-index: 100;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  pointer-events: none;
}

.reverso-tooltip h5 {
  font-size: 0.95rem;
  margin: 0 0 8px 0;
  color: var(--primary);
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
}

.reverso-tooltip .correction {
  font-size: 1.1rem;
  font-weight: bold;
  color: var(--accent);
  margin-bottom: 5px;
}

.reverso-tooltip .desc {
  font-size: 0.85rem;
  color: #555;
  line-height: 1.4;
  font-style: italic;
}

/* ==========================================================================
     LISTE DES ERREURS & PANEL.
     ========================================================================== */
.panel {
  background: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e1e8ed;
  display: flex;
  flex-direction: column;
  max-height: 600px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

.score-display {
  text-align: center;
  margin-bottom: 15px;
  padding: 15px;
  background: #fff5f5;
  border-radius: 8px;
  border: 1px solid #fadbd8;
}

.score-display span {
  font-size: 2.2rem;
  font-weight: bold;
  color: var(--danger);
  display: block;
  margin: 5px 0;
}

.error-list {
  overflow-y: auto;
  flex: 1;
  padding-right: 5px;
  margin-top: 10px;
}

.error-list::-webkit-scrollbar {
  width: 6px;
}

.error-list::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.error-item {
  padding: 10px;
  border-left: 4px solid #ccc;
  background: #fdfdfd;
  margin-bottom: 8px;
  font-size: 0.85rem;
  border-radius: 4px;
  border: 1px solid #eee;
}

.error-item[data-type="Dessin"] {
  border-left-color: #e67e22;
}

.error-item[data-type="Règle"] {
  border-left-color: #e74c3c;
}

.error-item[data-type="Sens"] {
  border-left-color: #3498db;
}

.error-item[data-type="Autre"] {
  border-left-color: #9b59b6;
}
</style>