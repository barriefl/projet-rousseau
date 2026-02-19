<template>
  <div class="emile-regles">
    <div class="header">
      <h1>Typologies & Règles</h1>
      <button class="btn btn-primary" @click="openModal('create')">➕ Nouvelle Typologie</button>
    </div>

    <div class="workspace-layout">
      
      <div class="unassigned-panel"
           @dragover.prevent
           @dragenter.prevent="dragEnter($event)"
           @dragleave.prevent="dragLeave($event)"
           @drop="onDropUnassigned($event)"
      >
        <h3 style="margin-top: 0; color: var(--primary); border-bottom: 2px solid #eee; padding-bottom: 10px;">
          📥 Nouvelles règles détectées
        </h3>
        <p v-if="unclassifiedRules.length === 0" style="color: #7f8c8d; font-size: 0.9rem; text-align: center; margin-top: 20px;">
          Toutes les règles connues sont classées !
        </p>
        
        <div class="rules-container">
          <div 
            v-for="rule in unclassifiedRules" 
            :key="rule.id" 
            class="rule-item" 
            draggable="true"
            @dragstart="onDragStart(rule, 'unassigned')"
          >
            <div>
              <span class="rule-id">{{ rule.lt_rule_id }}</span>
              <div class="rule-info">{{ rule.description || 'Description manquante' }}</div>
            </div>
            <label class="switch">
              <input type="checkbox" v-model="rule.is_active" @change="toggleRuleActive(rule)">
              <span class="slider"></span>
            </label>
          </div>
        </div>
      </div>

      <div class="typologies-grid">
        <div v-if="isLoading" style="color: #7f8c8d; padding: 20px;">⏳ Chargement...</div>

        <div 
          v-else
          v-for="typo in typologies" 
          :key="typo.id" 
          class="typo-box"
        >
          <div class="typo-header" :data-type="typo.type_rousseau">
            <span>{{ typo.name }}</span>
            <div class="header-actions">
              <span class="badge" style="background: #eee; color: #333; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;">
                +{{ typo.penalty }} pt
              </span>
              <span class="edit-icon" @click="openModal('edit', typo)">✏️</span>
              <span class="edit-icon" style="color: var(--danger);" @click="deleteTypology(typo)">🗑️</span>
            </div>
          </div>

          <div 
            class="typo-body"
            @dragover.prevent
            @dragenter.prevent="dragEnter($event)"
            @dragleave.prevent="dragLeave($event)"
            @drop="onDropToTypology($event, typo)"
          >
            <div 
              v-for="rule in typo.rules" 
              :key="rule.id" 
              class="rule-item" 
              draggable="true"
              @dragstart="onDragStart(rule, typo.id)"
            >
              <div>
                <span class="rule-id">{{ rule.lt_rule_id }}</span>
                <div class="rule-info">{{ rule.description }}</div>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="rule.is_active" @change="toggleRuleActive(rule)">
                <span class="slider"></span>
              </label>
            </div>
            
            <div v-if="!typo.rules || typo.rules.length === 0" style="text-align: center; color: #bdc3c7; font-size: 0.85rem; padding-top: 20px;">
              Glissez des règles LanguageTool ici.
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="isModalOpen" @click.self="closeModal">
      <div class="modal">
        <h2 style="color: var(--primary); margin-bottom: 20px;">
          {{ modalMode === 'edit' ? 'Modifier la Typologie' : 'Nouvelle Typologie' }}
        </h2>
        
        <div class="form-group">
          <label>Titre de la typologie :</label>
          <input type="text" v-model="currentTypo.name">
        </div>
        
        <div class="form-group">
          <label>Description :</label>
          <textarea v-model="currentTypo.description" rows="2"></textarea>
        </div>
        
        <div class="flex-row">
          <div class="form-group" style="flex: 1;">
            <label>Type Rousseau :</label>
            <select v-model="currentTypo.type_rousseau">
              <option value="D">D (Dessin)</option>
              <option value="R">R (Règle)</option>
              <option value="S">S (Sens)</option>
              <option value="AUTRE">AUTRE</option>
            </select>
          </div>
          <div class="form-group" style="flex: 1;">
            <label>Malus appliqué :</label>
            <input type="number" v-model="currentTypo.penalty" step="0.25" min="0">
          </div>
        </div>
        
        <div class="modal-actions">
          <button class="btn btn-outline" @click="closeModal">Annuler</button>
          <button class="btn btn-primary" @click="saveTypology" :disabled="isSaving || !currentTypo.name">
            {{ isSaving ? 'Sauvegarde...' : 'Enregistrer' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import api from '@/services/api';

// --- ÉTATS. ---
const typologies = ref<any[]>([]);
const unclassifiedRules = ref<any[]>([]);
const isLoading = ref(true);
const isSaving = ref(false);

// --- CHARGEMENT. ---
const loadData = async () => {
  isLoading.value = true;
  try {
    const [typoRes, unassignedRes] = await Promise.all([
      api.getGradingScales(),
      api.getUnclassifiedRules()
    ]);
    
    typologies.value = typoRes.data; 
    unclassifiedRules.value = unassignedRes.data;
  } catch (error) {
    console.error("Erreur de chargement :", error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => { loadData(); });

// --- DRAG & DROP LOGIQUE API. ---
let draggedRule: any = null;
let draggedSourceId: number | 'unassigned' | null = null;

const onDragStart = (rule: any, sourceId: number | 'unassigned') => {
  draggedRule = rule;
  draggedSourceId = sourceId;
};

const dragEnter = (e: Event) => { (e.currentTarget as HTMLElement).classList.add('drag-over'); };
const dragLeave = (e: Event) => { (e.currentTarget as HTMLElement).classList.remove('drag-over'); };

// Action: Lâcher une règle dans une typologie.
const onDropToTypology = async (e: Event, targetTypo: any) => {
  (e.currentTarget as HTMLElement).classList.remove('drag-over');
  if (!draggedRule || draggedSourceId === targetTypo.id) return;

  try {
    await api.updateRule(draggedRule.id, { grading_scale_id: targetTypo.id });
    
    await loadData();
  } catch (error) {
    console.error("Erreur lors de l'assignation :", error);
    alert("Impossible de déplacer cette règle.");
  }
};

// Action: Lâcher une règle dans le panneau "Non assignées" (pour la retirer d'une typologie).
const onDropUnassigned = async (e: Event) => {
  (e.currentTarget as HTMLElement).classList.remove('drag-over');
  if (!draggedRule || draggedSourceId === 'unassigned') return;

  try {
    await api.updateRule(draggedRule.id, { grading_scale_id: null });
    await loadData();
  } catch (error) {
    console.error("Erreur lors du désassignement :", error);
  }
};

// Action: Activer / Désactiver une règle avec le Switch.
const toggleRuleActive = async (rule: any) => {
  try {
    await api.updateRule(rule.id, { is_active: rule.is_active });
  } catch (error) {
    console.error("Erreur de mise à jour du statut :", error);
    rule.is_active = !rule.is_active;
  }
};

// --- LOGIQUE MODAL TYPOLOGIE. ---
const isModalOpen = ref(false);
const modalMode = ref<'create' | 'edit'>('create');
const currentTypo = ref<any>({});

const openModal = (mode: 'create' | 'edit', typo?: any) => {
  modalMode.value = mode;
  if (mode === 'edit' && typo) {
    currentTypo.value = { ...typo };
  } else {
    currentTypo.value = { name: '', description: '', type_rousseau: 'D', penalty: 1.0 };
  }
  isModalOpen.value = true;
};

const closeModal = () => { isModalOpen.value = false; };

const saveTypology = async () => {
  isSaving.value = true;
  try {
    if (modalMode.value === 'edit') {
      // await api.updateGradingScale(currentTypo.value.id, currentTypo.value);
    } else {
      await api.createGradingScale(currentTypo.value);
    }
    await loadData();
    closeModal();
  } catch (error) {
    console.error("Erreur sauvegarde :", error);
  } finally {
    isSaving.value = false;
  }
};

const deleteTypology = async (typo: any) => {
  if (confirm(`Voulez-vous supprimer "${typo.name}" ? Ses règles redeviendront non assignées.`)) {
    try {
      await api.deleteGradingScale(typo.id);
      await loadData();
    } catch (error) {
      console.error("Erreur suppression :", error);
    }
  }
};
</script>

<style scoped>
.header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 20px; 
}
.header h1 { 
  font-size: 1.6rem; 
  color: var(--primary); 
  margin: 0; 
}
.btn { 
  padding: 8px 16px; 
  border-radius: 5px; 
  cursor: pointer; 
  font-weight: 500; 
  transition: 0.2s; 
  border: none; 
}
.btn-primary { 
  background: var(--accent); 
  color: white; 
}
.btn-outline { 
  background: transparent; 
  border: 1px solid #ccc; 
  color: var(--text); 
}

.workspace-layout { 
  display: grid; 
  grid-template-columns: 350px 1fr; 
  gap: 20px; 
  align-items: start; 
}

.unassigned-panel { 
  background: white; 
  border-radius: 8px; 
  border: 2px dashed #bdc3c7; 
  padding: 20px; 
  min-height: 500px; 
  max-height: 80vh; 
  overflow-y: auto; 
  transition: 0.2s; 
}
.unassigned-panel.drag-over { 
  background: #f0f8ff; 
  border-color: var(--accent); 
}

.typologies-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
  gap: 20px; 
}
.typo-box { 
  background: white; 
  border-radius: 8px; 
  border: 1px solid #e1e8ed; 
  display: flex; 
  flex-direction: column; 
  min-height: 300px; 
  max-height: 500px; 
  box-shadow: 0 2px 4px rgba(0,0,0,0.02); 
}

.typo-header { 
  padding: 15px; 
  border-bottom: 1px solid #eee; 
  font-weight: bold; 
  font-size: 0.95rem; 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  color: var(--primary); 
}
.typo-header[data-type="D"] { 
  border-top: 4px solid var(--type-d, #e67e22); 
}
.typo-header[data-type="R"] { 
  border-top: 4px solid var(--type-r, #e74c3c); 
}
.typo-header[data-type="S"] { 
  border-top: 4px solid var(--type-s, #3498db); 
}
.typo-header[data-type="AUTRE"] { 
  border-top: 4px solid var(--type-autre, #9b59b6); 
}

.header-actions { 
  display: flex; 
  align-items: center; 
  gap: 8px; 
}
.edit-icon { 
  cursor: pointer; 
  opacity: 0.7; 
  transition: 0.2s; 
  font-size: 1.1rem; 
}
.edit-icon:hover { 
  opacity: 1; 
  transform: scale(1.1); 
}

.typo-body { 
  padding: 15px; 
  flex: 1; 
  overflow-y: auto; 
  background: #fafafa; 
  transition: 0.2s; 
}
.typo-body.drag-over { 
  background: #f0f8ff; 
  border: 2px dashed var(--accent); 
}

.rule-item { 
  background: white; 
  border: 1px solid #dcdde1; 
  padding: 12px; 
  margin-bottom: 10px; 
  border-radius: 6px; 
  cursor: grab; 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  box-shadow: 0 1px 2px rgba(0,0,0,0.05); 
}
.rule-item:active { 
  cursor: grabbing; 
  opacity: 0.6; 
}
.rule-id { 
  font-family: monospace; 
  color: var(--accent); 
  font-weight: bold; 
  font-size: 0.8rem; 
  display: block; 
  margin-bottom: 3px; 
}
.rule-info { 
  font-size: 0.85rem; 
  color: var(--text); 
  line-height: 1.3; 
}

/* Switch. */
.switch { 
  position: relative; 
  display: inline-block; 
  width: 34px; 
  height: 18px; 
  flex-shrink: 0; 
  margin-left: 10px;
}
.switch input { 
  opacity: 0; 
  width: 0; 
  height: 0; 
}
.slider { 
  position: absolute; 
  cursor: pointer; 
  top: 0; 
  left: 0; 
  right: 0; 
  bottom: 0; 
  background-color: #ccc; 
  transition: .4s; 
  border-radius: 20px; 
}
.slider:before { 
  position: absolute; 
  content: ""; 
  height: 14px; 
  width: 14px; 
  left: 2px; 
  bottom: 2px; 
  background-color: white; 
  transition: .4s; 
  border-radius: 50%; 
}
input:checked + .slider { 
  background-color: var(--accent, #1abc9c); 
} 
input:checked + .slider:before { 
  transform: translateX(16px); 
}

/* Modal. */
.modal-overlay { 
  position: fixed; 
  top: 0; 
  left: 0; 
  right: 0; 
  bottom: 0; 
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
  width: 550px; 
  max-width: 90%; 
  box-shadow: 0 10px 25px rgba(0,0,0,0.2); 
}
.form-group { 
  margin-bottom: 15px; 
}
.form-group label { 
  display: block; 
  margin-bottom: 5px; 
  font-size: 0.9rem; 
  font-weight: 500; 
}
.form-group input, .form-group select, .form-group textarea { 
  width: 100%; 
  padding: 10px; 
  border: 1px solid #ccc; 
  border-radius: 4px; 
  font-family: inherit; 
}
.flex-row { 
  display: flex; 
  gap: 15px; 
}
.modal-actions { 
  display: flex; 
  justify-content: flex-end; 
  gap: 10px; 
  margin-top: 15px; 
}
</style>