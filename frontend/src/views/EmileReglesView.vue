<template>
  <div class="emile-regles">
    <div class="header">
      <h1>Typologies & Règles</h1>
      <button class="btn btn-primary" @click="openModal('create')">➕ Nouvelle Typologie</button>
    </div>
    
    <div class="settings-context">
      <div>
        <strong>Surcharge par dictée :</strong>
        <select class="settings-select">
          <option>Configuration Globale (Défaut)</option>
          <option>Dictée #1 (Jean Dupont)</option>
        </select>
      </div>
    </div>

    <div class="typologies-grid">
      <div 
        v-for="typo in typologies" 
        :key="typo.id" 
        class="typo-box"
      >
        <div class="typo-header" :data-type="typo.typeRousseau">
          <span>{{ typo.title }}</span>
          <div class="header-actions">
            <input type="number" class="malus-input" v-model="typo.malus" step="0.5" min="0">
            <span class="edit-icon" @click="openModal('edit', typo)">✏️</span>
          </div>
        </div>

        <div 
          class="typo-body"
          @dragover.prevent
          @dragenter.prevent="dragEnter($event)"
          @dragleave.prevent="dragLeave($event)"
          @drop="onDrop($event, typo.id)"
        >
          <div 
            v-for="rule in typo.rules" 
            :key="rule.id" 
            class="rule-item" 
            draggable="true"
            @dragstart="onDragStart(rule.id, typo.id)"
          >
            <div>
              <span class="rule-id">{{ rule.lt_id }}</span>
              <div class="rule-info">{{ rule.info }}</div>
            </div>
            <label class="switch">
              <input type="checkbox" v-model="rule.active">
              <span class="slider"></span>
            </label>
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
          <label>Titre :</label>
          <input type="text" v-model="currentTypo.title">
        </div>
        <div class="form-group">
          <label>Description :</label>
          <textarea v-model="currentTypo.description" rows="2"></textarea>
        </div>
        
        <div class="flex-row">
          <div class="form-group" style="flex: 1;">
            <label>Type :</label>
            <select v-model="currentTypo.typeRousseau">
              <option value="D">D</option>
              <option value="R">R</option>
              <option value="S">S</option>
              <option value="AUTRE">AUTRE</option>
            </select>
          </div>
          <div class="form-group" style="flex: 1;">
            <label>Couleur :</label>
            <input type="color" v-model="currentTypo.color" style="height: 42px; padding: 2px;">
          </div>
          <div class="form-group" style="flex: 1;">
            <label>Malus par défaut :</label>
            <input type="number" v-model="currentTypo.malus" step="0.5" min="0">
          </div>
        </div>
        
        <div class="modal-actions">
          <button class="btn btn-outline" @click="closeModal">Annuler</button>
          <button class="btn btn-primary" @click="saveTypology">Enregistrer</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

// --- TYPES. ---
type TypeRousseau = 'D' | 'R' | 'S' | 'AUTRE';

interface Rule {
  id: string;
  lt_id: string;
  info: string;
  active: boolean;
}

interface Typology {
  id: number;
  title: string;
  description: string;
  typeRousseau: TypeRousseau;
  color: string;
  malus: number;
  rules: Rule[];
}

// --- DONNÉES DE DÉMONSTRATION. ---
const typologies = ref<Typology[]>([
  {
    id: 1,
    title: 'Fautes de frappe (Type D)',
    description: 'Substitutions, omissions, ajouts de lettres ou de mots.',
    typeRousseau: 'D',
    color: '#3498db',
    malus: 1.0,
    rules: [{ id: 'r1', lt_id: 'TYPO_SPELLING', info: 'Substitutions, omissions...', active: true }]
  },
  {
    id: 2,
    title: 'Erreurs d\'accents et de cédilles',
    description: 'Absence ou mauvaise utilisation (é/è/ç)',
    typeRousseau: 'R',
    color: '#e74c3c',
    malus: 0.5,
    rules: [{ id: 'r2', lt_id: 'FRENCH_ACCENTS', info: 'Absence ou mauvaise utilisation (é/è/ç)', active: true }]
  },
  {
    id: 3,
    title: 'Confusions homophoniques (S)',
    description: 'Confondre des mots qui se prononcent pareil (a/à, et/est)',
    typeRousseau: 'S',
    color: '#9b59b6',
    malus: 1.5,
    rules: [
      { id: 'r3', lt_id: 'A_VS_A_ACCENT', info: 'Confusion a / à', active: true },
      { id: 'r4', lt_id: 'SON_VS_SONT', info: 'Confusion son / sont', active: true }
    ]
  }
]);

// --- LOGIQUE DRAG & DROP. ---
let draggedRuleId: string | null = null;
let draggedFromTypoId: number | null = null;

const onDragStart = (ruleId: string, typoId: number) => {
  draggedRuleId = ruleId;
  draggedFromTypoId = typoId;
};

const dragEnter = (e: Event) => { (e.currentTarget as HTMLElement).classList.add('drag-over'); };
const dragLeave = (e: Event) => { (e.currentTarget as HTMLElement).classList.remove('drag-over'); };

const onDrop = (e: Event, targetTypoId: number) => {
  (e.currentTarget as HTMLElement).classList.remove('drag-over');
  
  if (!draggedRuleId || draggedFromTypoId === null || draggedFromTypoId === targetTypoId) return;

  const sourceTypo = typologies.value.find(t => t.id === draggedFromTypoId);
  const targetTypo = typologies.value.find(t => t.id === targetTypoId);

  if (sourceTypo && targetTypo) {
    const ruleIndex = sourceTypo.rules.findIndex(r => r.id === draggedRuleId);
    if (ruleIndex > -1) {
      const [movedRule] = sourceTypo.rules.splice(ruleIndex, 1);

      if (movedRule) {
        targetTypo.rules.push(movedRule);
      }
    }
  }

  draggedRuleId = null;
  draggedFromTypoId = null;
};

// --- LOGIQUE MODAL. ---
const isModalOpen = ref(false);
const modalMode = ref<'create' | 'edit'>('create');
const currentTypo = ref<Partial<Typology>>({});

const openModal = (mode: 'create' | 'edit', typo?: Typology) => {
  modalMode.value = mode;
  if (mode === 'edit' && typo) {
    currentTypo.value = JSON.parse(JSON.stringify(typo)); 
  } else {
    currentTypo.value = { title: '', description: '', typeRousseau: 'D', color: '#16a085', malus: 1.0, rules: [] };
  }
  isModalOpen.value = true;
};

const closeModal = () => { isModalOpen.value = false; };

const saveTypology = () => {
  if (modalMode.value === 'edit') {
    const index = typologies.value.findIndex(t => t.id === currentTypo.value.id);
    if (index > -1) typologies.value[index] = currentTypo.value as Typology;
  } else {
    const newId = Math.max(...typologies.value.map(t => t.id), 0) + 1;
    typologies.value.push({ ...currentTypo.value, id: newId } as Typology);
  }
  closeModal();
};
</script>

<style scoped>
/* En-tête. */
.header { 
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
    margin-bottom: 20px; 
}
.header h1 { 
    font-size: 1.6rem; 
    color: var(--primary); 
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

/* Paramètres. */
.settings-context { 
    display: flex; 
    justify-content: space-between; 
    background: white; 
    padding: 15px; 
    border-radius: 8px; 
    border: 1px solid #ccc; 
    margin-bottom: 20px; 
    align-items: center;
}
.settings-select { 
    margin-left: 10px; 
    padding: 6px; 
    border-radius: 4px; 
    border: 1px solid #ccc; 
    outline: none; 
}

/* Grille et Boîtes Typologies. */
.typologies-grid { 
    display: grid; 
    grid-template-columns: repeat(3, 1fr); 
    gap: 20px; 
}
.typo-box { 
    background: white; 
    border-radius: 8px; 
    border: 1px solid #e1e8ed; 
    display: flex; 
    flex-direction: column; 
    min-height: 250px; 
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
    border-top: 4px solid var(--type-d); 
}
.typo-header[data-type="R"] { 
    border-top: 4px solid var(--type-r); 
}
.typo-header[data-type="S"] { 
    border-top: 4px solid var(--type-s); 
}
.typo-header[data-type="AUTRE"] { 
    border-top: 4px solid var(--type-autre); 
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
}
.edit-icon:hover { 
    opacity: 1; 
    transform: scale(1.1); 
}
.malus-input { 
    width: 60px; 
    padding: 5px; 
    border: 1px solid #ccc; 
    border-radius: 4px; 
    text-align: center; 
    font-weight: normal; 
}

/* Corps & Drag/Drop. */
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

/* Item Règle. */
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
    color: #7f8c8d; 
    font-size: 0.75rem; 
    display: block; 
    margin-bottom: 2px; 
}
.rule-info { 
    font-size: 0.9rem; 
    color: var(--text); 
}

/* Switch Toggle CSS Pur. */
.switch { 
    position: relative; 
    display: inline-block; 
    width: 40px; 
    height: 20px; 
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
    height: 16px; 
    width: 16px; 
    left: 2px; 
    bottom: 2px; 
    background-color: white; 
    transition: .4s; 
    border-radius: 50%; 
}
input:checked + .slider { 
    background-color: #1abc9c; 
} 
input:checked + .slider:before { 
    transform: translateX(20px); 
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