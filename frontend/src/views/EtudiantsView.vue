<template>
  <div class="etudiants-view">
    <div class="header">
      <h1>Annuaire des Étudiants</h1>
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
        <tr v-for="student in students" :key="student.id">
          <td><strong>{{ student.nom }}, {{ student.prenom }}</strong></td>
          <td>{{ student.promo }}</td>
          <td>{{ student.groupe }}</td>
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
import { ref } from 'vue';

// --- DONNÉES DE DÉMO. ---
// Plus tard, faire un api.getStudents() ici.
const students = ref([
  { 
    id: 1, 
    nom: 'Dupont', 
    prenom: 'Jean', 
    promo: 'BUT1 - 2024/2025', 
    groupe: 'G1 (Auto)' 
  },
  { 
    id: 2, 
    nom: 'Martin', 
    prenom: 'Sophie', 
    promo: 'BUT1 - 2024/2025', 
    groupe: 'G2 (Jalons)' 
  }
]);

// --- ACTIONS. ---
const deleteStudent = (student: any) => {
  const isConfirmed = confirm(
    `⚠️ RGPD : Êtes-vous sûr de vouloir supprimer définitivement les données de ${student.prenom} ${student.nom} ?\n\nCette action est irréversible.`
  );

  if (isConfirmed) {
    students.value = students.value.filter(s => s.id !== student.id);
    
    // Plus tard : await api.deleteStudent(student.id);
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