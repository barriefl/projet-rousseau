<template>
  <div class="emile-regles">
    <div class="header">
      <h1>Typologies & Règles</h1>
      <button v-if="!selectedDictationId" class="btn btn-primary" @click="openModal('create')">
        ➕ Nouvelle Typologie
      </button>
    </div>

    <div class="dictation-selector-bar">
      <div class="selector-group">
        <label>Mode de configuration :</label>
        <select v-model="selectedDictationId" @change="loadDictationRules">
          <option value="">⚙️ Configuration Globale (Défaut)</option>
          <option v-for="dict in dictations" :key="dict.id" :value="dict.id">
            📝 Dictée : {{ dict.title }}
          </option>
        </select>
      </div>
      
      <div class="dictation-selector-bar">
      <div v-if="selectedDictationId" class="save-action">
        <button class="btn btn-success" @click="saveDictationRules" :disabled="isSavingRules">
          {{ isSavingRules ? '⏳ Recalcul en cours...' : '💾 Sauvegarder ce barème et recalculer les notes' }}
        </button>
      </div>
      
      <div v-else class="save-action">
        <button class="btn btn-primary" @click="recalculateGlobal" :disabled="isSavingRules">
          {{ isSavingRules ? '⏳ Mise à jour en cours...' : '🔄 Sauvegarder les règles et recalculer les notes' }}
        </button>
      </div>
    </div>
    </div>

    <div class="workspace-layout" :class="{ 'dictation-mode': selectedDictationId }">
      
      <div 
        v-if="!selectedDictationId"
        class="unassigned-panel"
        @dragover.prevent
        @dragenter.prevent="handleDragEnter"
        @dragleave.prevent="handleDragLeave"
        @drop="onDropUnassigned"
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
            @dragstart="onDragStart($event, rule, 'unassigned')"
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
              
              <div v-if="selectedDictationId" class="dictation-input-wrapper">
                <span>+</span>
                <input 
                  type="number" 
                  step="0.25" 
                  min="0" 
                  v-model.number="rulesConfigOverrides[typo.name]"
                  class="penalty-input"
                >
                <span>pt</span>
              </div>
              
              <template v-else>
                <span class="badge" style="background: #eee; color: #333; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;">
                  +{{ typo.penalty }} pt
                </span>
                <span class="edit-icon" @click="openModal('edit', typo)">✏️</span>
                <span class="edit-icon" style="color: var(--danger);" @click="deleteTypology(typo)">🗑️</span>
              </template>
            </div>
          </div>

          <div 
            class="typo-body"
            @dragover.prevent
            @dragenter.prevent="handleDragEnter"
            @dragleave.prevent="handleDragLeave"
            @drop="onDropToTypology($event, typo)"
            :class="{ 'disabled-drop': selectedDictationId }"
          >
            <div 
              v-for="rule in typo.rules" 
              :key="rule.id" 
              class="rule-item" 
              :draggable="!selectedDictationId"
              @dragstart="onDragStart($event, rule, typo.id)"
            >
              <div>
                <span class="rule-id">{{ rule.lt_rule_id }}</span>
                <div class="rule-info">{{ rule.description }}</div>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="rule.is_active" @change="toggleRuleActive(rule)" :disabled="selectedDictationId !== ''">
                <span class="slider"></span>
              </label>
            </div>
            
            <div v-if="!typo.rules || typo.rules.length === 0" style="text-align: center; color: #bdc3c7; font-size: 0.85rem; padding-top: 20px;">
              {{ selectedDictationId ? 'Aucune règle dans cette typologie.' : 'Glissez des règles LanguageTool ici.' }}
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

// Assurez-vous d'avoir ce type dans votre fichier index.ts, avec rules_config ?: Record<string, number>
import type { Dictation } from '@/types'; 

// --- ÉTATS GLOBAUX ---
const typologies = ref<any[]>([]);
const unclassifiedRules = ref<any[]>([]);
const isLoading = ref(true);
const isSaving = ref(false);

// --- ÉTATS POUR LE MODE DICTÉE ---
const dictations = ref<Dictation[]>([]);
const selectedDictationId = ref<number | ''>('');
const rulesConfigOverrides = ref<Record<string, number>>({});
const isSavingRules = ref(false);

// --- CHARGEMENT DES DONNÉES ---
const loadData = async () => {
  isLoading.value = true;
  try {
    const [typoRes, unassignedRes, dictRes] = await Promise.all([
      api.getGradingScales(),
      api.getUnclassifiedRules(),
      api.getDictations()
    ]);
    
    typologies.value = typoRes.data; 
    unclassifiedRules.value = unassignedRes.data;
    dictations.value = dictRes.data;
  } catch (error) {
    console.error("Erreur de chargement :", error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => { loadData(); });

// --- LOGIQUE DU MODE DICTÉE ---
const loadDictationRules = () => {
  if (!selectedDictationId.value) {
    rulesConfigOverrides.value = {};
    return;
  }

  const dict = dictations.value.find(d => d.id === selectedDictationId.value);
  rulesConfigOverrides.value = {};

  typologies.value.forEach(typo => {
    // On extrait la valeur d'abord pour satisfaire TypeScript
    const savedPenalty = dict?.rules_config?.[typo.name];

    if (savedPenalty !== undefined && savedPenalty !== null) {
      rulesConfigOverrides.value[typo.name] = savedPenalty;
    } else {
      rulesConfigOverrides.value[typo.name] = typo.penalty;
    }
  });
};

const saveDictationRules = async () => {
  if (!selectedDictationId.value) return;
  
  const confirmSave = confirm("Sauvegarder et recalculer toutes les copies de cette dictée ?");
  if (!confirmSave) return;

  isSavingRules.value = true;

  try {
    await api.updateDictationRules(Number(selectedDictationId.value), rulesConfigOverrides.value);
    
    // Mise à jour de la mémoire locale proprement
    const dictIndex = dictations.value.findIndex(d => d.id === selectedDictationId.value);
    const dictToUpdate = dictations.value[dictIndex];
    if (dictToUpdate) {
      dictToUpdate.rules_config = { ...rulesConfigOverrides.value };
    }

    alert("✅ Barème mis à jour et scores recalculés !");
  } catch (error) {
    console.error("Erreur lors de la sauvegarde :", error);
    alert("Erreur lors du recalcul.");
  } finally {
    isSavingRules.value = false;
  }
};

const recalculateGlobal = async () => {
  const confirmSave = confirm("Voulez-vous appliquer ce nouveau rangement de règles et recalculer les scores de TOUTES les dictées ?");
  if (!confirmSave) return;

  isSavingRules.value = true;

  try {
    // On prépare une liste d'appels API pour chaque dictée
    const updatePromises = dictations.value.map(dict => {
      
      // On reconstitue la configuration complète pour cette dictée
      const currentConfig: Record<string, number> = {};
      
      typologies.value.forEach(typo => {
        // Si la dictée avait déjà une pénalité personnalisée pour cette typologie, on la garde.
        // Sinon, on applique la pénalité par défaut de la typologie.
        const savedPenalty = dict.rules_config?.[typo.name];
        currentConfig[typo.name] = savedPenalty !== undefined ? savedPenalty : typo.penalty;
      });

      // 🌟 On appelle VOTRE route existante pour chaque dictée
      return api.updateDictationRules(dict.id, currentConfig);
    });

    // On exécute toutes les requêtes en même temps pour plus de rapidité
    await Promise.all(updatePromises);
    
    alert("✅ Toutes les règles ont été mises à jour et l'ensemble des copies recalculées !");
  } catch (error) {
    console.error("Erreur lors du recalcul global :", error);
    alert("Une erreur est survenue lors de la mise à jour globale.");
  } finally {
    isSavingRules.value = false;
  }
};

// --- LOGIQUE DRAG & DROP (Protégée contre le mode Dictée) ---
let draggedRule: any = null;
let draggedSourceId: number | 'unassigned' | null = null;

const onDragStart = (e: DragEvent, rule: any, sourceId: number | 'unassigned') => {
  if (selectedDictationId.value) {
    e.preventDefault();
    return;
  }
  draggedRule = rule;
  draggedSourceId = sourceId;
};

const handleDragEnter = (e: Event) => {
  if (selectedDictationId.value) return;
  (e.currentTarget as HTMLElement).classList.add('drag-over');
};

const handleDragLeave = (e: Event) => {
  if (selectedDictationId.value) return;
  (e.currentTarget as HTMLElement).classList.remove('drag-over');
};

const onDropToTypology = async (e: Event, targetTypo: any) => {
  if (selectedDictationId.value) return;
  (e.currentTarget as HTMLElement).classList.remove('drag-over');
  
  if (!draggedRule || draggedSourceId === targetTypo.id) return;
  
  try {
    await api.updateRule(draggedRule.id, { grading_scale_id: targetTypo.id });
    await loadData();
  } catch (error) {
    console.error("Erreur lors de l'assignation :", error);
  }
};

const onDropUnassigned = async (e: Event) => {
  if (selectedDictationId.value) return;
  (e.currentTarget as HTMLElement).classList.remove('drag-over');
  
  if (!draggedRule || draggedSourceId === 'unassigned') return;
  
  try {
    await api.updateRule(draggedRule.id, { grading_scale_id: null });
    await loadData();
  } catch (error) {
    console.error("Erreur lors du désassignement :", error);
  }
};

const toggleRuleActive = async (rule: any) => {
  try {
    await api.updateRule(rule.id, { is_active: rule.is_active });
  } catch (error) {
    rule.is_active = !rule.is_active; // Rollback
  }
};

// --- LOGIQUE MODAL TYPOLOGIE ---
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
/* CSS de base */
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header h1 { font-size: 1.6rem; color: var(--primary); margin: 0; }
.btn { padding: 8px 16px; border-radius: 5px; cursor: pointer; font-weight: 500; transition: 0.2s; border: none; }
.btn-primary { background: var(--accent); color: white; }
.btn-success { background: #2ecc71; color: white; font-weight: bold; }
.btn-success:hover:not(:disabled) { background: #27ae60; transform: translateY(-2px); }
.btn-outline { background: transparent; border: 1px solid #ccc; color: var(--text); }

/* --- NOUVEAU CSS POUR LE MODE DICTÉE --- */
.dictation-selector-bar {
  background: white;
  padding: 15px 20px;
  border-radius: 8px;
  border: 1px solid #e1e8ed;
  margin-bottom: 25px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.selector-group label { margin-right: 15px; font-weight: bold; color: var(--primary); }
.selector-group select { padding: 8px 12px; border-radius: 6px; border: 2px solid #ecf0f1; font-size: 1rem; outline: none; min-width: 300px; }
.selector-group select:focus { border-color: var(--accent); }

.dictation-input-wrapper { display: flex; align-items: center; gap: 5px; font-weight: bold; color: var(--danger); }
.penalty-input { width: 60px; padding: 4px; border: 2px solid #ccc; border-radius: 4px; text-align: center; font-weight: bold; color: var(--danger); outline: none; }
.penalty-input:focus { border-color: var(--accent); }

/* Modification du layout quand on édite une dictée */
.workspace-layout { display: grid; grid-template-columns: 350px 1fr; gap: 20px; align-items: start; transition: 0.3s; }
.workspace-layout.dictation-mode { grid-template-columns: 1fr; }
.disabled-drop { cursor: not-allowed; opacity: 0.9; }

/* Styles des typologies et du drag and drop */
.unassigned-panel { background: white; border-radius: 8px; border: 2px dashed #bdc3c7; padding: 20px; min-height: 500px; max-height: 80vh; overflow-y: auto; transition: 0.2s; }
.unassigned-panel.drag-over { background: #f0f8ff; border-color: var(--accent); }

.typologies-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.typo-box { background: white; border-radius: 8px; border: 1px solid #e1e8ed; display: flex; flex-direction: column; min-height: 300px; max-height: 500px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }

.typo-header { padding: 15px; border-bottom: 1px solid #eee; font-weight: bold; font-size: 0.95rem; display: flex; justify-content: space-between; align-items: center; color: var(--primary); }
.typo-header[data-type="D"] { border-top: 4px solid var(--type-d, #e67e22); }
.typo-header[data-type="R"] { border-top: 4px solid var(--type-r, #e74c3c); }
.typo-header[data-type="S"] { border-top: 4px solid var(--type-s, #3498db); }
.typo-header[data-type="AUTRE"] { border-top: 4px solid var(--type-autre, #9b59b6); }

.header-actions { display: flex; align-items: center; gap: 8px; }
.edit-icon { cursor: pointer; opacity: 0.7; transition: 0.2s; font-size: 1.1rem; }
.edit-icon:hover { opacity: 1; transform: scale(1.1); }

.typo-body { padding: 15px; flex: 1; overflow-y: auto; background: #fafafa; transition: 0.2s; }
.typo-body.drag-over { background: #f0f8ff; border: 2px dashed var(--accent); }

.rule-item { background: white; border: 1px solid #dcdde1; padding: 12px; margin-bottom: 10px; border-radius: 6px; cursor: grab; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.rule-item:active { cursor: grabbing; opacity: 0.6; }
.rule-id { font-family: monospace; color: var(--accent); font-weight: bold; font-size: 0.8rem; display: block; margin-bottom: 3px; }
.rule-info { font-size: 0.85rem; color: var(--text); line-height: 1.3; }

/* Switch css */
.switch { position: relative; display: inline-block; width: 34px; height: 18px; flex-shrink: 0; margin-left: 10px;}
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 20px; }
.slider:before { position: absolute; content: ""; height: 14px; width: 14px; left: 2px; bottom: 2px; background-color: white; transition: .4s; border-radius: 50%; }
input:checked + .slider { background-color: var(--accent, #1abc9c); } 
input:checked + .slider:before { transform: translateX(16px); }

/* Modal css */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); z-index: 1000; display: flex; justify-content: center; align-items: center; }
.modal { background: white; padding: 30px; border-radius: 8px; width: 550px; max-width: 90%; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-size: 0.9rem; font-weight: 500; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-family: inherit; }
.flex-row { display: flex; gap: 15px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 15px; }
</style>