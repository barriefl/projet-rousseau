<template>
  <div class="import-workspace">
    <div class="header">
      <button class="btn btn-outline" style="margin-right: 15px;" @click="$router.push('/gestion')">← Retour</button>
      <h1 style="display: inline-block;">Importation des Résultats (Voltaire / Ecri+)</h1>
    </div>

    <div class="panel" v-if="!importSuccess">
      <h2 class="step-title">1. Configuration de l'import</h2>

      <div class="form-grid">
        <div class="form-group">
          <label>Promotion cible :</label>
          <select v-model="selectedPromotion" :disabled="isAnalyzing" class="action-select">
            <option value="" disabled>-- Choisir --</option>
            <option v-for="promo in promotions" :key="promo.id" :value="promo.id">
              {{ promo.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Outil / Plateforme :</label>
          <select v-model="selectedPlatform" :disabled="isAnalyzing" class="action-select">
            <option value="" disabled>-- Choisir --</option>
            <option v-for="type in Object.values(Platforms)" :key="type" :value="type">
              {{ type }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Type d'évaluation :</label>
          <select v-model="selectedType" :disabled="isAnalyzing" class="action-select">
            <option value="" disabled>-- Choisir --</option>
            <option v-for="type in Object.values(AssessmentTypes)" :key="type" :value="type">
              {{ type }}
            </option>
          </select>
        </div>
      </div>

      <div class="form-group" style="margin-top: 15px;">
        <label>Fichier CSV :</label>
        <input type="file" accept=".csv" @change="handleFileUpload" :disabled="isAnalyzing" class="file-input" />
      </div>

      <button class="btn btn-primary btn-with-icon" style="margin-top: 20px;"
        :disabled="!selectedPromotion || !selectedPlatform || !selectedType || !selectedFile || isAnalyzing"
        @click="analyzeFile">
        <Loader2 v-if="isAnalyzing" :size="18" class="animate-spin" />
        <Search v-else :size="18" />
        <span>{{ isAnalyzing ? 'Analyse en cours...' : 'Analyser le fichier' }}</span>
      </button>
    </div>

    <div class="panel" v-if="previewData && !importSuccess" style="margin-top: 20px;">
      <h2 class="step-title">2. Rapport d'analyse</h2>
      <p style="color: #7f8c8d; font-size: 0.95rem; margin-bottom: 20px;">
        Vérifiez les liaisons avec les étudiants avant de sauvegarder les scores.
      </p>

      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-number" style="color: #27ae60;">{{ exactMatches.length }}</span>
          <span class="stat-label">Liés automatiquement</span>
        </div>
        <div class="stat-card">
          <span class="stat-number" style="color: #f39c12;">{{ fuzzyMatches.length }}</span>
          <span class="stat-label">Correspondances floues</span>
        </div>
        <div class="stat-card">
          <span class="stat-number" style="color: #e74c3c;">{{ previewData.unmatched_results.length }}</span>
          <span class="stat-label">Introuvables (Ignorés)</span>
        </div>
      </div>

      <div v-if="fuzzyMatches.length > 0" class="fuzzy-section">
        <h3 class="title-with-icon">
          <SearchCheck :size="22" color="var(--primary)" />
          Vérification des fautes de frappe
        </h3>
        <p style="font-size: 0.9rem; margin-top: 0;">Décochez la case si l'étudiant du CSV ne correspond pas à
          l'étudiant trouvé en base.</p>
        <table class="preview-table">
          <thead>
            <tr>
              <th>Lier ?</th>
              <th>Nom CSV</th>
              <th>Étudiant trouvé en Base</th>
              <th>Score extrait</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(match, index) in fuzzyMatches" :key="index">
              <td style="text-align: center;">
                <input type="checkbox" v-model="match.user_validated" style="transform: scale(1.2); cursor: pointer;" />
              </td>
              <td><strong>{{ match.csv_prenom }} {{ match.csv_nom }}</strong></td>
              <td>{{ match.db_first_name }} {{ match.db_last_name }}</td>
              <td><strong>{{ match.score }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="previewData.unmatched_results.length > 0" class="fuzzy-section"
        style="background: #fdf5f5; border-color: #fadbd8;">
        <h3 class="title-with-icon" style="color: #c0392b;">
          <AlertTriangle :size="22" />
          Étudiants introuvables (seront ignorés)
        </h3>
        <p style="font-size: 0.9rem; margin-top: 0;">Ces lignes du CSV ne correspondent à aucun étudiant de la promotion
          sélectionnée.</p>
        <div class="badge-container">
          <span v-for="(match, index) in previewData.unmatched_results" :key="index" class="badge badge-red">
            {{ match.csv_prenom }} {{ match.csv_nom }}
          </span>
        </div>
      </div>

      <div class="execute-actions">
        <button class="btn btn-outline" @click="resetImport" :disabled="isExecuting">Annuler</button>
        <button class="btn btn-success btn-with-icon" @click="executeImport" :disabled="isExecuting">
          <Loader2 v-if="isExecuting" :size="18" class="animate-spin" />
          <Save v-else :size="18" />
          <span>{{ isExecuting ? 'Importation en cours...' : 'Sauvegarder les résultats' }}</span>
        </button>
      </div>
    </div>

    <div class="panel success-panel" v-if="importSuccess">
      <div class="success-container">
        <CheckCircle :size="48" color="var(--accent)" />
      </div>
      <h2>Résultats enregistrés !</h2>
      <p>Les scores ont été associés aux étudiants avec succès.</p>
      <div class="success-stats">
        <div><strong>{{ importResult.created }}</strong> nouveaux scores ajoutés</div>
        <div><strong>{{ importResult.updated }}</strong> scores mis à jour</div>
      </div>
      <button class="btn btn-primary" @click="resetImport" style="margin-top: 20px;">Faire un nouvel import</button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import api from '@/services/api';
import type {
  Promotion,
  AssessmentPreviewResponse,
  AssessmentMatchPreview,
  AssessmentExecuteRequest
} from '@/types';
import { AssessmentType, Platform } from '@/types/generated_enums';
import {
  Loader2,
  Search,
  SearchCheck,
  AlertTriangle,
  Save,
  CheckCircle
} from 'lucide-vue-next';
import { useUiStore } from '@/stores/ui';

const ui = useUiStore();

// --- ÉTATS. ---
const promotions = ref<Promotion[]>([]);
const selectedPromotion = ref<number | ''>('');
const selectedPlatform = ref<Platform | ''>('');
const selectedType = ref<AssessmentType | ''>('');
const selectedFile = ref<File | null>(null);

const isAnalyzing = ref<boolean>(false);
const previewData = ref<AssessmentPreviewResponse | null>(null);

const isExecuting = ref<boolean>(false);
const importSuccess = ref<boolean>(false);
const importResult = ref({ created: 0, updated: 0 });

const Platforms = Platform;
const AssessmentTypes = AssessmentType;

// --- COMPUTED. ---
const exactMatches = computed(() => {
  return previewData.value?.matched_results.filter(m => m.match_type === 'exact') || [];
});

const fuzzyMatches = computed(() => {
  return previewData.value?.matched_results.filter(m => m.match_type === 'fuzzy') || [];
});

// --- CHARGEMENT. ---
onMounted(async () => {
  try {
    promotions.value = await api.getPromotions();
  } catch (error) {
    console.error("Erreur chargement promotions:", error);
    ui.notify("Erreur lors du chargement des données.", "error");
  }
});

// --- ACTIONS. ---
const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0] || null;
  }
};

const analyzeFile = async () => {
  if (!selectedPromotion.value || !selectedPlatform.value || !selectedType.value || !selectedFile.value) return;

  isAnalyzing.value = true;
  previewData.value = null;

  try {
    const res = await api.previewAssessmentImport(
      selectedPromotion.value as number,
      selectedPlatform.value,
      selectedType.value,
      selectedFile.value
    );

    const data: AssessmentPreviewResponse = res;

    data.matched_results = data.matched_results.map((m: AssessmentMatchPreview) => {
      if (m.match_type === 'fuzzy') m.user_validated = true;
      return m;
    });

    previewData.value = data;
  } catch (error: unknown) {
    console.error("Erreur d'analyse détaillée:", error);
    const err = error as { response?: { data?: { detail?: unknown } }, message?: string };
    let errorMsg = "Une erreur est survenue lors de l'analyse du CSV.";

    if (err.response?.data?.detail) {
      const detail = err.response.data.detail;
      if (Array.isArray(detail)) {
        errorMsg = detail.map(e => e.msg || JSON.stringify(e)).join('\n');
      } else if (typeof detail === 'object') {
        errorMsg = JSON.stringify(detail);
      } else {
        errorMsg = String(detail);
      }
    } else if (err.message) {
      errorMsg = err.message;
    }

    console.error("Erreur d'analyse détaillée:", errorMsg);
    ui.notify("Erreur lors de l'analyse du fichier.", "error");
  } finally {
    isAnalyzing.value = false;
  }
};

const executeImport = async () => {
  if (!previewData.value || !selectedPlatform.value || !selectedType.value) return;
  isExecuting.value = true;

  const executePayload: AssessmentExecuteRequest = {
    platform: selectedPlatform.value as Platform,
    assessment_type: selectedType.value as AssessmentType,
    results: []
  };

  exactMatches.value.forEach((match: AssessmentMatchPreview) => {
    if (match.db_student_id) {
      executePayload.results.push({
        student_id: match.db_student_id,
        score: match.score,
        details: match.details
      });
    }
  });

  fuzzyMatches.value.forEach((match: AssessmentMatchPreview) => {
    if (match.db_student_id && match.user_validated) {
      executePayload.results.push({
        student_id: match.db_student_id,
        score: match.score,
        details: match.details
      });
    }
  });

  try {
    const res = await api.executeAssessmentImport(executePayload);
    importResult.value = { created: res.created, updated: res.updated };
    importSuccess.value = true;
  } catch (error: unknown) {
    console.error("Erreur d'exécution détaillée:", error);
    const err = error as { response?: { data?: { detail?: unknown } }, message?: string };
    let errorMsg = "Erreur critique lors de l'enregistrement des résultats.";

    if (err.response?.data?.detail) {
      const detail = err.response.data.detail;
      if (Array.isArray(detail)) {
        errorMsg = detail.map(e => e.msg || JSON.stringify(e)).join('\n');
      } else if (typeof detail === 'object') {
        errorMsg = JSON.stringify(detail);
      } else {
        errorMsg = String(detail);
      }
    } else if (err.message) {
      errorMsg = err.message;
    }

    console.error(`Erreur : ${errorMsg}`);
    ui.notify("Erreur lors de l'enregistrement des données.", "error");
  } finally {
    isExecuting.value = false;
  }
};

const resetImport = () => {
  selectedFile.value = null;
  previewData.value = null;
  importSuccess.value = false;
  const fileInput = document.querySelector('.file-input') as HTMLInputElement;
  if (fileInput) fileInput.value = '';
};
</script>

<style scoped>
.import-workspace {
  max-width: 1000px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: center;
  margin-bottom: 25px;
}

.header h1 {
  font-size: 1.6rem;
  color: var(--primary);
  margin: 0;
}

.panel {
  background: white;
  padding: 30px;
  border-radius: 8px;
  border: 1px solid #e1e8ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

.step-title {
  color: var(--primary);
  font-size: 1.3rem;
  margin-top: 0;
  margin-bottom: 15px;
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 10px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

/* --- Style Menu Déroulant. --- */
.action-select {
  width: 100%;
  padding: 10px 32px 10px 12px;
  border: 1px solid #bdc3c7;
  border-radius: 6px;
  background-color: #fff;
  color: #2c3e50;
  font-family: inherit;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%237f8c8d' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 16px;
}

.action-select:hover:not(:disabled) {
  border-color: var(--primary);
}

.action-select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(26, 188, 156, 0.2);
}

.action-select:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
  opacity: 0.7;
}

/* --- Style File Input. --- */
.file-input {
  display: block;
  width: 100%;
  padding: 10px;
  border: 2px dashed #bdc3c7;
  border-radius: 6px;
  background-color: #fafafa;
  color: #7f8c8d;
  font-family: inherit;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.file-input:hover:not(:disabled) {
  border-color: var(--accent);
  background-color: #f4f9fd;
}

.file-input::file-selector-button {
  margin-right: 15px;
  padding: 8px 16px;
  border: none;
  background-color: var(--primary);
  color: white;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.file-input::file-selector-button:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.file-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn {
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 1rem;
  border: none;
  transition: 0.2s;
}

.btn-primary {
  background: var(--accent);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  filter: brightness(1.1);
}

.btn-success {
  background: #27ae60;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #219653;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(39, 174, 96, 0.2);
}

.btn-outline {
  background: transparent;
  border: 1px solid #ccc;
  color: #555;
}

.btn-outline:hover:not(:disabled) {
  background: #f8f9fa;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Aperçu Stats. */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 25px;
}

.stat-card {
  background: #f8f9fa;
  border: 1px solid #e1e8ed;
  border-radius: 6px;
  padding: 15px;
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  color: #7f8c8d;
  font-weight: 500;
}

.fuzzy-section {
  margin-bottom: 25px;
  background: #fffdf5;
  border: 1px solid #f9e79f;
  padding: 20px;
  border-radius: 8px;
}

.fuzzy-section h3 {
  margin-top: 0;
  color: #d35400;
  font-size: 1.1rem;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  margin-top: 10px;
}

.preview-table th,
.preview-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
  font-size: 0.95rem;
}

.preview-table th {
  background: #f8f9fa;
  color: #555;
}

.badge-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.badge {
  padding: 5px 10px;
  border-radius: 4px;
  font-weight: 500;
  font-size: 0.85rem;
}

.badge-red {
  background: #fadbd8;
  color: #c0392b;
  border: 1px solid #f5b7b1;
}

.execute-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 20px;
  border-top: 2px solid #ecf0f1;
  padding-top: 20px;
}

.success-panel {
  text-align: center;
  padding: 50px 20px;
}

.success-icon {
  font-size: 4rem;
  margin-bottom: 15px;
}

.success-stats {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-top: 20px;
  font-size: 1.1rem;
  color: #2c3e50;
}

/* Alignement des icônes dans les titres H3 */
.title-with-icon {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 20px 0;
}

/* On définit le bouton success s'il n'existe pas encore */
.btn-success {
  background-color: var(--accent);
  /* Ton vert teal */
  color: white;
}

.btn-success:hover:not(:disabled) {
  background-color: #16a085;
}

/* Style pour l'icône de succès géante */
.success-container {
  display: flex;
  justify-content: center;
  padding: 20px;
}

/* Animation de rotation (déjà vue précédemment, mais au cas où) */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}
</style>