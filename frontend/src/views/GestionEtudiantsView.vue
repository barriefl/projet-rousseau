<template>
  <div class="gestion-etudiants-view">
    <div class="page-header">
      <h1>Gestion des Étudiants</h1>
    </div>

    <div class="tabs-nav">
      <button class="btn tab-btn btn-with-icon" :class="{ active: activeTab === 'promotions' }"
        @click="activeTab = 'promotions'">
        <GraduationCap :size="18" />
        <span>Promotions</span>
      </button>

      <button class="btn tab-btn btn-with-icon" :class="{ active: activeTab === 'outils' }"
        @click="activeTab = 'outils'">
        <Wrench :size="18" />
        <span>Outils</span>
      </button>

      <button class="btn tab-btn btn-with-icon" :class="{ active: activeTab === 'groupes' }"
        @click="activeTab = 'groupes'">
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
            <td colspan="2">
              <AppEmptyState title="Aucune promotion" message="Impossible de charger les promotions." />
            </td>
          </tr>
          <tr v-for="promo in promotions" :key="promo.id">
            <td><strong>{{ promo.name }}</strong></td>
            <td style="text-align: right;">
              <div class="action-buttons">
                <button class="btn btn-outline btn-sm btn-with-icon" @click="openModal('promo', promo)">
                  <Pencil :size="14" />
                  <span>Modifier</span>
                </button>
                <button class="btn btn-danger btn-sm btn-with-icon" @click="deleteItem('promo', promo)">
                  <Trash2 :size="14" />
                  <span>Supprimer</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="activeTab === 'outils'" class="tab-content">
      <div class="content-header">
        <h2>Liste des Outils</h2>
        <button class="btn btn-primary btn-with-icon" @click="openModal('outil')">
          <Plus :size="18" />
          <span>Nouvel Outil</span>
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Code</th>
            <th>Nom complet</th>
            <th style="text-align: right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="outils?.length === 0">
            <td colspan="3">
              <AppEmptyState title="Aucun outil" message="Ajoutez un outil pour commencer." />
            </td>
          </tr>
          <tr v-for="outil in outils" :key="outil.id">
            <td><strong>{{ outil.name }}</strong></td>
            <td>{{ outil.full_name }}</td>
            <td style="text-align: right;">
              <div class="action-buttons">
                <button class="btn btn-outline btn-sm btn-with-icon" @click="openModal('outil', outil)">
                  <Pencil :size="14" />
                  <span>Modifier</span>
                </button>
                <button class="btn btn-danger btn-sm btn-with-icon" @click="deleteItem('outil', outil)">
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
            <td colspan="3">
              <AppEmptyState title="Aucun groupe" message="Impossible de charger les groupes." />
            </td>
          </tr>
          <tr v-for="groupe in groupes" :key="groupe.id">
            <td><strong>{{ groupe.name }}</strong></td>
            <td style="color: #555; font-size: 0.9rem;">{{ groupe.description || '-' }}</td>
            <td style="text-align: right;">
              <div class="action-buttons">
                <button class="btn btn-outline btn-sm btn-with-icon" @click="openModal('groupe', groupe)">
                  <Pencil :size="14" />
                  <span>Modifier</span>
                </button>
                <button class="btn btn-danger btn-sm btn-with-icon" @click="deleteItem('groupe', groupe)">
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
          {{ editingItem ? 'Modifier' : 'Ajouter' }}
          {{ modalType === 'promo' ? 'une promotion' : modalType === 'outil' ? 'un outil' : 'un groupe' }}
        </h2>

        <div class="form-group">
          <label>{{ modalType === 'outil' ? 'Code court *' : 'Nom *' }} :</label>
          <input type="text" v-model="formName" :placeholder="getPlaceholder" @keyup.enter="saveItem">
        </div>

        <div class="form-group" v-if="modalType === 'outil'" style="margin-top: 15px;">
          <label>Nom complet * :</label>
          <input type="text" v-model="formFullName" placeholder="Ex : Projet Voltaire">
        </div>

        <template v-if="modalType === 'groupe'">
          <div class="form-group" style="margin-top: 15px;">
            <label>Description :</label>
            <textarea v-model="formDescription" placeholder="Notes optionnelles..." rows="2"></textarea>
          </div>
        </template>

        <div class="modal-actions" style="margin-top: 25px;">
          <button class="btn btn-outline" @click="closeModal">Annuler</button>
          <button class="btn btn-primary" @click="saveItem" :disabled="!isFormValid">
            Enregistrer
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, type Ref } from 'vue';
import api from '@/services/api';

import type { Promotion, Tool, Group } from '@/types';

import { GraduationCap, Users, Plus, Pencil, Trash2, Wrench } from 'lucide-vue-next';

import AppEmptyState from '@/components/common/AppEmptyState.vue';

import { useUiStore } from '@/stores/ui';

const ui = useUiStore();

const activeTab = ref<'promotions' | 'outils' | 'groupes'>('promotions');

const promotions = ref<Promotion[]>([]);
const outils = ref<Tool[]>([]);
const groupes = ref<Group[]>([]);

interface Identifiable {
  id: number;
}

interface BaseItem {
  id: number;
  name: string;
}

// --- CHARGEMENT. ---
onMounted(async () => {
  try {
    const [promoRes, toolRes, groupRes] = await Promise.all([
      api.getPromotions(),
      api.getTools(),
      api.getGroups()
    ]);
    promotions.value = promoRes || [];
    outils.value = toolRes || [];
    groupes.value = groupRes || [];
  } catch (error) {
    console.error("Erreur de chargement :", error);
    ui.notify("Erreur lors du chargement des données.", "error");
  }
});

// --- GESTION DE LA MODALE. ---
const showModal = ref(false);
const modalType = ref<'promo' | 'outil' | 'groupe'>('promo');
const editingItem = ref<Promotion | Group | null>(null);

const formName = ref('');
const formFullName = ref('');
const formDescription = ref('');

const isFormValid = computed(() => {
  if (!formName.value.trim()) return false;
  if (modalType.value === 'outil' && !formFullName.value.trim()) return false;
  return true;
});

const getPlaceholder = computed(() => {
  if (modalType.value === 'promo') return 'Ex : 2024 - 2025';
  if (modalType.value === 'outil') return 'Ex : PV';
  return 'Ex : G1';
});

const openModal = (type: 'promo' | 'outil' | 'groupe', item: Promotion | Tool | Group | null = null) => {
  modalType.value = type;
  editingItem.value = item;
  formName.value = item ? item.name : '';

  formFullName.value = '';
  formDescription.value = '';

  if (!item) {
    showModal.value = true;
    return;
  }

  if (type === 'outil') {
    const tool = item as Tool;
    formFullName.value = tool.full_name || '';
  } else if (type === 'groupe') {
    const group = item as Group;
    formDescription.value = group.description || '';
  }

  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  editingItem.value = null;
  formName.value = '';
  formFullName.value = '';
  formDescription.value = '';
};

const saveItem = async () => {
  if (!isFormValid.value) return;

  try {
    let res;
    const type = modalType.value;

    if (type === 'promo') {
      res = editingItem.value
        ? await api.updatePromotion(editingItem.value.id, { name: formName.value })
        : await api.createPromotion({ name: formName.value });
      updateLocalList(promotions, res);
    }
    else if (type === 'outil') {
      const payload = { name: formName.value, full_name: formFullName.value };
      res = editingItem.value
        ? await api.updateTool(editingItem.value.id, payload)
        : await api.createTool(payload);
      updateLocalList(outils, res);
    }
    else if (type === 'groupe') {
      const payload = {
        name: formName.value,
        description: formDescription.value
      };

      res = editingItem.value
        ? await api.updateGroup(editingItem.value.id, payload)
        : await api.createGroup(payload);

      updateLocalList(groupes, res);
    }

    ui.notify("Enregistrement réussi.", "success");
    closeModal();
  } catch (error: unknown) {
    console.error('Erreur : ', error);
    ui.notify("Erreur lors de l'enregistrement.", "error");
  }
};

const updateLocalList = <T extends Identifiable>(listRef: Ref<T[]>, item: T) => {
  const index = listRef.value.findIndex((i) => i.id === item.id);
  if (index !== -1) listRef.value[index] = item;
  else listRef.value.push(item);
};

const deleteItem = async (type: 'promo' | 'outil' | 'groupe', item: BaseItem) => {
  if (await ui.askConfirm(`Supprimer "${item.name}" ?`)) {
    try {
      if (type === 'promo') await api.deletePromotion(item.id), promotions.value = promotions.value.filter(p => p.id !== item.id);
      if (type === 'outil') await api.deleteTool(item.id), outils.value = outils.value.filter(o => o.id !== item.id);
      if (type === 'groupe') await api.deleteGroup(item.id), groupes.value = groupes.value.filter(g => g.id !== item.id);
      ui.notify("Supprimé.", "success");
    }
    catch (error: unknown) {
      console.error('Erreur : ', error);
      ui.notify("Erreur suppression.", "error");
    }
  }
};
</script>

<style scoped>
/* ==========================================================================
   ONGLETS.
   ========================================================================== */
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

/* ==========================================================================
   TABLEAUX.
   ========================================================================== */
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


/* ==========================================================================
   BOUTONS.
   ========================================================================== */
.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 0.85rem;
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

/* ==========================================================================
   FORMULAIRE.
   ========================================================================== */
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
.form-group textarea:focus,
.form-group select:focus {
  border-color: var(--accent);
  outline: none;
}

select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
}
</style>