<template>
  <div class="import-workspace">
    <div class="header">
      <button class="btn btn-outline" style="margin-right: 15px;" @click="$router.push('/gestion')">← Retour</button>
      <h1 style="display: inline-block;">Importation d'une Étude (CSV)</h1>
    </div>

    <div class="panel" v-if="!importSuccess">
      <h2 class="step-title">1. Sélection des données</h2>

      <div class="form-row">
        <div class="form-group" style="flex: 1;">
          <label>Promotion cible :</label>
          <select v-model="selectedPromotion" :disabled="isAnalyzing">
            <option value="" disabled>-- Choisissez une promotion --</option>
            <option v-for="promo in promotions" :key="promo.id" :value="promo.id">
              {{ promo.name }}
            </option>
          </select>
        </div>

        <div class="form-group" style="flex: 2;">
          <label>Fichier CSV de l'étude :</label>
          <input type="file" accept=".csv" @change="handleFileUpload" :disabled="isAnalyzing" class="file-input" />
        </div>
      </div>

      <button class="btn btn-primary btn-with-icon" :disabled="!selectedPromotion || !selectedFile || isAnalyzing"
        @click="analyzeFile">
        <Loader2 v-if="isAnalyzing" :size="18" class="animate-spin" />
        <Search v-else :size="18" />
        <span>{{ isAnalyzing ? 'Analyse en cours...' : 'Analyser le fichier' }}</span>
      </button>
    </div>

    <div class="panel" v-if="previewData && !importSuccess" style="margin-top: 20px;">
      <h2 class="step-title">2. Rapport d'analyse</h2>
      <p style="color: #7f8c8d; font-size: 0.95rem; margin-bottom: 20px;">
        Vérifiez les correspondances trouvées avant de lancer l'importation définitive.
      </p>

      <div v-if="previewData.groups_to_create.length > 0" class="alert-box info-box">
        <div class="alert-message title-with-icon">
          <AlertTriangle :size="20" color="#e67e22" />
          <strong>Nouveaux groupes détectés :</strong>
        </div>
        <p style="margin: 5px 0 0 0; font-size: 0.9rem;">
          Les groupes suivants n'existent pas en base de données :
          <span v-for="g in previewData.groups_to_create" :key="g" class="badge badge-gray">{{ g }}</span>
          <br>Ils seront créés automatiquement lors de l'importation.
        </p>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-number" style="color: #27ae60;">{{ previewData.exact_matches.length }}</span>
          <span class="stat-label">Correspondances exactes</span>
        </div>
        <div class="stat-card">
          <span class="stat-number" style="color: #f39c12;">{{ previewData.fuzzy_matches.length }}</span>
          <span class="stat-label">Correspondances floues (fautes)</span>
        </div>
        <div class="stat-card">
          <span class="stat-number" style="color: #3498db;">{{ previewData.new_students.length }}</span>
          <span class="stat-label">Nouveaux étudiants</span>
        </div>
      </div>

      <div v-if="previewData.fuzzy_matches.length > 0" class="fuzzy-section">
        <h3 class="title-with-icon">
          <SearchCheck :size="24" color="var(--primary)" />
          Vérification requise (Fautes de frappe possibles)
        </h3>
        <table class="preview-table">
          <thead>
            <tr>
              <th>Nom dans le CSV</th>
              <th>Étudiant trouvé en Base</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(match, index) in previewData.fuzzy_matches" :key="index">
              <td><strong>{{ match.csv_data.first_name }} {{ match.csv_data.last_name }}</strong></td>
              <td>{{ match.db_first_name }} {{ match.db_last_name }}</td>
              <td>
                <select v-model="match.user_choice" class="action-select">
                  <option value="update">Mettre à jour l'étudiant existant</option>
                  <option value="create">Créer comme nouvel étudiant</option>
                </select>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="execute-actions">
        <button class="btn btn-outline" @click="resetImport" :disabled="isExecuting">Annuler</button>
        <button class="btn btn-success btn-with-icon" @click="executeImport" :disabled="isExecuting">
          <Loader2 v-if="isExecuting" :size="18" class="animate-spin" />
          <Rocket v-else :size="18" />
          <span>{{ isExecuting ? 'Importation en cours...' : 'Valider et Importer' }}</span>
        </button>
      </div>
    </div>

    <div class="panel success-panel" v-if="importSuccess">
      <div class="success-container">
        <CheckCircle :size="60" color="var(--accent)" />
      </div>
      <h2>Importation réussie !</h2>
      <p>La base de données a été mise à jour avec succès.</p>
      <div class="success-stats">
        <div><strong>{{ importResult.created }}</strong> étudiants créés</div>
        <div><strong>{{ importResult.updated }}</strong> étudiants mis à jour</div>
      </div>
      <button class="btn btn-primary" @click="resetImport" style="margin-top: 20px;">Faire un nouvel import</button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import api from '@/services/api';
import type { Promotion, StudentMatchPreview, ImportPreviewResponse, ImportExecutePayload } from '@/types';
import {
  Search,
  Loader2,
  AlertTriangle,
  SearchCheck,
  Rocket,
  CheckCircle
} from 'lucide-vue-next';
import { useUiStore } from '@/stores/ui';

const ui = useUiStore();

// --- ÉTATS. ---
const promotions = ref<Promotion[]>([]);
const selectedPromotion = ref<number | ''>('');
const selectedFile = ref<File | null>(null);

const isAnalyzing = ref(false);
const previewData = ref<ImportPreviewResponse | null>(null);

const isExecuting = ref(false);
const importSuccess = ref(false);
const importResult = ref({ created: 0, updated: 0 });

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
  if (!selectedPromotion.value || !selectedFile.value) return;

  isAnalyzing.value = true;
  previewData.value = null;

  try {
    const res = await api.previewImport(selectedPromotion.value as number, selectedFile.value);

    const data: ImportPreviewResponse = res;
    data.groups_to_create.sort((a, b) => a.localeCompare(b, 'fr'));
    data.fuzzy_matches = data.fuzzy_matches.map((m: StudentMatchPreview) => ({ ...m, user_choice: 'update' }));

    previewData.value = data;
  } catch (error: unknown) {
    console.error("Erreur d'analyse:", error);
    ui.notify("Erreur lors de l'analyse du fichier.", "error");
  } finally {
    isAnalyzing.value = false;
  }
};

const executeImport = async () => {
  if (!previewData.value || !selectedPromotion.value) return;
  isExecuting.value = true;

  const executePayload: ImportExecutePayload = {
    promotion_id: selectedPromotion.value as number,
    create_missing_groups: true,
    students: []
  };

  previewData.value.exact_matches.forEach((match: StudentMatchPreview) => {
    executePayload.students.push({
      csv_data: match.csv_data,
      action: 'update',
      db_student_id: match.db_student_id ?? null
    });
  });

  previewData.value.fuzzy_matches.forEach((match: StudentMatchPreview) => {
    executePayload.students.push({
      csv_data: match.csv_data,
      action: match.user_choice || 'create',
      db_student_id: match.user_choice === 'update' ? (match.db_student_id ?? null) : null
    });
  });

  previewData.value.new_students.forEach((match: StudentMatchPreview) => {
    executePayload.students.push({
      csv_data: match.csv_data,
      action: 'create',
      db_student_id: null
    });
  });

  try {
    const res = await api.executeImport(executePayload);
    importResult.value = { created: res.created, updated: res.updated };
    importSuccess.value = true;
  } catch (error: unknown) {
    console.error("Erreur d'exécution:", error);
    ui.notify("Erreur lors de l'importation de l'étude.", "error");
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
  margin-bottom: 5px;
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 10px;
}

.form-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  margin-top: 20px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 1rem;
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

/* APERCU. */
.alert-box {
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.info-box {
  background: #e8f4f8;
  border: 1px solid #bce0ee;
  color: #2c3e50;
}

.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: bold;
  font-size: 0.8rem;
  margin-right: 5px;
  display: inline-block;
  margin-top: 5px;
}

.badge-gray {
  background: #bdc3c7;
  color: white;
}

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

.action-select {
  width: 100%;
  max-width: 300px;
  padding: 8px 32px 8px 12px;
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
  -moz-appearance: none;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%237f8c8d' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 16px;
}

.action-select:hover {
  border-color: var(--primary);
}

.action-select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(26, 188, 156, 0.2);
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

/* Pour l'alignement icône + texte dans les messages forts */
.alert-message {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 15px 0;
  color: #d35400;
  /* Orange foncé pour l'alerte */
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 25px;
}

/* Le bouton success si tu ne l'avais pas encore */
.btn-success {
  background-color: var(--accent);
  color: white;
}

.btn-success:hover:not(:disabled) {
  background-color: #16a085;
}
</style>