<template>
  <div class="import-view">
    <div class="header">
      <button class="btn btn-outline" @click="router.push('/gestion')">← Retour à la gestion</button>
      <h1>📥 Importer une dictée étudiant</h1>
    </div>

    <div class="form-card">
      <div v-if="isLoading" class="loading-state">
        ⏳ Chargement des données...
      </div>
      
      <div v-else>
        <div class="grid-2">
          <div class="form-group">
            <label>1. Associer à un étudiant :</label>
            <select v-model="selectedStudent">
              <option value="">-- Sélectionner un étudiant --</option>
              <option v-for="student in students" :key="student.id" :value="student.id">
                {{ student.last_name }}, {{ student.first_name }} ({{ student.group }})
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>2. Associer à une dictée référente :</label>
            <select v-model="selectedDictation">
              <option value="">-- Aucune (Analyse libre) --</option>
              <option v-for="dict in dictations" :key="dict.id" :value="dict.id">
                {{ dict.title }}
              </option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>3. Type d'évaluation :</label>
          <select v-model="submissionType">
            <option value="INITIAL">Dictée Initiale</option>
            <option value="FINAL">Dictée Finale</option>
          </select>
        </div>

        <div class="form-group" style="margin-top: 25px;">
          <label>4. Source du texte :</label>
          
          <div class="upload-zone" @click="triggerFileInput">
            <i>📄</i>
            <h3>Cliquez ou glissez-déposez un fichier .txt ici</h3>
            <p v-if="fileName" style="color: var(--accent); font-weight: bold; margin-top: 10px;">
              Fichier chargé : {{ fileName }}
            </p>
            <input 
              type="file" 
              ref="fileInputRef" 
              style="display: none;" 
              accept=".txt"
              @change="handleFileUpload"
            >
          </div>
          
          <div class="separator"><span>OU</span></div>
          
          <textarea 
            rows="8" 
            v-model="studentText"
            placeholder="Saisissez ou collez le texte de l'étudiant ici..."
          ></textarea>
        </div>
        
        <div class="actions">
          <button 
            class="btn btn-primary btn-large" 
            @click="submitForm"
            :disabled="isSubmitting || !selectedStudent || !studentText"
          >
            {{ isSubmitting ? 'Analyse en cours...' : 'Lancer l\'analyse LanguageTool 🚀' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import type { Student, Dictation } from '@/types';

const router = useRouter();

// --- ÉTATS. ---
const isLoading = ref(true);
const isSubmitting = ref(false);

const students = ref<Student[]>([]);
const dictations = ref<Dictation[]>([]);

// Valeurs du formulaire.
const selectedStudent = ref('');
const selectedDictation = ref('');
const submissionType = ref('INITIAL');
const studentText = ref('');
const fileName = ref('');
const fileInputRef = ref<HTMLInputElement | null>(null);

// --- CHARGEMENT DES DONNÉES. ---
onMounted(async () => {
  try {
    const [studentsRes, dictationsRes] = await Promise.all([
      api.getStudents(),
      api.getDictations()
    ]);

    students.value = studentsRes.data.sort((a, b) => {
      const cmp = a.last_name.localeCompare(b.last_name, 'fr');
      if (cmp === 0) return a.first_name.localeCompare(b.first_name, 'fr');
      return cmp;
    });

    dictations.value = dictationsRes.data;
  } catch (error) {
    console.error("Erreur de chargement :", error);
    alert("Impossible de charger les listes (Étudiants ou Dictées).");
  } finally {
    isLoading.value = false;
  }
});

// --- GESTION DU FICHIER TXT. ---
const triggerFileInput = () => {
  if (fileInputRef.value) fileInputRef.value.click();
};

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];

  if (!file) return;
  if (file.type !== 'text/plain') {
    alert("Veuillez importer un fichier texte (.txt)");
    return;
  }

  fileName.value = file.name;
  const reader = new FileReader();
  
  reader.onload = (e) => {
    studentText.value = (e.target?.result as string) || '';
  };
  reader.onerror = () => alert("Erreur lors de la lecture du fichier.");
  
  reader.readAsText(file);
  target.value = '';
};

// --- SOUMISSION API. ---
const submitForm = async () => {
  if (!selectedStudent.value || !studentText.value.trim()) {
    alert("Veuillez sélectionner un étudiant et fournir un texte.");
    return;
  }

  isSubmitting.value = true;

  try {
    const payload = {
      student_uuid: selectedStudent.value,
      dictation_id: selectedDictation.value,
      assessment_type: submissionType.value,
      content_student: studentText.value
    };

    await api.createSubmission(payload);

    alert("Analyse de la dictée réussie !");
    router.push('/correction');
    
  } catch (error) {
    console.error("Erreur d'analyse :", error);
    alert("Erreur lors de l'enregistrement de la dictée. Vérifiez la console.");
  } finally {
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
  padding: 40px; 
  border-radius: 12px; 
  box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
  border: 1px solid #e1e8ed;
  max-width: 900px;
}

.grid-2 { 
    display: grid; 
    grid-template-columns: 1fr 1fr; 
    gap: 20px; 
}

.form-group { 
    margin-bottom: 15px; 
}
.form-group label { 
    display: block; 
    margin-bottom: 8px; 
    font-size: 1rem; 
    font-weight: 600; 
    color: var(--primary); 
}
.form-group select, .form-group textarea { 
  width: 100%; 
  padding: 12px; 
  border: 2px solid #ecf0f1; 
  border-radius: 8px; 
  font-family: inherit; 
  font-size: 1rem; 
  transition: border-color 0.2s;
}
.form-group select:focus, .form-group textarea:focus { 
    border-color: var(--accent); 
    outline: none; 
}

.upload-zone { 
  border: 2px dashed #bdc3c7; 
  border-radius: 8px; 
  padding: 40px 20px; 
  text-align: center; 
  background: #f8f9fa; 
  cursor: pointer; 
  transition: 0.2s; 
}
.upload-zone:hover { 
    border-color: var(--accent); 
    background: #f0f8ff; 
}
.upload-zone i { 
    font-size: 3rem; 
    color: #bdc3c7; 
    margin-bottom: 10px; 
    display: block; 
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

.separator { 
    text-align: center; 
    margin: 25px 0; 
    position: relative; 
}
.separator::before { 
    content: ""; 
    position: absolute; 
    left: 0; 
    top: 50%; 
    width: 100%; 
    height: 1px; 
    background: #e1e8ed; 
    z-index: 1; 
}
.separator span { 
    background: white; 
    padding: 0 15px; 
    color: #7f8c8d; 
    font-weight: bold; 
    position: relative; 
    z-index: 2; 
}

.actions { 
  display: flex; 
  justify-content: flex-end; 
  margin-top: 30px; 
}
.btn { 
  padding: 10px 20px; 
  border-radius: 6px; 
  cursor: pointer; 
  font-weight: 600; 
  transition: 0.2s; 
  border: none; 
}
.btn-large { 
  padding: 12px 24px; 
  font-size: 1.1rem; 
}
.btn-primary { 
  background: var(--accent); 
  color: white; 
}
.btn-primary:hover { 
  background: #12876f; 
  transform: translateY(-2px); 
}
.btn-outline { 
  background: transparent; 
  border: 1px solid #ccc; 
  color: var(--text); 
}
.btn-outline:hover { 
  background: #f8f9fa; 
  border-color: var(--primary); 
}
</style>