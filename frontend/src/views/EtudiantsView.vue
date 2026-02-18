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
          <th style="text-align: right;">Gestion RGPD</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="4" style="text-align: center; padding:30px;">
            ⏳ Chargement des étudiants en cours...
          </td>
        </tr>

        <tr v-for="student in students" :key="student.id">
          <td><strong>{{ student.last_name }}, {{ student.first_name }}</strong></td>
          <td>{{ student.promo || 'Non renseignée'}}</td>
          <td>{{ student.group || 'Non assigné' }}</td>
          <td style="text-align: right;">
            <button class="btn-danger" @click="deleteStudent(student)">
              Supprimer les données
            </button>
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
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import api from '@/services/api';
import type { Student } from '@/types';

const students = ref<Student[]>([]);
const loading = ref(true);

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
</style>