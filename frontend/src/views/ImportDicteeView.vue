<template>
  <div class="import-view">
    <div class="page-header">
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
          <label>Fichiers étudiants (.txt ou .json) :</label>

          <div class="format-info-row">
            <div class="format-badge txt-badge">
              <FileText :size="14" />
              <span>.txt — Un fichier par étudiant, nommé "NOM_Prenom_*.txt"</span>
            </div>
            <div class="format-badge json-badge">
              <FileJson :size="14" />
              <span>.json — Export de formulaire, plusieurs étudiants par fichier</span>
            </div>
          </div>

          <div class="upload-zone" @click="triggerFileInput" @dragover.prevent="dragOver = true"
            @dragleave.prevent="dragOver = false" @drop.prevent="handleDrop"
            :class="{ 'drag-over': dragOver, 'disabled': !canUpload }">
            <FileUp :size="48" class="upload-icon" />
            <h3 v-if="canUpload">Cliquez ou glissez-déposez vos fichiers .txt / .json ici.</h3>
            <h3 v-else style="color: var(--danger);">Veuillez sélectionner une promotion et une dictée d'abord.</h3>
            <p>Formats acceptés : <strong>.txt</strong> (un par étudiant) ou <strong>.json</strong> (export formulaire,
              multi-étudiants)</p>
            <input type="file" ref="fileInputRef" style="display: none;" accept=".txt,.json" multiple
              :disabled="!canUpload" @change="handleFileUpload">
          </div>
        </div>

        <div v-if="parsedFiles.length > 0" class="files-list">
          <div class="list-header">
            <h3 class="list-title">Traitement des fichiers ({{ parsedFiles.length }} entrée(s))</h3>
            <div class="list-summary">
              <span class="summary-badge matched">{{ countByStatus('MATCHED') + countByStatus('CONFIRMED') }}
                associé(s)</span>
              <span class="summary-badge warned">{{ countByStatus('SUGGESTED') }} à vérifier</span>
              <span class="summary-badge unknown">{{ countByStatus('UNKNOWN') }} inconnu(s)</span>
              <span class="summary-badge ignored">{{ countByStatus('IGNORED') }} ignoré(s)</span>
            </div>
          </div>

          <div v-for="fileItem in parsedFiles" :key="fileItem.id" class="file-item"
            :class="`status-${fileItem.status.toLowerCase()}`">
            <div class="file-info">
              <div class="file-name-row">
                <span class="file-type-icon" :class="fileItem.sourceType === 'json' ? 'json' : 'txt'">
                  {{ fileItem.sourceType === 'json' ? 'JSON' : 'TXT' }}
                </span>
                <span class="file-name">{{ fileItem.originalName }}</span>
              </div>
              <span class="parsed-name" v-if="fileItem.parsedName">
                <ArrowRight :size="14" />
                <span>Extrait : "{{ fileItem.parsedName }}"</span>
              </span>
              <span v-if="fileItem.sourceType === 'json' && fileItem.emailHint" class="email-hint">
                <Mail :size="12" />
                {{ fileItem.emailHint }}
              </span>
            </div>

            <div v-if="fileItem.status === 'MATCHED' || fileItem.status === 'CONFIRMED'" class="file-action success">
              <div class="action-content">
                <div class="match-info">
                  <CheckCircle :size="18" />
                  <span>Associé à <strong>{{ getStudentName(fileItem.studentId) }}</strong></span>
                </div>
                <div v-if="willOverwrite(fileItem.studentId)" class="overwrite-warning">
                  <AlertTriangle :size="14" />
                  <span>Attention : remplacera la dictée {{ submissionType.toLowerCase() }} existante.</span>
                </div>
              </div>
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
          <div v-if="!canSubmit && !isSubmitting" class="warning-text title-with-icon">
            <AlertTriangle :size="18" />
            <span>Traitez les fichiers en jaune et rouge avant de valider.</span>
          </div>

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

  <StudentFormModal :show="showCreateModal" :student-data="(newStudentForm as Student)" :promotions="promotions"
    :groups="groups" :tools="tools" :is-edit="false"
    :lock-promotion-id="selectedPromotion === '' ? null : selectedPromotion" @close="showCreateModal = false"
    @save="handleCreateStudent" />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import type { Student, Dictation, Promotion, Group, StudentCreatePayload, StudentWithScores, Tool } from '@/types';
import { AssessmentType } from '@/types/generated_enums';
import AppLoading from '@/components/common/AppLoading.vue';
import {
  FileText,
  FileUp,
  CheckCircle,
  UserPlus,
  AlertTriangle,
  XCircle,
  Plus,
  ArrowRight,
  Rocket,
  Loader2,
  Mail,
} from 'lucide-vue-next';
import { useUiStore } from '@/stores/ui';
import StudentFormModal from '@/components/students/StudentFormModal.vue';
import { shallowRef } from 'vue';

const FileJsonIcon = shallowRef(FileText);

import('lucide-vue-next').then((module) => {
  if (module.FileJson) {
    FileJsonIcon.value = module.FileJson;
  }
}).catch(() => {
  // En cas d'erreur, on garde FileText (qui est déjà la valeur par défaut).
});

const ui = useUiStore();
const router = useRouter();
const AssessmentTypes = AssessmentType;

// --- TYPES LOCAUX. ---
type FileStatus = 'MATCHED' | 'SUGGESTED' | 'UNKNOWN' | 'CONFIRMED' | 'IGNORED';
type SourceType = 'txt' | 'json';

interface ParsedFile {
  id: string;
  file: File;
  content: string;
  originalName: string;
  parsedName: string;
  status: FileStatus;
  studentId: string | null;
  suggestedStudent: StudentWithScores | null;
  sourceType: SourceType;
  emailHint?: string;
}

/** Entrée attendue dans un JSON d'export formulaire. */
interface JsonDictationEntry {
  nomdefamille?: string;
  nom?: string;
  prnom?: string;
  rponse1?: string;
  reponse1?: string;
  response1?: string;
  adressedecourriel?: string;
  email?: string;
  [key: string]: unknown;
}

// --- ÉTATS. ---
const isLoading = ref(true);
const isSubmitting = ref(false);
const dragOver = ref(false);

const students = ref<StudentWithScores[]>([]);
const dictations = ref<Dictation[]>([]);
const promotions = ref<Promotion[]>([]);
const groups = ref<Group[]>([]);
const tools = ref<Tool[]>([]);

const selectedPromotion = ref<number | ''>('');
const selectedDictation = ref<number | ''>('');
const submissionType = ref<AssessmentType>(AssessmentType.INITIAL);

const parsedFiles = ref<ParsedFile[]>([]);
const fileInputRef = ref<HTMLInputElement | null>(null);

const importProgress = ref(0);
const processedCount = ref(0);
const totalToProcess = ref(0);

const showCreateModal = ref(false);
const editingFileItem = ref<ParsedFile | null>(null);
const newStudentForm = ref<Partial<Student>>({ first_name: '', last_name: '' });

// --- CHARGEMENT. ---
onMounted(async () => {
  try {
    const [studentsRes, dictationsRes, promoRes, groupRes, toolsRes] = await Promise.all([
      api.getStudentsWithScores(),
      api.getDictations(),
      api.getPromotions(),
      api.getGroups(),
      api.getTools(),
    ]);
    students.value = studentsRes;
    dictations.value = dictationsRes;
    promotions.value = promoRes;
    groups.value = groupRes;
    tools.value = toolsRes;
  } catch (error) {
    console.error('Erreur de chargement :', error);
    ui.notify('Erreur lors du chargement des données.', 'error');
  } finally {
    isLoading.value = false;
  }
});

// --- COMPUTED. ---
const canUpload = computed(() => selectedPromotion.value !== '' && selectedDictation.value !== '');

const canSubmit = computed(() =>
  parsedFiles.value.length > 0 &&
  parsedFiles.value.every(f => ['MATCHED', 'CONFIRMED', 'IGNORED'].includes(f.status))
);

const filesReadyToSubmit = computed(() =>
  parsedFiles.value.filter(f => f.status === 'MATCHED' || f.status === 'CONFIRMED').length
);

const countByStatus = (status: FileStatus) =>
  parsedFiles.value.filter(f => f.status === status).length;

// --- UTILITAIRES. ---
const normalizeText = (text: string) =>
  text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();

const levenshtein = (a: string, b: string): number => {
  const matrix = Array.from({ length: a.length + 1 }, () => Array<number>(b.length + 1).fill(0));
  for (let i = 0; i <= a.length; i++) matrix[i]![0] = i;
  for (let j = 0; j <= b.length; j++) matrix[0]![j] = j;
  for (let i = 1; i <= a.length; i++) {
    const row = matrix[i]!;
    const prevRow = matrix[i - 1]!;
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      row[j] = Math.min(prevRow[j]! + 1, row[j - 1]! + 1, prevRow[j - 1]! + cost);
    }
  }
  return matrix[a.length]![b.length]!;
};

const willOverwrite = (studentId: string | null) => {
  if (!studentId) return false;
  const student = students.value.find(s => s.id === studentId);
  if (!student) return false;
  if (submissionType.value === AssessmentType.INITIAL && student.initial_score !== null && student.initial_score !== undefined) return true;
  if (submissionType.value === AssessmentType.FINAL && student.final_score !== null && student.final_score !== undefined) return true;
  return false;
};

const getStudentName = (uuid: string | null) => {
  if (!uuid) return '';
  const s = students.value.find(s => s.id === uuid);
  return s ? `${s.last_name} ${s.first_name}` : 'Inconnu';
};

// --- PARSING JSON. ---
/**
 * Extrait les entrées d'un JSON d'export formulaire.
 * Supporte les structures : [[{...}]], [{...}], {...}
 */
const extractJsonEntries = (raw: unknown): JsonDictationEntry[] => {
  if (!raw) return [];
  if (Array.isArray(raw)) {
    const flat = raw.flat(Infinity);
    return flat.filter((e): e is JsonDictationEntry => typeof e === 'object' && e !== null);
  }
  if (typeof raw === 'object') return [raw as JsonDictationEntry];
  return [];
};

const getDictationText = (entry: JsonDictationEntry): string => {
  const rawText = (entry.rponse1 ?? entry.reponse1 ?? entry.response1 ?? '') as string;
  return rawText
    .replace(/ {6}/g, '\n\n') // 6 espaces => Double saut (Paragraphe).
    .replace(/ {3}/g, '\n')   // 3 espaces => Simple saut (Ligne).
    .trim();
};

const getLastName = (entry: JsonDictationEntry): string =>
  (entry.nomdefamille ?? entry.nom ?? '') as string;

const getFirstName = (entry: JsonDictationEntry): string =>
  (entry.prnom ?? '') as string;

const getEmail = (entry: JsonDictationEntry): string =>
  (entry.adressedecourriel ?? entry.email ?? '') as string;

// --- MATCHING. ---
const findMatchForFile = (fileItem: ParsedFile) => {
  const normFileName = normalizeText(fileItem.parsedName);
  const studentsInPromo = students.value.filter(s => s.promotion_id === selectedPromotion.value);

  let bestMatch: StudentWithScores | null = null;
  let minDistance = Infinity;

  for (const student of studentsInPromo) {
    const fullName1 = normalizeText(`${student.last_name} ${student.first_name}`);
    const fullName2 = normalizeText(`${student.first_name} ${student.last_name}`);

    if (normFileName === fullName1 || normFileName === fullName2) {
      fileItem.status = 'MATCHED';
      fileItem.studentId = student.id;
      return;
    }

    const dist = Math.min(levenshtein(normFileName, fullName1), levenshtein(normFileName, fullName2));
    if (dist < minDistance) {
      minDistance = dist;
      bestMatch = student;
    }
  }

  const maxAllowed = Math.floor(normFileName.length / 4);
  if (bestMatch && minDistance <= maxAllowed && minDistance > 0) {
    fileItem.status = 'SUGGESTED';
    fileItem.suggestedStudent = bestMatch;
  } else {
    fileItem.status = 'UNKNOWN';
  }
};

// --- TRAITEMENT DES FICHIERS. ---
const handlePromotionChange = () => {
  if (parsedFiles.value.length > 0) {
    if (confirm('Changer de promotion va réinitialiser les fichiers déjà chargés. Continuer ?')) {
      parsedFiles.value = [];
    }
  }
};

const triggerFileInput = () => {
  if (!canUpload.value) {
    ui.notify('Veuillez sélectionner une promotion et une dictée d\'abord.', 'error');
    return;
  }
  fileInputRef.value?.click();
};

const handleDrop = (e: DragEvent) => {
  dragOver.value = false;
  if (!canUpload.value) {
    ui.notify('Veuillez sélectionner une promotion et une dictée d\'abord.', 'error');
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
    const name = file.name.toLowerCase();
    if (name.endsWith('.txt')) {
      await processTxtFile(file);
    } else if (name.endsWith('.json')) {
      await processJsonFile(file);
    } else {
      ui.notify(`Format non supporté : ${file.name}. Utilisez .txt ou .json.`, 'error');
    }
  }
};

/** Traite un fichier .txt (un étudiant par fichier). */
const processTxtFile = async (file: File) => {
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
    suggestedStudent: null,
    sourceType: 'txt',
  };

  findMatchForFile(parsedFile);
  parsedFiles.value.push(parsedFile);
};

/** Traite un fichier .json (peut contenir plusieurs étudiants). */
const processJsonFile = async (file: File) => {
  let raw: unknown;
  try {
    raw = JSON.parse(await file.text());
  } catch {
    ui.notify(`Impossible de lire ${file.name} : JSON invalide.`, 'error');
    return;
  }

  const entries = extractJsonEntries(raw);
  if (entries.length === 0) {
    ui.notify(`Aucune entrée valide trouvée dans ${file.name}.`, 'error');
    return;
  }

  let added = 0;
  for (const entry of entries) {
    const lastName = getLastName(entry).trim();
    const firstName = getFirstName(entry).trim();
    const text = getDictationText(entry).trim();

    if (!lastName || !firstName || !text) continue;

    const parsedName = `${lastName} ${firstName}`;
    const parsedFile: ParsedFile = {
      id: Math.random().toString(36).substr(2, 9),
      file,
      content: text,
      originalName: file.name,
      parsedName,
      status: 'UNKNOWN',
      studentId: null,
      suggestedStudent: null,
      sourceType: 'json',
      emailHint: getEmail(entry) || undefined,
    };

    findMatchForFile(parsedFile);
    parsedFiles.value.push(parsedFile);
    added++;
  }

  if (added > 0) {
    ui.notify(`${added} étudiant(s) importé(s) depuis ${file.name}.`, 'success');
  } else {
    ui.notify(`Aucune dictée valide trouvée dans ${file.name}.`, 'error');
  }
};

// --- ACTIONS UTILISATEUR. ---
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
    promotion_id: selectedPromotion.value === '' ? undefined : selectedPromotion.value as number,
    group_id: undefined,
    tool_id: undefined,
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
    ui.notify('Étudiant créé et associé !');
    showCreateModal.value = false;
  } catch (err) {
    console.error('Erreur : ', err);
  }
};

// --- SOUMISSION. ---
const submitAll = async () => {
  if (!selectedDictation.value || !selectedPromotion.value) {
    ui.notify('Veuillez vérifier vos sélections.', 'error');
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
        student_uuid: f.studentId as string,
        dictation_id: Number(selectedDictation.value),
        assessment_type: submissionType.value,
        content_student: f.content,
      }));

      await api.createBulkSubmissions(payload);

      processedCount.value += chunk.length;
      importProgress.value = Math.round((processedCount.value / totalToProcess.value) * 100);
    }

    setTimeout(() => {
      ui.notify('Les dictées ont été importées.', 'success');
      setTimeout(() => router.push('/correction'), 1500);
    }, 500);
  } catch (error) {
    console.error("Erreur d'import :", error);
    ui.notify("Erreur lors de l'envoi en masse.", 'error');
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
/* ==========================================================================
   STYLE DE LA PAGE.
   ========================================================================== */
.form-card {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  border: 1px solid #e1e8ed;
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

/* ==========================================================================
   BADGES DE FORMAT.
   ========================================================================== */
.format-info-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.format-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.82rem;
  font-weight: 500;
}

.format-badge.txt-badge {
  background: #eaf7f0;
  color: #1a7f4e;
  border: 1px solid #a9e0c6;
}

.format-badge.json-badge {
  background: #eef2ff;
  color: #3730a3;
  border: 1px solid #c7d2fe;
}

/* ==========================================================================
   ZONE D'UPLOAD.
   ========================================================================== */
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

.upload-zone h3 {
  color: var(--primary);
  margin-bottom: 5px;
}

.upload-zone p {
  color: #7f8c8d;
  font-size: 0.9rem;
}

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

/* ==========================================================================
   LISTE DES FICHIERS.
   ========================================================================== */
.files-list {
  margin-top: 30px;
  background: #fafafa;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #eee;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 10px;
}

.list-title {
  margin: 0;
  color: var(--primary);
  font-size: 1.1rem;
}

.list-summary {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.summary-badge {
  font-size: 0.78rem;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
}

.summary-badge.matched {
  background: #e8f8f1;
  color: #1a7f4e;
}

.summary-badge.warned {
  background: #fdf5e0;
  color: #a0600a;
}

.summary-badge.unknown {
  background: #fdedec;
  color: #c0392b;
}

.summary-badge.ignored {
  background: #f4f4f4;
  color: #888;
}

/* ==========================================================================
   ITEM DE FICHIER.
   ========================================================================== */
.file-item {
  background: white;
  border: 1px solid #e1e8ed;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  transition: 0.2s;
  border-left: 5px solid #ccc;
  gap: 12px;
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
  gap: 4px;
  min-width: 0;
}

.file-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-type-icon {
  font-size: 0.65rem;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}

.file-type-icon.txt {
  background: #eaf7f0;
  color: #1a7f4e;
}

.file-type-icon.json {
  background: #eef2ff;
  color: #3730a3;
}

.file-name {
  font-weight: 600;
  color: var(--text);
}

.parsed-name {
  font-size: 0.85rem;
  color: #7f8c8d;
  font-style: italic;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-left: 2px;
}

.email-hint {
  font-size: 0.78rem;
  color: #95a5a6;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-left: 2px;
}

/* ==========================================================================
   ACTIONS.
   ========================================================================== */
.file-action {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.9rem;
  padding: 10px 14px;
  border-radius: 8px;
  flex-shrink: 0;
  max-width: 60%;
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

.action-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.match-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.overwrite-warning {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: #d35400;
  background: #fdfae7;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px dashed #fde68a;
}

.btn-group {
  display: flex;
  gap: 5px;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 0.85rem;
}

.btn-success {
  background: #2ecc71;
  color: white;
}

.btn-success:hover {
  background: #27ae60;
}

/* ==========================================================================
   ACTIONS GLOBALES.
   ========================================================================== */
.actions {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-top: 25px;
  border-top: 2px solid #f0f2f5;
  padding-top: 20px;
}

.warning-text {
  color: #e67e22;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-large {
  padding: 15px 30px;
  font-size: 1.1rem;
  width: 100%;
  box-shadow: 0 4px 6px rgba(26, 188, 156, 0.2);
  display: flex;
  justify-content: center;
}

.btn-large:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(26, 188, 156, 0.3);
}

/* ==========================================================================
   BARRE DE PROGRESSION.
   ========================================================================== */
.progress-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-text {
  font-weight: 600;
  color: var(--primary);
  font-size: 1rem;
  text-align: center;
}

.progress-bar {
  width: 100%;
  height: 24px;
  background-color: #edf2f7;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.progress-fill {
  height: 100%;
  background-color: var(--accent);
  background-image: linear-gradient(45deg,
      rgba(255, 255, 255, .15) 25%,
      transparent 25%,
      transparent 50%,
      rgba(255, 255, 255, .15) 50%,
      rgba(255, 255, 255, .15) 75%,
      transparent 75%,
      transparent);
  background-size: 1rem 1rem;
  border-radius: 12px;
  transition: width 0.4s ease-out;
  animation: progress-stripes 1s linear infinite;
  box-shadow: 0 2px 5px rgba(26, 188, 156, 0.4);
}

@keyframes progress-stripes {
  from {
    background-position: 1rem 0;
  }

  to {
    background-position: 0 0;
  }
}

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