<template>
  <div class="import-view">
    <div class="header">
      <button class="btn btn-outline" @click="router.push('/gestion')">← Retour</button>
      <h1>Importation de Dictées</h1>
    </div>

    <div class="form-card">
      <AppLoading v-if="isLoading" message="Chargement des données..." />

      <div v-else>
        <div class="global-settings grid-3">
          <div class="form-group">
            <label>Promotion cible * :</label>
            <select v-model="selectedPromotion" @change="handlePromotionChange">
              <option value="" disabled>-- Sélectionnez une promotion --</option>
              <option v-for="promo in promotions" :key="promo.id" :value="promo.id">
                {{ promo.name }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Associer à une dictée référente * :</label>
            <select v-model="selectedDictation">
              <option value="" disabled>-- Sélectionnez une dictée --</option>
              <option v-for="dict in dictations" :key="dict.id" :value="dict.id">
                {{ dict.title }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Type d'évaluation :</label>
            <select v-model="submissionType">
              <option v-for="type in Object.values(AssessmentTypes)" :key="type" :value="type">
                {{ type }}
              </option>
            </select>
          </div>
        </div>

        <div class="form-group" style="margin-top: 25px;">
          <label>Fichiers étudiants (.txt) :</label>
          <div class="upload-zone" @click="triggerFileInput" @dragover.prevent="dragOver = true"
            @dragleave.prevent="dragOver = false" @drop.prevent="handleDrop"
            :class="{ 'drag-over': dragOver, 'disabled': !selectedPromotion }">
            <FileText :size="48" class="upload-icon" />
            <h3 v-if="selectedPromotion">Cliquez ou glissez-déposez vos fichiers .txt ici</h3>
            <h3 v-else style="color: var(--danger);">Veuillez sélectionner une promotion d'abord</h3>
            <p>Le format conseillé du nom de fichier est "NOM_Prenom_*.txt"</p>
            <input type="file" ref="fileInputRef" style="display: none;" accept=".txt" multiple
              :disabled="!selectedPromotion" @change="handleFileUpload">
          </div>
        </div>

        <div v-if="parsedFiles.length > 0" class="files-list">
          <h3 class="list-title">Traitement des fichiers ({{ parsedFiles.length }})</h3>

          <div v-for="fileItem in parsedFiles" :key="fileItem.id" class="file-item"
            :class="`status-${fileItem.status.toLowerCase()}`">
            <div class="file-info">
              <span class="file-name">{{ fileItem.originalName }}</span>
              <span class="parsed-name" v-if="fileItem.parsedName">
                <ArrowRight :size="14" />
                <span>Extrait : "{{ fileItem.parsedName }}"</span>
              </span>
            </div>

            <div v-if="fileItem.status === 'MATCHED' || fileItem.status === 'CONFIRMED'" class="file-action success">
              <CheckCircle :size="18" />
              <span>Associé à <strong>{{ getStudentName(fileItem.studentId) }}</strong></span>
              <button class="btn btn-sm btn-outline btn-with-icon" style="margin-left: auto;"
                @click="openCreateStudentForm(fileItem)">
                <UserPlus :size="14" /> <span>Créer un autre étudiant</span>
              </button>
            </div>

            <div v-if="fileItem.status === 'SUGGESTED'" class="file-action warning">
              <AlertTriangle :size="18" />
              <span>Voulez-vous dire <strong>{{ fileItem.suggestedStudent?.last_name }} {{
                fileItem.suggestedStudent?.first_name }}</strong> ?</span>
              <div class="btn-group">
                <button class="btn btn-sm btn-success" @click="confirmSuggestion(fileItem)">Oui</button>
                <button class="btn btn-sm btn-outline" @click="rejectSuggestion(fileItem)">Non</button>
              </div>
            </div>

            <div v-if="fileItem.status === 'UNKNOWN'" class="file-action danger">
              <XCircle :size="18" />
              <span>Aucun étudiant trouvé dans cette promotion.</span>
              <div class="btn-group">
                <button class="btn btn-sm btn-primary btn-with-icon" @click="openCreateStudentForm(fileItem)">
                  <Plus :size="14" />
                  <span>Créer étudiant</span>
                </button>
                <button class="btn btn-sm btn-outline" @click="ignoreFile(fileItem)">Ignorer fichier</button>
              </div>
            </div>

            <div v-if="fileItem.status === 'IGNORED'" class="file-action text-muted">
              Fichier ignoré.
              <button class="btn btn-sm btn-outline" @click="reprocessFile(fileItem)"
                style="margin-left: 10px;">Annuler</button>
            </div>
          </div>
        </div>

        <div class="actions" v-if="parsedFiles.length > 0">
          <p v-if="!canSubmit && !isSubmitting" class="warning-text title-with-icon" style="margin-right: 15px;">
            <AlertTriangle :size="18" />
            <span>Traitez les fichiers en jaune et rouge avant de valider.</span>
          </p>
          <button v-if="!isSubmitting" class="btn btn-primary btn-large btn-with-icon" @click="submitAll"
            :disabled="isSubmitting || !canSubmit">
            <Loader2 v-if="isSubmitting" :size="20" class="animate-spin" />
            <template v-else>
              <span>Envoyer {{ filesReadyToSubmit }} dictée(s)</span>
              <Rocket :size="20" />
            </template>
          </button>

          <div v-else class="progress-container">
            <div class="progress-text">
              Analyse en cours : {{ processedCount }} / {{ totalToProcess }} ({{ importProgress }}%)
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: importProgress + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <StudentFormModal
    :show="showCreateModal"
    :student-data="(newStudentForm as Student)"
    :promotions="promotions"
    :groups="groups"
    :is-edit="false"
    :lock-promotion-id="selectedPromotion === '' ? null : selectedPromotion"
    @close="showCreateModal = false"
    @save="handleCreateStudent"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import type { Student, Dictation, Promotion, Group, StudentCreatePayload } from '@/types';
import { AssessmentType } from '@/types/generated_enums';
import AppLoading from '@/components/common/AppLoading.vue';
import {
  FileText,
  CheckCircle,
  UserPlus,
  AlertTriangle,
  XCircle,
  Plus,
  ArrowRight,
  Rocket,
  Loader2
} from 'lucide-vue-next';
import { useUiStore } from '@/stores/ui';
import StudentFormModal from '@/components/students/StudentFormModal.vue';

const ui = useUiStore();

const router = useRouter();

const AssessmentTypes = AssessmentType;

// --- TYPES LOCAUX. ---
type FileStatus = 'MATCHED' | 'SUGGESTED' | 'UNKNOWN' | 'CONFIRMED' | 'IGNORED';

interface ParsedFile {
  id: string;
  file: File;
  content: string;
  originalName: string;
  parsedName: string;
  status: FileStatus;
  studentId: string | null;
  suggestedStudent: Student | null;
}

// --- ÉTATS. ---
const isLoading = ref(true);
const isSubmitting = ref(false);
const dragOver = ref(false);

const students = ref<Student[]>([]);
const dictations = ref<Dictation[]>([]);
const promotions = ref<Promotion[]>([]);
const groups = ref<Group[]>([]);

// Valeurs globales du formulaire.
const selectedPromotion = ref<number | ''>('');
const selectedDictation = ref<number | ''>('');
const submissionType = ref<AssessmentType>(AssessmentType.INITIAL);

// Liste des fichiers déposés.
const parsedFiles = ref<ParsedFile[]>([]);
const fileInputRef = ref<HTMLInputElement | null>(null);

const importProgress = ref(0);
const processedCount = ref(0);
const totalToProcess = ref(0);

// États pour le formulaire de création.
const showCreateModal = ref(false);
const editingFileItem = ref<ParsedFile | null>(null);
const newStudentForm = ref<Partial<Student>>({
  first_name: '',
  last_name: '',
  promotion_id: undefined
});

// --- CHARGEMENT. ---
onMounted(async () => {
  try {
    const [studentsRes, dictationsRes, promoRes, groupRes] = await Promise.all([
      api.getStudents(),
      api.getDictations(),
      api.getPromotions(),
      api.getGroups()
    ]);
    students.value = studentsRes;
    dictations.value = dictationsRes;
    promotions.value = promoRes;
    groups.value = groupRes;
  } catch (error) {
    console.error("Erreur de chargement :", error);
    ui.notify("Erreur lors du chargement des données.", "error");
  } finally {
    isLoading.value = false;
  }
});

// --- UTILITAIRES. ---
const normalizeText = (text: string) => {
  return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
};

const levenshtein = (a: string, b: string): number => {
  const matrix = Array.from({ length: a.length + 1 }, () => Array<number>(b.length + 1).fill(0));
  for (let i = 0; i <= a.length; i++) matrix[i]![0] = i;
  for (let j = 0; j <= b.length; j++) matrix[0]![j] = j;

  for (let i = 1; i <= a.length; i++) {
    const row = matrix[i]!;
    const prevRow = matrix[i - 1]!;
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      row[j] = Math.min(
        prevRow[j]! + 1,
        row[j - 1]! + 1,
        prevRow[j - 1]! + cost
      );
    }
  }
  return matrix[a.length]![b.length]!;
};

// --- GESTION DES FICHIERS. ---
const handlePromotionChange = () => {
  if (parsedFiles.value.length > 0) {
    if (confirm("Changer de promotion va réinitialiser les fichiers déjà chargés. Continuer ?")) {
      parsedFiles.value = [];
    }
  }
};

const triggerFileInput = () => {
  if (!selectedPromotion.value) {
    ui.notify("Veuillez sélectionner une promotion d'abord.", "error");
    return;
  }
  if (fileInputRef.value) fileInputRef.value.click();
};

const handleDrop = (e: DragEvent) => {
  dragOver.value = false;
  if (!selectedPromotion.value) {
    ui.notify("Veuillez sélectionner une promotion d'abord.", "error");
    return;
  }
  if (e.dataTransfer?.files) processFiles(Array.from(e.dataTransfer.files));
};

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files) processFiles(Array.from(target.files));
  target.value = '';
};

const processFiles = async (files: File[]) => {
  for (const file of files) {
    if (file.type !== 'text/plain') continue;

    const content = await file.text();

    const baseName = file.name.replace('.txt', '');
    const nameParts = baseName.split('_').slice(0, 2);
    const cleanName = nameParts.join(' ').trim();

    const parsedFile: ParsedFile = {
      id: Math.random().toString(36).substr(2, 9),
      file,
      content,
      originalName: file.name,
      parsedName: cleanName,
      status: 'UNKNOWN',
      studentId: null,
      suggestedStudent: null
    };

    findMatchForFile(parsedFile);
    parsedFiles.value.push(parsedFile);
  }
};

const findMatchForFile = (fileItem: ParsedFile) => {
  const normFileName = normalizeText(fileItem.parsedName);

  const studentsInPromo = students.value.filter(s => s.promotion_id === selectedPromotion.value);

  let bestMatch: Student | null = null;
  let minDistance = Infinity;

  for (const student of studentsInPromo) {
    const fullName1 = normalizeText(`${student.last_name} ${student.first_name}`);
    const fullName2 = normalizeText(`${student.first_name} ${student.last_name}`);

    if (normFileName === fullName1 || normFileName === fullName2) {
      fileItem.status = 'MATCHED';
      fileItem.studentId = student.id;
      return;
    }

    const dist1 = levenshtein(normFileName, fullName1);
    const dist2 = levenshtein(normFileName, fullName2);
    const currentMin = Math.min(dist1, dist2);

    if (currentMin < minDistance) {
      minDistance = currentMin;
      bestMatch = student;
    }
  }

  const maxAllowedDistance = Math.floor(normFileName.length / 4);

  if (bestMatch && minDistance <= maxAllowedDistance && minDistance > 0) {
    fileItem.status = 'SUGGESTED';
    fileItem.suggestedStudent = bestMatch;
  } else {
    fileItem.status = 'UNKNOWN';
  }
};

// --- ACTIONS UTILISATEUR SUR LES FICHIERS. ---
const confirmSuggestion = (fileItem: ParsedFile) => {
  fileItem.status = 'CONFIRMED';
  fileItem.studentId = fileItem.suggestedStudent!.id;
};

const rejectSuggestion = (fileItem: ParsedFile) => {
  fileItem.status = 'UNKNOWN';
  fileItem.suggestedStudent = null;
};

const ignoreFile = (fileItem: ParsedFile) => {
  fileItem.status = 'IGNORED';
};

const reprocessFile = (fileItem: ParsedFile) => {
  findMatchForFile(fileItem);
};

// --- CRÉATION ÉTUDIANT MANQUANT. ---
const openCreateStudentForm = (fileItem: ParsedFile) => {
  editingFileItem.value = fileItem;

  const parts = fileItem.parsedName?.split(' ') || [];
  
  newStudentForm.value = {
    last_name: parts[0]?.toUpperCase() || '',
    first_name: parts.slice(1).join(' ') || '',
    promotion_id: selectedPromotion.value === '' ? undefined : selectedPromotion.value,
    group_id: undefined
  };

  showCreateModal.value = true;
};

const handleCreateStudent = async (payload: StudentCreatePayload) => {
  try {
    const newStudent = await api.createStudent(payload);
    
    if (editingFileItem.value) {
      editingFileItem.value.status = 'CONFIRMED';
      editingFileItem.value.studentId = newStudent.id;
    }

    ui.notify("Étudiant créé et associé !");
    showCreateModal.value = false;
  } catch (err) {
    console.error("Erreur : ", err)
  }
};

const getStudentName = (uuid: string | null) => {
  if (!uuid) return '';
  const s = students.value.find(s => s.id === uuid);
  return s ? `${s.last_name} ${s.first_name}` : 'Inconnu';
};

// --- VALIDATION FINALE. ---
const canSubmit = computed(() => {
  return parsedFiles.value.length > 0 && parsedFiles.value.every(f =>
    f.status === 'MATCHED' || f.status === 'CONFIRMED' || f.status === 'IGNORED'
  );
});

const filesReadyToSubmit = computed(() => {
  return parsedFiles.value.filter(f => f.status === 'MATCHED' || f.status === 'CONFIRMED').length;
});

const submitAll = async () => {
  if (!selectedDictation.value || !selectedPromotion.value) {
    ui.notify("Veuillez vérifier vos sélections.", "error");
    return;
  }

  const filesToProcess = parsedFiles.value.filter(f => f.status === 'MATCHED' || f.status === 'CONFIRMED');
  if (filesToProcess.length === 0) return;

  isSubmitting.value = true;
  importProgress.value = 0;
  processedCount.value = 0;
  totalToProcess.value = filesToProcess.length;

  const CHUNK_SIZE = 5;

  try {
    for (let i = 0; i < filesToProcess.length; i += CHUNK_SIZE) {
      const chunk = filesToProcess.slice(i, i + CHUNK_SIZE);

      const payload = chunk.map(f => ({
        student_id: f.studentId as string,
        dictation_id: Number(selectedDictation.value),
        assessment_type: submissionType.value,
        content_student: f.content
      }));

      await api.createBulkSubmissions(payload);

      processedCount.value += chunk.length;
      importProgress.value = Math.round((processedCount.value / totalToProcess.value) * 100);
    }

    setTimeout(() => {
      ui.notify("Les dictées ont été importées.", "success");
      setTimeout(() => {
        router.push('/correction');
      }, 1500);
    }, 500);

  } catch (error) {
    console.error("Erreur d'import :", error);
    ui.notify("Erreur lors de l'envoi en masse.", "error");
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 1.6rem;
  color: var(--primary);
  margin: 0;
}

.form-card {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  border: 1px solid #e1e8ed;
}

.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  padding-bottom: 20px;
  border-bottom: 2px solid #f0f2f5;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: var(--primary);
}

.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 1rem;
  outline: none;
}

.form-group select:focus {
  border-color: var(--accent);
}

.form-group select:disabled {
  background-color: #f1f1f1;
  cursor: not-allowed;
}

/* Upload Zone. */
.upload-zone {
  border: 2px dashed #bdc3c7;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  background: #f8f9fa;
  cursor: pointer;
  transition: 0.2s;
}

.upload-zone.drag-over {
  border-color: var(--accent);
  background: #f0f8ff;
}

.upload-zone.disabled {
  border-color: #ecf0f1;
  background: #fdfdfd;
  cursor: not-allowed;
  opacity: 0.6;
}

.upload-zone i {
  font-size: 3rem;
  color: #bdc3c7;
  display: block;
  margin-bottom: 10px;
  font-style: normal;
}

.upload-zone h3 {
  color: var(--primary);
  margin-bottom: 5px;
}

.upload-zone p {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.files-list {
  margin-top: 30px;
  background: #fafafa;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #eee;
}

.list-title {
  margin-top: 0;
  color: var(--primary);
  font-size: 1.1rem;
  margin-bottom: 15px;
}

.file-item {
  background: white;
  border: 1px solid #e1e8ed;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: 0.2s;
  border-left: 5px solid #ccc;
}

.file-item:hover {
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.file-item.status-matched,
.file-item.status-confirmed {
  border-left-color: #2ecc71;
}

.file-item.status-suggested {
  border-left-color: #f1c40f;
}

.file-item.status-unknown {
  border-left-color: #e74c3c;
}

.file-item.status-ignored {
  border-left-color: #95a5a6;
  opacity: 0.6;
}

.file-info {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-weight: 600;
  color: var(--text);
}

.parsed-name {
  font-size: 0.85rem;
  color: #7f8c8d;
  margin-top: 3px;
  font-style: italic;
}

.file-action {
  display: flex;
  align-items: center;
  gap: 15px;
  font-size: 0.9rem;
}

.file-action.success {
  color: #27ae60;
}

.file-action.warning {
  color: #d35400;
  background: #fdfae7;
  padding: 8px 12px;
  border-radius: 4px;
}

.file-action.danger {
  color: #c0392b;
  background: #fdedec;
  padding: 8px 12px;
  border-radius: 4px;
}

.btn-group {
  display: flex;
  gap: 5px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  border: none;
  transition: 0.2s;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 0.85rem;
}

.btn-large {
  padding: 12px 24px;
  font-size: 1.1rem;
}

.btn-primary {
  background: var(--accent);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #12876f;
}

.btn-success {
  background: #2ecc71;
  color: white;
}

.btn-success:hover {
  background: #27ae60;
}

.btn-outline {
  background: transparent;
  border: 1px solid #ccc;
  color: var(--text);
}

.btn-outline:hover {
  background: #eee;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 25px;
  border-top: 2px solid #f0f2f5;
  padding-top: 20px;
}

.warning-text {
  color: #e67e22;
  font-weight: bold;
}

/* Icône dans la zone d'upload */
.upload-icon {
  color: var(--primary);
  opacity: 0.5;
  margin-bottom: 15px;
}

.drag-over .upload-icon {
  color: var(--accent);
  opacity: 1;
  transform: scale(1.1);
  transition: 0.3s;
}

/* Alignement dans les bandeaux d'action */
.file-action {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 15px;
  border-radius: 8px;
  margin-bottom: 10px;
}

.file-action.success {
  background-color: #ecfdf5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.file-action.warning {
  background-color: #fffbeb;
  color: #92400e;
  border: 1px solid #fde68a;
}

.file-action.danger {
  background-color: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.warning-text {
  color: #92400e;
  font-weight: 500;
}

.parsed-name {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: #7f8c8d;
  margin-left: 10px;
  font-style: italic;
}

/* Style pour le bouton principal d'envoi */
.btn-large {
  padding: 15px 30px;
  font-size: 1.1rem;
  width: 100%;
  /* Optionnel : pour qu'il prenne toute la largeur en bas de page */
  margin-top: 20px;
  box-shadow: 0 4px 6px rgba(26, 188, 156, 0.2);
}

.btn-large:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(26, 188, 156, 0.3);
}

/* Animation de rotation pour le loader */
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

.progress-container {
  width: 100%;
  max-width: 400px;
  text-align: right;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.progress-text {
  font-weight: bold;
  color: var(--primary);
  margin-bottom: 8px;
  font-size: 0.95rem;
}

.progress-bar {
  width: 100%;
  height: 12px;
  background-color: #ecf0f1;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.progress-fill {
  height: 100%;
  background-color: var(--accent);
  transition: width 0.4s ease-out;
}
</style>