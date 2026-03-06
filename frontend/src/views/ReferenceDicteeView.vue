<template>
  <div class="reference-view">
    <div class="page-header">
      <button class="btn btn-outline" @click="router.push('/gestion')">← Retour</button>
      <h1>Définir une dictée référente</h1>
    </div>

    <div class="form-card warning-border">
      <p class="intro-text">
        Ce texte servira de base parfaite (zéro faute) pour l'algorithme de comparaison. É.M.I.L.E. l'utilisera pour
        détecter les oublis ou les ajouts de mots par les étudiants.
      </p>

      <div class="form-group">
        <label>Titre de la dictée référente :</label>
        <input type="text" v-model="dictationTitle" placeholder="Ex: Dictée Initiale (Septembre 2024)">
      </div>

      <div class="form-group" style="margin-top: 25px;">
        <label>Le texte de référence parfait :</label>

        <div class="upload-zone" @click="triggerFileInput">
          <i>📄</i>
          <h3>Importez le fichier du professeur (.txt)</h3>
          <p v-if="fileName" style="color: var(--warning); font-weight: bold; margin-top: 10px;">
            Fichier chargé : {{ fileName }}
          </p>
          <input type="file" ref="fileInputRef" style="display: none;" accept=".txt" @change="handleFileUpload">
        </div>

        <div class="separator"><span>OU</span></div>

        <textarea rows="10" v-model="dictationText"
          placeholder="Saisissez la correction parfaite de la dictée ici..."></textarea>
      </div>

      <div class="actions">
        <button class="btn btn-warning btn-large" @click="submitDictation" :disabled="isSubmitting">
          {{ isSubmitting ? 'Enregistrement...' : 'Sauvegarder la référence ⭐' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import { useUiStore } from '@/stores/ui';

const ui = useUiStore();

const router = useRouter();

// --- ÉTATS. ---
const dictationTitle = ref('');
const dictationText = ref('');
const fileName = ref('');
const fileInputRef = ref<HTMLInputElement | null>(null);
const isSubmitting = ref(false);

// --- GESTION DU FICHIER (FileReader). ---
const triggerFileInput = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
};

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];

  if (!file) return;

  if (file.type !== 'text/plain') {
    ui.notify("Veuillez importer un fichier texte (.txt).", "error");
    return;
  }

  fileName.value = file.name;

  const reader = new FileReader();
  reader.onload = (e) => {
    dictationText.value = (e.target?.result as string) || '';
  };
  reader.onerror = () => {
    ui.notify("Erreur lors de la lecture du fichier.", "error");
  };

  reader.readAsText(file);

  target.value = '';
};

// --- SOUMISSION À L'API. ---
const submitDictation = async () => {
  if (!dictationTitle.value.trim() || !dictationText.value.trim()) {
    ui.notify("Veuillez renseigner un titre et un texte.", "error");
    return;
  }

  isSubmitting.value = true;

  try {
    await api.createDictation({
      title: dictationTitle.value,
      content_reference: dictationText.value
    });

    ui.notify("Dictée de référence enregistrée.", "success");
    setTimeout(() => {
      router.push('/gestion');
    }, 1500);

  } catch (error) {
    console.error("Erreur lors de la création de la dictée :", error);
    ui.notify("Erreur lors de l'enregistrement de la dictée.", "error");
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
/* ==========================================================================
   STYLE PAGE.
   ========================================================================== */
.intro-text {
  font-size: 1rem;
  color: #555;
  margin-bottom: 25px;
  line-height: 1.5;
  background: #fffbe6;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid var(--warning);
}

.form-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  border: 1px solid #e1e8ed;
  max-width: 99%;
}

.warning-border {
  border-top: 5px solid var(--warning);
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 1rem;
  font-weight: 600;
  color: var(--primary);
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #ecf0f1;
  border-radius: 8px;
  font-family: inherit;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  border-color: var(--warning);
  outline: none;
}

/* ==========================================================================
   UPLOAD ZONE.
   ========================================================================== */
.upload-zone {
  border: 2px dashed #bdc3c7;
  border-radius: 8px;
  padding: 30px;
  text-align: center;
  background: #f8f9fa;
  cursor: pointer;
  transition: 0.2s;
}

.upload-zone:hover {
  border-color: var(--warning);
  background: #fffdf5;
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
  margin: 0;
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

/* ==========================================================================
   BOUTONS.
   ========================================================================== */
.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 30px;
}

.btn-large {
  padding: 12px 24px;
  font-size: 1.1rem;
}

.btn-warning {
  background: var(--warning);
  color: white;
}

.btn-warning:hover {
  background: #d68910;
  transform: translateY(-2px);
}
</style>