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
          <th>Groupe</th>
          <th style="text-align: right">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="4" style="text-align: center; padding: 30px">
            <AppLoading message="Chargement des catégories et des règles..." />
          </td>
        </tr>

        <tr v-for="student in students" :key="student.id">
          <td>
            <strong>{{ student.last_name }} {{ student.first_name }}</strong>
          </td>
          <td>{{ student.promotion_name || 'Non renseignée' }}</td>
          <td>{{ student.group_name || 'Non assigné' }}</td>
          <td style="text-align: right">
            <div class="action-buttons">
              <button class="btn btn-primary btn-sm" @click="openEditModal(student)">
                <Pencil :size="16" />
                <span>Modifier</span>
              </button>
              <button class="btn btn-danger btn-sm" @click="deleteStudent(student)">
                <Trash2 :size="16" />
                <span>Supprimer</span>
              </button>
            </div>
          </td>
        </tr>

        <tr v-if="students.length === 0 && !loading">
          <AppEmptyState title="Aucun étudiant" message="Aucun étudiant dans la base de données." />
        </tr>
      </tbody>
    </table>
  </div>

  <div class="page-container">
    <StudentFormModal
      :show="showEditModal"
      :student-data="selectedStudent"
      :promotions="promotions"
      :groups="groups"
      :is-edit="true"
      @close="showEditModal = false"
      @save="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import type { Student, Promotion, Group, StudentUpdatePayload } from '@/types'
import AppLoading from '@/components/common/AppLoading.vue';
import AppEmptyState from '@/components/common/AppEmptyState.vue';
import { Pencil, Trash2 } from 'lucide-vue-next';
import { useUiStore } from '@/stores/ui';
import StudentFormModal from '@/components/students/StudentFormModal.vue';

const ui = useUiStore();

const students = ref<Student[]>([])
const promotions = ref<Promotion[]>([])
const groups = ref<Group[]>([])
const loading = ref(true)

const loadData = async () => {
  try {
    const res = await api.getStudents();
    students.value = res;
  } catch (e) {
    console.error(e)
    ui.notify("Erreur lors du chargement des données.", "error");
  }
};

// --- LOGIQUE D'ÉDITION. ---
const showEditModal = ref(false)
const selectedStudent = ref<Student | null>(null);

onMounted(async () => {
  try {
    const [studentsRes, promoRes, groupsRes] = await Promise.all([
      api.getStudents(),
      api.getPromotions(),
      api.getGroups(),
    ])

    const studentData = studentsRes as Student[]
    promotions.value = promoRes as Promotion[]
    groups.value = groupsRes as Group[]

    const sortedStudents = studentData.sort((a, b) => {
      const compareNom = a.last_name.localeCompare(b.last_name, 'fr')
      if (compareNom === 0) {
        return a.first_name.localeCompare(b.first_name, 'fr')
      }
      return compareNom
    })

    students.value = sortedStudents
  } catch (error: unknown) {
    console.error('Erreur API :', error)
    ui.notify("Erreur de chargement des données.", "error");
  } finally {
    loading.value = false
  }
});

const deleteStudent = async (student: Student) => {
  const confirmed = await ui.askConfirm(`Voulez-vous vraiment supprimer ${student.first_name} ${student.last_name} ?`);

  if (confirmed) {
    try {
      await api.deleteStudent(student.id);
      ui.notify("Étudiant supprimé avec succès !");
      loadData();
    } catch (e) {
      console.error(e)
      ui.notify("Erreur lors de la suppression.", "error");
    }
  }
};

const openEditModal = (student: Student) => {
  selectedStudent.value = student;
  showEditModal.value = true;
};

const handleUpdate = async (payload: StudentUpdatePayload) => {
  try {
    await api.updateStudent(payload.id, payload);
    
    ui.notify("Profil mis à jour avec succès !", "success");
    showEditModal.value = false;
    await loadData();
  } catch (err) {
    console.error(err);
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

table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

th,
td {
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
</style>
