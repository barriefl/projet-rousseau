<template>
  <div class="import-view">
    <div class="header">
      <button class="btn btn-outline" @click="router.push('/gestion')">← Retour</button>
      <h1>📥 Importation de Dictées</h1>
    </div>

    <div class="form-card">
      <div v-if="isLoading" class="loading-state">
        ⏳ Chargement des étudiants et dictées...
      </div>
      
      <div v-else>
        <div class="global-settings grid-2">
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
              <option value="Initiale">Dictée Initiale</option>
              <option value="Finale">Dictée Finale</option>
            </select>
          </div>
        </div>

        <div class="form-group" style="margin-top: 25px;">
          <label>Fichiers étudiants (.txt) :</label>
          <div 
            class="upload-zone" 
            @click="triggerFileInput"
            @dragover.prevent="dragOver = true"
            @dragleave.prevent="dragOver = false"
            @drop.prevent="handleDrop"
            :class="{ 'drag-over': dragOver }"
          >
            <i>📄</i>
            <h3>Cliquez ou glissez-déposez vos fichiers .txt ici</h3>
            <p>Le format conseillé du nom de fichier est "NOM_Prenom.txt"</p>
            <input 
              type="file" 
              ref="fileInputRef" 
              style="display: none;" 
              accept=".txt"
              multiple
              @change="handleFileUpload"
            >
          </div>
        </div>

        <div v-if="parsedFiles.length > 0" class="files-list">
          <h3 class="list-title">Traitement des fichiers ({{ parsedFiles.length }})</h3>
          
          <div 
            v-for="fileItem in parsedFiles" 
            :key="fileItem.id" 
            class="file-item"
            :class="`status-${fileItem.status.toLowerCase()}`"
          >
            <div class="file-info">
              <span class="file-name">{{ fileItem.originalName }}</span>
              <span class="parsed-name" v-if="fileItem.parsedName">👉 Extrait : "{{ fileItem.parsedName }}"</span>
            </div>

            <div v-if="fileItem.status === 'MATCHED' || fileItem.status === 'CONFIRMED'" class="file-action success">
              ✅ Associé à <strong>{{ getStudentName(fileItem.studentId) }}</strong>
              <button class="btn btn-sm btn-outline" style="margin-left: auto;" @click="openCreateStudentForm(fileItem)">➕ Créer un autre étudiant</button>
            </div>

            <div v-if="fileItem.status === 'SUGGESTED'" class="file-action warning">
              ⚠️ Voulez-vous dire <strong>{{ fileItem.suggestedStudent?.last_name }} {{ fileItem.suggestedStudent?.first_name }}</strong> ?
              <div class="btn-group">
                <button class="btn btn-sm btn-success" @click="confirmSuggestion(fileItem)">Oui</button>
                <button class="btn btn-sm btn-outline" @click="rejectSuggestion(fileItem)">Non</button>
              </div>
            </div>

            <div v-if="fileItem.status === 'UNKNOWN'" class="file-action danger">
              ❌ Aucun étudiant trouvé.
              <div class="btn-group">
                <button class="btn btn-sm btn-primary" @click="openCreateStudentForm(fileItem)">➕ Créer étudiant</button>
                <button class="btn btn-sm btn-outline" @click="ignoreFile(fileItem)">Ignorer fichier</button>
              </div>
            </div>

            <div v-if="fileItem.status === 'IGNORED'" class="file-action text-muted">
              Fichier ignoré.
              <button class="btn btn-sm btn-outline" @click="reprocessFile(fileItem)" style="margin-left: 10px;">Annuler</button>
            </div>
          </div>
        </div>
        
        <div class="actions" v-if="parsedFiles.length > 0">
          <p v-if="!canSubmit && !isSubmitting" class="warning-text" style="margin-right: 15px;">
            ⚠️ Traitez les fichiers en jaune et rouge avant de valider.
          </p>
          <button 
            v-if="!isSubmitting"
            class="btn btn-primary btn-large" 
            @click="submitAll"
            :disabled="isSubmitting || !canSubmit"
          >
            {{ isSubmitting ? 'Importation en cours...' : `Envoyer ${filesReadyToSubmit} dictée(s) 🚀` }}
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

  <div class="modal-overlay" v-if="showCreateModal" @click.self="closeCreateModal">
    <div class="modal large-modal">
      <h2 style="color: var(--primary); margin-bottom: 20px;">Créer un nouvel étudiant</h2>

      <div class="form-grid">
        <div class="form-group">
          <label>Nom *</label>
          <input type="text" v-model="newStudentForm.last_name" required>
        </div>
        <div class="form-group">
          <label>Prénom *</label>
          <input type="text" v-model="newStudentForm.first_name" required>
        </div>
        <div class="form-group">
          <label>Promo</label>
          <input type="text" v-model="newStudentForm.promo">
        </div>
        <div class="form-group">
          <label>Groupe</label>
          <select v-model="newStudentForm.group">
            <option value="">-- Sélectionner --</option>
            <option value="G0">G0</option>
            <option value="G1">G1</option>
            <option value="G2">G2</option>
            <option value="G3">G3</option>
            <option value="G4">G4</option>
            <option value="G5">G5</option>
          </select>
        </div>
        <div class="form-group">
          <label>Niveau d'appétence (1-4)</label>
          <input type="number" v-model="newStudentForm.appetence_level" min="1" max="4">
        </div>
        <div class="form-group">
          <label>A une bibliothèque ?</label>
          <select v-model="newStudentForm.has_library">
            <option value="">-- Sélectionner --</option>
            <option value="Oui">Oui</option>
            <option value="Non">Non</option>
          </select>
        </div>
        <div class="form-group">
          <label>Support de lecture</label>
          <select v-model="newStudentForm.reading_support">
            <option value="">-- Sélectionner --</option>
            <option value="Ecran">Ecran</option>
            <option value="Papier">Papier</option>
            <option value="Beaucoup écran - un peu papier">Beaucoup écran - un peu papier</option>
            <option value="Beaucoup papier - un peu écran">Beaucoup papier - un peu écran</option>
          </select>
        </div>
        <div class="form-group" style="grid-column: span 2;">
          <label>Œuvres lues</label>
          <div class="checkbox-grid">
            <label v-for="work in readingWorksOptions" :key="work" class="checkbox-label">
              <input type="checkbox" :value="work" v-model="selectedReadingWorks">
              {{ work }}
            </label>
          </div>
        </div>
        <div class="form-group" style="grid-column: span 2;">
          <label>Motif de lecture</label>
          <div class="checkbox-grid">
            <label v-for="motive in motiveOptions" :key="motive" class="checkbox-label">
              <input type="checkbox" :value="motive" v-model="selectedMotives">
              {{ motive }}
            </label>
          </div>
        </div>
        <div class="form-group" style="grid-column: span 2;">
          <label>Niveau déclaré</label>
          <div class="radio-grid">
            <label v-for="level in declaredLevelOptions" :key="level" class="radio-label">
              <input type="radio" :value="level" v-model="newStudentForm.declared_level">
              {{ level }}
            </label>
          </div>
        </div>
        <div class="form-group">
          <label>Diplôme Parent 1</label>
          <select v-model="newStudentForm.parent_1_degree">
            <option value="">-- Sélectionner --</option>
            <option value="Aucun">Aucun</option>
            <option value="CAP BEP BP">CAP BEP BP</option>
            <option value="Bac">Bac</option>
            <option value="Bac+2 BTS Licence">Bac+2 BTS Licence</option>
            <option value="Bac+4 Master Doctorat">Bac+4 Master Doctorat</option>
            <option value="Autres">Autres</option>
            <option value="Je ne sais pas">Je ne sais pas</option>
          </select>
        </div>
        <div class="form-group">
          <label>CSP Parent 1</label>
          <select v-model="newStudentForm.parent_1_csp">
            <option value="">-- Sélectionner --</option>
            <option value="Agriculteurs exploitants">Agriculteurs exploitants</option>
            <option value="Artisans, commerçants, chefs entreprise">Artisans, commerçants, chefs entreprise</option>
            <option value="Cadres, professions intellectuelles sup.">Cadres, professions intellectuelles sup.</option>
            <option value="Employés / ouvriers">Employés / ouvriers</option>
            <option value="Retraités">Retraités</option>
            <option value="Autres sans activité professionnelle">Autres sans activité professionnelle</option>
            <option value="Je ne sais pas">Je ne sais pas</option>
          </select>
        </div>
        <div class="form-group">
          <label>Diplôme Parent 2</label>
          <select v-model="newStudentForm.parent_2_degree">
            <option value="">-- Sélectionner --</option>
            <option value="Aucun">Aucun</option>
            <option value="CAP BEP BP">CAP BEP BP</option>
            <option value="Bac">Bac</option>
            <option value="Bac+2 BTS Licence">Bac+2 BTS Licence</option>
            <option value="Bac+4 Master Doctorat">Bac+4 Master Doctorat</option>
            <option value="Autres">Autres</option>
            <option value="Je ne sais pas">Je ne sais pas</option>
          </select>
        </div>
        <div class="form-group">
          <label>CSP Parent 2</label>
          <select v-model="newStudentForm.parent_2_csp">
            <option value="">-- Sélectionner --</option>
            <option value="Agriculteurs exploitants">Agriculteurs exploitants</option>
            <option value="Artisans, commerçants, chefs entreprise">Artisans, commerçants, chefs entreprise</option>
            <option value="Cadres, professions intellectuelles sup.">Cadres, professions intellectuelles sup.</option>
            <option value="Employés / ouvriers">Employés / ouvriers</option>
            <option value="Retraités">Retraités</option>
            <option value="Autres sans activité professionnelle">Autres sans activité professionnelle</option>
            <option value="Je ne sais pas">Je ne sais pas</option>
          </select>
        </div>
      </div>

      <div class="modal-actions" style="margin-top: 25px;">
        <button class="btn btn-outline" @click="closeCreateModal">Annuler</button>
        <button class="btn btn-primary" @click="confirmCreateStudent" :disabled="!newStudentForm.first_name || !newStudentForm.last_name">
          Enregistrer et associer
        </button>
      </div>
    </div>
  </div>

  <div class="toast-notification" :class="notification.type" v-if="notification.show">
    <span class="toast-icon">{{ notification.type === 'success' ? '✅' : '❌' }}</span>
    <span class="toast-message">{{ notification.message }}</span>
  </div>

  <div class="modal-overlay" v-if="confirmDialog.show" @click.self="resolveConfirm(false)">
    <div class="modal confirm-modal">
      <h3 style="color: var(--danger); margin-top: 0;">⚠️ Confirmation requise</h3>
      <p style="margin: 20px 0; line-height: 1.5; color: var(--text); white-space: pre-wrap;">{{ confirmDialog.message }}</p>
      <div class="modal-actions">
        <button class="btn btn-outline" @click="resolveConfirm(false)">Annuler</button>
        <button class="btn btn-danger" @click="resolveConfirm(true)">Confirmer</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import type { Student, Dictation } from '@/types';

const router = useRouter();

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

// Valeurs globales du formulaire.
const selectedDictation = ref('');
const submissionType = ref('Initiale');

// Liste des fichiers déposés.
const parsedFiles = ref<ParsedFile[]>([]);
const fileInputRef = ref<HTMLInputElement | null>(null);

const importProgress = ref(0);
const processedCount = ref(0);
const totalToProcess = ref(0);

// États pour le formulaire.
const showCreateModal = ref(false);
const editingFileItem = ref<ParsedFile | null>(null);

const newStudentForm = ref({
  first_name: '', last_name: '', promo: '', group: '', appetence_level: '',
  has_library: '', reading_support: '', reading_works: '', motive: '',
  parent_1_degree: '', parent_1_csp: '', parent_2_degree: '', parent_2_csp: '', declared_level: ''
});

const readingWorksOptions = [
  "Romans / écrits littéraires", "Mangas / BD", "Livres de jeux, devinettes et énigmes",
  "Textes religieux et spirituels", "Presse / revues / articles", "Poésies, poèmes",
  "Réseaux sociaux", "Cours / livres éducatifs",
  "Ecrits publicitaires et marketing / modes d'emploi", "Autres livres"
];

const motiveOptions = [
  "Apprentissage", "Distraction", "Information"
];

const declaredLevelOptions = [
  "Mauvais", "2", "3", "4", "5", "Excellent"
];

const selectedReadingWorks = ref<string[]>([]);
const selectedMotives = ref<string[]>([]);

// --- CHARGEMENT. ---
onMounted(async () => {
  try {
    const [studentsRes, dictationsRes] = await Promise.all([
      api.getStudents(),
      api.getDictations()
    ]);
    students.value = studentsRes.data;
    dictations.value = dictationsRes.data;
  } catch (error) {
    console.error("Erreur de chargement :", error);
  } finally {
    isLoading.value = false;
  }
});

// --- UTILITAIRES (NORMALISATION ET LEVENSHTEIN). ---
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
const triggerFileInput = () => { if (fileInputRef.value) fileInputRef.value.click(); };

const handleDrop = (e: DragEvent) => {
  dragOver.value = false;
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
    const cleanName = file.name.replace('.txt', '').replace(/[-_]/g, ' ').trim();
    
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
  
  let bestMatch: Student | null = null;
  let minDistance = Infinity;

  for (const student of students.value) {
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

const openCreateStudentForm = (fileItem: ParsedFile) => {
  editingFileItem.value = fileItem;
  const parts = fileItem.parsedName.split(' ');
  
  newStudentForm.value = {
    first_name: parts.slice(1).join(' ') || '',
    last_name: parts[0]?.toUpperCase() || '',
    promo: '', group: '', appetence_level: '', has_library: '',
    reading_support: '', reading_works: '', motive: '',
    parent_1_degree: '', parent_1_csp: '', parent_2_degree: '', parent_2_csp: '', declared_level: ''
  };

  selectedReadingWorks.value = [];
  selectedMotives.value = [];
  
  showCreateModal.value = true;
};

const closeCreateModal = () => {
  showCreateModal.value = false;
  editingFileItem.value = null;
};

const confirmCreateStudent = async () => {
  if (!editingFileItem.value || !newStudentForm.value.first_name || !newStudentForm.value.last_name) return;

  newStudentForm.value.reading_works = selectedReadingWorks.value.length > 0 
    ? selectedReadingWorks.value.join(';') 
    : '';

  newStudentForm.value.motive = selectedMotives.value.length > 0 
    ? selectedMotives.value.join(';') 
    : '';

  try {
    const dataToSend = Object.fromEntries(
      Object.entries(newStudentForm.value).map(([k, v]) => {
        if (v === '') return [k, null];
        if (k === 'appetence_level' && v !== null) return [k, String(v)];
        return [k, v];
      })
    );

    const newStudent = await api.createStudent(dataToSend as any);
    
    students.value.push(newStudent);
    
    editingFileItem.value.status = 'CONFIRMED';
    editingFileItem.value.studentId = newStudent.id;

    closeCreateModal();
  } catch (error) {
    console.error("Erreur de création :", error);
    showNotification("Impossible de créer l'étudiant.", "error");
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

// --- VALIDATION FINALE EN LOTS (CHUNKS). ---
const submitAll = async () => {
  if (!selectedDictation.value) {
    if (typeof showNotification === 'function') {
      showNotification("⚠️ Veuillez sélectionner une dictée référente avant de lancer l'importation.", "error");
    } else {
      alert("⚠️ Veuillez sélectionner une dictée référente avant de lancer l'importation.");
    }
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
        content_student: f.content
      }));

      await api.createBulkSubmissions(payload);

      processedCount.value += chunk.length;
      importProgress.value = Math.round((processedCount.value / totalToProcess.value) * 100);
    }

    setTimeout(() => {
      showNotification("Succès ! Les dictées ont été importées.", "success");
      setTimeout(() => {
        router.push('/correction');
      }, 1500);
    }, 500);
    
  } catch (error) {
    console.error("Erreur d'import :", error);
    showNotification("Une erreur est survenue lors de l'envoi en masse.", "error");
    isSubmitting.value = false;
  }
};

// --- NOTIFICATIONS & CONFIRMATIONS CUSTOM. ---
const notification = ref({ show: false, message: '', type: 'success' });
const showNotification = (msg: string, type: 'success' | 'error' = 'success') => {
  notification.value = { show: true, message: msg, type };
  setTimeout(() => { notification.value.show = false; }, 4000);
};

const confirmDialog = ref({ show: false, message: '', resolve: (val: boolean) => {} });
const askConfirm = (msg: string): Promise<boolean> => {
  return new Promise((resolve) => {
    confirmDialog.value = { show: true, message: msg, resolve };
  });
};
const resolveConfirm = (val: boolean) => {
  confirmDialog.value.show = false;
  confirmDialog.value.resolve(val);
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
  box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
  border: 1px solid #e1e8ed; 
}

.grid-2 { 
  display: grid; 
  grid-template-columns: 1fr 1fr; 
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

/* Drag & Drop Zone. */
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

/* Liste des fichiers. */
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
  box-shadow: 0 2px 5px rgba(0,0,0,0.05); 
}

/* Couleurs d'état (Bordure gauche). */
.file-item.status-matched, .file-item.status-confirmed { 
  border-left-color: #2ecc71; 
}
.file-item.status-suggested { 
  border-left-color: #f1c40f; 
}
.file-item.status-unknown { 
  border-left-color: #e74c3c; 
}
.file-item.status-ignored { 
  border-left-color: #95a5a6; opacity: 0.6; 
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

/* Boutons. */
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

/* --- Modale Étudiant. --- */
.modal-overlay { 
  position: fixed; 
  top: 0; left: 0; right: 0; bottom: 0; 
  background: rgba(0,0,0,0.6); 
  z-index: 1000; 
  display: flex; 
  justify-content: center; 
  align-items: center; 
}
.modal { 
  background: white; 
  padding: 30px; 
  border-radius: 8px; 
  width: 500px; 
  max-width: 90%; 
  max-height: 90vh; 
  overflow-y: auto; 
  box-shadow: 0 10px 25px rgba(0,0,0,0.2); 
}
.large-modal {
  width: 700px;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}
.form-group input[type="text"], 
.form-group input[type="number"], 
.form-group select { 
  width: 100%; 
  padding: 8px 12px; 
  border: 1px solid #ccc; 
  border-radius: 4px; 
  font-family: inherit; 
  box-sizing: border-box;
  transition: 0.2s border-color;
}

.form-group input[type="text"]:focus,
.form-group input[type="number"]:focus,
.form-group select:focus {
  border-color: var(--accent);
  outline: none;
}
.form-group select {
  cursor: pointer;
  background-color: white;
}
.modal-actions { 
  display: flex; 
  justify-content: flex-end; 
  gap: 10px; 
}
.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
  margin-top: 10px;
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  border: 1px solid #e1e8ed;
}
.radio-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-top: 10px;
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  border: 1px solid #e1e8ed;
}
.checkbox-label, .radio-label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-weight: 500;
  font-size: 0.9rem;
  color: var(--text);
  cursor: pointer;
  line-height: 1.3;
}
.checkbox-label input[type="checkbox"],
.radio-label input[type="radio"] {
  width: 16px;
  height: 16px;
  margin-top: 2px;
  cursor: pointer;
  accent-color: var(--accent);
}

/* --- NOTIFICATIONS & CONFIRMATIONS. --- */
.toast-notification {
  position: fixed; 
  top: 20px; 
  right: 20px; 
  padding: 15px 25px; 
  border-radius: 8px;
  display: flex; 
  align-items: center; 
  gap: 12px; 
  font-weight: 500;
  box-shadow: 0 5px 15px rgba(0,0,0,0.2); 
  z-index: 9999;
  animation: slideIn 0.3s ease-out;
}
.toast-notification.success { 
  background: #d4edda; 
  color: #155724; 
  border-left: 5px solid #28a745; 
}
.toast-notification.error { 
  background: #f8d7da; 
  color: #721c24; 
  border-left: 5px solid #dc3545; 
}
.toast-icon { 
  font-size: 1.2rem; 
}

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.confirm-modal { 
  width: 400px; 
  text-align: center; 
}
.btn-danger { 
  background: var(--danger); 
  color: white; 
  border: none; 
  padding: 8px 16px; 
  border-radius: 4px; 
  cursor: pointer; 
  font-weight: bold; 
  transition: 0.2s;
}
.btn-danger:hover { 
  background: #c0392b; 
  transform: scale(1.05); 
}
.confirm-modal .modal-actions {
  justify-content: center;
  margin-top: 30px;
}

/* Barre de progression. */
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
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
}
.progress-fill {
  height: 100%;
  background-color: var(--accent);
  transition: width 0.4s ease-out;
}
</style>