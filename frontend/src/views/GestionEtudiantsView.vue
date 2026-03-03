<template>
  <div class="gestion-etudiants-view">
    <div class="header">
      <h1>Gestion des Étudiants</h1>
    </div>

    <div class="tabs-nav">
      <button class="tab-btn btn-with-icon" :class="{ active: activeTab === 'promotions' }"
        @click="activeTab = 'promotions'">
        <GraduationCap :size="18" />
        <span>Promotions</span>
      </button>
      <button class="tab-btn btn-with-icon" :class="{ active: activeTab === 'groupes' }" @click="activeTab = 'groupes'">
        <Users :size="18" />
        <span>Groupes</span>
      </button>
    </div>

    <div v-if="activeTab === 'promotions'" class="tab-content">
      <div class="content-header">
        <h2>Liste des Promotions</h2>
        <button class="btn btn-primary btn-with-icon" @click="openModal('promo')">
          <Plus :size="18" />
          <span>Nouvelle Promotion</span>
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Nom de la promotion</th>
            <th style="text-align: right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="promotions?.length === 0">
            <td colspan="2" class="empty-state">Aucune promotion configurée.</td>
          </tr>
          <tr v-for="promo in promotions" :key="promo.id">
            <td><strong>{{ promo.name }}</strong></td>
            <td style="text-align: right;">
              <div class="action-buttons">
                <button class="btn-outline btn-sm btn-with-icon" @click="openModal('promo', promo)">
                  <Pencil :size="14" />
                  <span>Modifier</span>
                </button>
                <button class="btn-danger btn-sm btn-with-icon" @click="deleteItem('promo', promo)">
                  <Trash2 :size="14" />
                  <span>Supprimer</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="activeTab === 'groupes'" class="tab-content">
      <div class="content-header">
        <h2>Liste des Groupes</h2>
        <button class="btn btn-primary btn-with-icon" @click="openModal('groupe')">
          <Plus :size="18" />
          <span>Nouveau Groupe</span>
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Nom du groupe</th>
            <th>Description</th>
            <th style="text-align: right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="groupes?.length === 0">
            <td colspan="3" class="empty-state">Aucun groupe configuré.</td>
          </tr>
          <tr v-for="groupe in groupes" :key="groupe.id">
            <td><strong>{{ groupe.name }}</strong></td>
            <td style="color: #555; font-size: 0.9rem;">{{ groupe.description || '-' }}</td>
            <td style="text-align: right;">
              <div class="action-buttons">
                <button class="btn-outline btn-sm btn-with-icon" @click="openModal('groupe', groupe)">
                  <Pencil :size="14" />
                  <span>Modifier</span>
                </button>
                <button class="btn-danger btn-sm btn-with-icon" @click="deleteItem('groupe', groupe)">
                  <Trash2 :size="14" />
                  <span>Supprimer</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
      <div class="modal">
        <h2 style="color: var(--primary); margin-bottom: 20px;">
          {{ editingItem ? 'Modifier' : 'Ajouter' }} {{ modalType === 'promo' ? 'une promotion' : 'un groupe' }}
        </h2>

        <div class="form-group">
          <label>Nom * :</label>
          <input type="text" v-model="formName" :placeholder="modalType === 'promo' ? 'Ex: 2024-2025' : 'Ex: G1'"
            @keyup.enter="saveItem">
        </div>

        <div class="form-group" v-if="modalType === 'groupe'" style="margin-top: 15px;">
          <label>Description :</label>
          <textarea v-model="formDescription" placeholder="Ex: Jalons obligatoires..." rows="3"></textarea>
        </div>

        <div class="modal-actions" style="margin-top: 25px;">
          <button class="btn btn-outline" @click="closeModal">Annuler</button>
          <button class="btn btn-primary" @click="saveItem" :disabled="!formName.trim()">
            Enregistrer
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import api from '@/services/api';
import type { Promotion, Group } from '@/types';
import { GraduationCap, Users, Plus, Pencil, Trash2 } from 'lucide-vue-next';
import { useUiStore } from '@/stores/ui';

const ui = useUiStore();

const activeTab = ref<'promotions' | 'groupes'>('promotions');

const promotions = ref<Promotion[]>([]);
const groupes = ref<Group[]>([]);

// --- CHARGEMENT INITIAL. ---
onMounted(async () => {
  try {
    const [promoRes, groupRes] = await Promise.all([
      api.getPromotions(),
      api.getGroups()
    ]);
    promotions.value = promoRes || [];
    groupes.value = groupRes || [];
  } catch (error) {
    console.error("Erreur de chargement :", error);
    ui.notify("Erreur lors du chargement des données.", "error");
  }
});

// --- GESTION DE LA MODALE. ---
const showModal = ref(false);
const modalType = ref<'promo' | 'groupe'>('promo');
const editingItem = ref<Promotion | Group | null>(null);
const formName = ref('');
const formDescription = ref('');

const openModal = (type: 'promo' | 'groupe', item: Promotion | Group | null = null) => {
  modalType.value = type;
  editingItem.value = item;
  formName.value = item ? item.name : '';

  if (item && type === 'groupe' && 'description' in item) {
    formDescription.value = item.description || '';
  } else {
    formDescription.value = '';
  }

  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  editingItem.value = null;
  formName.value = '';
  formDescription.value = '';
};

const saveItem = async () => {
  if (!formName.value.trim()) return;

  const isPromo = modalType.value === 'promo';
  const label = isPromo ? 'Promotion' : 'Groupe';

  try {
    if (editingItem.value) {
      // MODE ÉDITION.
      if (isPromo) {
        const res = await api.updatePromotion(editingItem.value.id, { name: formName.value });
        const index = promotions.value.findIndex(p => p.id === editingItem.value!.id);
        if (index !== -1) promotions.value[index] = res as Promotion;
      } else {
        const res = await api.updateGroup(editingItem.value.id, {
          name: formName.value,
          description: formDescription.value || null
        });
        const index = groupes.value.findIndex(g => g.id === editingItem.value!.id);
        if (index !== -1) groupes.value[index] = res as Group;
      }
      ui.notify(`${label} modifiée.`, "success");

    } else {
      // MODE CRÉATION.
      if (isPromo) {
        const res = await api.createPromotion({ name: formName.value });
        promotions.value.push(res as Promotion);
      } else {
        const res = await api.createGroup({
          name: formName.value,
          description: formDescription.value || null
        });
        groupes.value.push(res as Group);
      }
      ui.notify(`${label} ajoutée.`, "success");
    }

    closeModal();

  } catch (error: unknown) {
    console.error(error);
    ui.notify("Erreur lors de l'enregistrement.", "error");
  }
};

const deleteItem = async (type: 'promo' | 'groupe', item: Promotion | Group) => {
  const label = type === 'promo' ? 'cette promotion' : 'ce groupe';
  const confirmed = await ui.askConfirm(`Êtes-vous sûr de vouloir supprimer ${label} ("${item.name}") ?`);

  if (confirmed) {
    try {
      if (type === 'promo') {
        await api.deletePromotion(item.id);
        promotions.value = promotions.value.filter(p => p.id !== item.id);
      } else {
        await api.deleteGroup(item.id);
        groupes.value = groupes.value.filter(g => g.id !== item.id);
      }
      ui.notify("Suppression effectuée.", "success");
    } catch (error: unknown) {
      console.error(error);
      ui.notify("Erreur lors de la suppression.", "error");
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
  margin: 0;
}

/* --- SYSTÈME D'ONGLETS. --- */
.tabs-nav {
  display: flex;
  gap: 10px;
  border-bottom: 2px solid #eee;
  margin-bottom: 25px;
}

.tab-btn {
  padding: 12px 20px;
  border: none;
  background: none;
  cursor: pointer;
  font-weight: 600;
  color: #7f8c8d;
  transition: all 0.2s;
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
}

.tab-btn:hover {
  color: var(--primary);
  background: #f8f9fa;
}

.tab-btn.active {
  color: var(--accent);
}

.tab-btn.active::after {
  content: "";
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background-color: var(--accent);
}

.tab-btn.active svg {
  transform: scale(1.1);
  color: var(--accent);
}

.tab-content {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.content-header h2 {
  font-size: 1.2rem;
  color: var(--primary);
  margin: 0;
}

/* --- TABLEAUX. --- */
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

.empty-state {
  text-align: center;
  color: #7f8c8d;
  padding: 30px;
  font-style: italic;
}

/* --- BOUTONS. --- */
.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 0.85rem;
}

.btn-with-icon {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-danger:hover {
  background-color: #c0392b;
  box-shadow: 0 2px 4px rgba(231, 76, 60, 0.2);
}

.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: 0.2s;
  font-weight: 500;
  padding: 8px 16px;
}

.btn-primary:hover:not(:disabled) {
  background: #12876f;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-danger {
  background: var(--danger);
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: 0.2s;
}

.btn-danger:hover {
  background: #c0392b;
  transform: scale(1.05);
}

.btn-outline {
  background: transparent;
  border: 1px solid #ccc;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-outline:hover {
  background: #eee;
}

/* --- MODALES. --- */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal {
  background: white;
  padding: 30px;
  border-radius: 8px;
  width: 450px;
  max-width: 90%;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  font-size: 0.9rem;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-family: inherit;
  box-sizing: border-box;
  resize: vertical;
}

.form-group input:focus,
.form-group textarea:focus {
  border-color: var(--accent);
  outline: none;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.confirm-modal {
  width: 400px;
  text-align: center;
}

.confirm-modal .modal-actions {
  justify-content: center;
  margin-top: 30px;
}
</style>