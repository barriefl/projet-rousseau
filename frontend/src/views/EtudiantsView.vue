<template>
  <div class="etudiants-view">
    <div class="header">
      <h1>Liste des Étudiants</h1>
    </div>

    <table>
      <thead>
        <tr>
          <th>Nom de l'étudiant</th>
          <th>Promotion</th>
          <th>Groupe Assigné</th>
          <th style="text-align: right;">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="4" style="text-align: center; padding:30px;">
            ⏳ Chargement des étudiants en cours...
          </td>
        </tr>

        <tr v-for="student in students" :key="student.id">
          <td><strong>{{ student.last_name }} {{ student.first_name }}</strong></td>
          <td>{{ student.promo || 'Non renseignée'}}</td>
          <td>{{ student.group || 'Non assigné' }}</td>
          <td style="text-align: right;">
            <div class="action-buttons">
              <button class="btn-primary btn-sm" @click="openEditModal(student)">
                ✏️ Modifier
              </button>
              <button class="btn-danger btn-sm" @click="deleteStudent(student)">
                🗑️ Supprimer
              </button>
            </div>
          </td>
        </tr>

        <tr v-if="students.length === 0">
          <td colspan="4" style="text-align: center; color: #7f8c8d; padding: 30px;">
            Aucun étudiant dans la base de données.
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="modal-overlay" v-if="showEditModal" @click.self="closeEditModal">
      <div class="modal large-modal">
        <h2 style="color: var(--primary); margin-bottom: 20px;">Modifier l'étudiant</h2>

        <div class="form-grid">
          <div class="form-group">
            <label>Nom *</label>
            <input type="text" v-model="editStudentForm.last_name" required>
          </div>
          <div class="form-group">
            <label>Prénom *</label>
            <input type="text" v-model="editStudentForm.first_name" required>
          </div>
          <div class="form-group">
            <label>Promo</label>
            <input type="text" v-model="editStudentForm.promo">
          </div>
          <div class="form-group">
            <label>Groupe</label>
            <select v-model="editStudentForm.group">
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
            <input type="number" v-model="editStudentForm.appetence_level" min="1" max="4">
          </div>
          <div class="form-group">
            <label>A une bibliothèque ?</label>
            <select v-model="editStudentForm.has_library">
              <option value="">-- Sélectionner --</option>
              <option value="Oui">Oui</option>
              <option value="Non">Non</option>
            </select>
          </div>
          <div class="form-group">
            <label>Support de lecture</label>
            <select v-model="editStudentForm.reading_support">
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
                <input type="radio" :value="level" v-model="editStudentForm.declared_level">
                {{ level }}
              </label>
            </div>
          </div>
          <div class="form-group">
            <label>Diplôme Parent 1</label>
            <select v-model="editStudentForm.parent_1_degree">
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
            <select v-model="editStudentForm.parent_1_csp">
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
            <select v-model="editStudentForm.parent_2_degree">
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
            <select v-model="editStudentForm.parent_2_csp">
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
          <button class="btn btn-outline" @click="closeEditModal">Annuler</button>
          <button class="btn btn-primary" @click="confirmEditStudent" :disabled="!editStudentForm.first_name || !editStudentForm.last_name">
            Sauvegarder les modifications
          </button>
        </div>
      </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import api from '@/services/api';
import type { Student } from '@/types';

const students = ref<Student[]>([]);
const loading = ref(true);

// --- LOGIQUE D'ÉDITION. ---
const showEditModal = ref(false);
const editingStudentId = ref<string | null>(null);

const editStudentForm = ref({
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

onMounted(async () => {
  try {
    const response = await api.getStudents();
    
    const sortedStudents = response.data.sort((a, b) => {
      const compareNom = a.last_name.localeCompare(b.last_name, 'fr');
      
      if (compareNom === 0) {
        return a.first_name.localeCompare(b.first_name, 'fr');
      }
      return compareNom;
    });

    students.value = sortedStudents;
    
  } catch (error) {
    console.error("Erreur API :", error);
    alert("Impossible de charger la liste des étudiants.");
  } finally {
    loading.value = false;
  }
});

const deleteStudent = async (student: Student) => {
  const isConfirmed = confirm(
    `⚠️ RGPD : Êtes-vous sûr de vouloir supprimer définitivement les données de ${student.first_name} ${student.last_name} ?\n\nCette action est irréversible.`
  );

  if (isConfirmed) {
    try {
      await api.deleteStudent(student.id);

      students.value = students.value.filter(s => s.id !== student.id);
      
      alert(`Les données de ${student.first_name} ${student.last_name} ont été supprimées avec succès.`);
      
    } catch (error) {
      console.error("Erreur lors de la suppression :", error);
      alert("Une erreur est survenue lors de la suppression de l'étudiant. Vérifiez que la route DELETE existe bien côté serveur.");
    }
  }
};

const openEditModal = (student: Student) => {
  editingStudentId.value = student.id;
  
  editStudentForm.value = {
    first_name: student.first_name || '',
    last_name: student.last_name || '',
    promo: student.promo || '',
    group: student.group || '',
    appetence_level: student.appetence_level || '',
    has_library: student.has_library || '',
    reading_support: student.reading_support || '',
    reading_works: student.reading_works || '',
    motive: student.motive || '',
    declared_level: student.declared_level || '',
    parent_1_degree: student.parent_1_degree || '',
    parent_1_csp: student.parent_1_csp || '',
    parent_2_degree: student.parent_2_degree || '',
    parent_2_csp: student.parent_2_csp || ''
  };

  selectedReadingWorks.value = student.reading_works 
    ? student.reading_works.split(';').map(s => s.trim()).filter(Boolean)
    : [];
    
  selectedMotives.value = student.motive 
    ? student.motive.split(';').map(s => s.trim()).filter(Boolean)
    : [];
  
  showEditModal.value = true;
};

const closeEditModal = () => {
  showEditModal.value = false;
  editingStudentId.value = null;
};

const confirmEditStudent = async () => {
  if (!editingStudentId.value || !editStudentForm.value.first_name || !editStudentForm.value.last_name) return;

  editStudentForm.value.reading_works = selectedReadingWorks.value.length > 0 
    ? selectedReadingWorks.value.join(';') 
    : '';

  editStudentForm.value.motive = selectedMotives.value.length > 0 
    ? selectedMotives.value.join(';') 
    : '';

  try {
    const dataToSend = Object.fromEntries(
      Object.entries(editStudentForm.value).map(([k, v]) => {
        if (v === '') return [k, null]; 
        if (k === 'appetence_level' && v !== null) return [k, String(v)]; 
        return [k, v];
      })
    );

    const updatedStudent = await api.updateStudent(editingStudentId.value, dataToSend as any);
    
    const index = students.value.findIndex(s => s.id === editingStudentId.value);
    if (index !== -1) {
      students.value[index] = updatedStudent;
    }

    alert("✅ Informations de l'étudiant mises à jour !");
    closeEditModal();
  } catch (error) {
    console.error("Erreur de mise à jour :", error);
    alert("Impossible de modifier l'étudiant. Avez-vous créé la route backend ?");
  }
};
</script>

<style scoped>
.header { 
    margin-bottom: 20px; 
}
.header h1 { 
    font-size: 1.6rem; 
    color: var(--primary); 
}

/* Style du Tableau. */
table { 
  width: 100%; 
  border-collapse: collapse; 
  background: white; 
  border-radius: 8px; 
  overflow: hidden; 
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
th, td { 
  padding: 12px 15px; 
  text-align: left; 
  border-bottom: 1px solid #eee; 
  font-size: 0.95rem; 
  vertical-align: middle;
}
th { 
    background-color: var(--light); 
    color: var(--secondary); 
    font-weight: 600;
}
tr:hover { 
    background-color: #fcfcfc; 
}

/* Bouton RGPD. */
.btn-danger { 
  background: var(--danger); 
  color: white; 
  border: none; 
  padding: 6px 12px; 
  border-radius: 4px; 
  cursor: pointer; 
  font-size: 0.85rem;
  transition: 0.2s;
  font-weight: 500;
}
.btn-danger:hover { 
  background: #c0392b;
  transform: scale(1.05);
}

/* Alignement des boutons du tableau. */
.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: 0.2s;
  font-weight: 500;
  padding: 6px 12px;
}
.btn-primary:hover:not(:disabled) {
  background: #12876f;
  transform: scale(1.05);
}
.btn-sm {
  padding: 6px 12px;
  font-size: 0.85rem;
}
.btn-outline {
  background: transparent;
  border: 1px solid #ccc;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}
.btn-outline:hover {
  background: #eee;
}

/* Modale. */
.modal-overlay { 
  position: fixed; 
  top: 0; 
  left: 0; 
  right: 0; 
  bottom: 0; 
  background: rgba(0,0,0,0.6); 
  z-index: 1000; 
  display: flex; justify-content: center; align-items: center; 
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
.form-group label { 
  display: block; 
  margin-bottom: 5px; 
  font-weight: 500; 
  font-size: 0.9rem; 
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
.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-weight: 500;
  font-size: 0.9rem;
  color: var(--text);
  cursor: pointer;
  line-height: 1.3;
}
.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  margin-top: 2px;
  cursor: pointer;
  accent-color: var(--accent);
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
.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 0.9rem;
  color: var(--text);
  cursor: pointer;
}
.radio-label input[type="radio"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--accent);
  margin: 0;
}
</style>