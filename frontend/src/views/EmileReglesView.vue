<template>
  <div class="emile-regles">
    <div class="header">
      <h1>Catégories & Règles</h1>
      <button class="btn btn-primary" @click="recalculateGlobal" :disabled="isSavingRules">
        {{ isSavingRules ? '⏳ Recalcul en cours...' : '🔄 Recalculer les notes de toutes les dictées' }}
      </button>
    </div>

    <div v-if="isLoading" class="loading-container">
      <div class="loading-content">
        <span class="spinner">⏳</span>
        <p>Chargement des catégories et des règles...</p>
      </div>
    </div>

    <div v-else class="workspace-layout">
      <div class="categories-grid">
        <div 
          v-for="category in categories" 
          :key="category.id" 
          class="category-box"
        >
          <div class="category-header" :data-type="category.type_rousseau">
            <div style="display: flex; flex-direction: column; gap: 2px;">
              <span>{{ category.name }}</span>
              <span style="font-size: 0.75rem; font-family: monospace; font-weight: normal; opacity: 0.8;">
                {{ category.lt_category_id }}
              </span>
            </div>
            <div class="header-actions">
              <span class="badge" style="background: #eee; color: #333; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;">
                +{{ category.penalty }} pt
              </span>
              <span class="edit-icon" @click="openModal(category)">✏️</span>
            </div>
          </div>

          <div class="category-body">
            <div 
              v-for="rule in category.rules" 
              :key="rule.id" 
              class="rule-item" 
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
            
            <div v-if="!category.rules || category.rules.length === 0" style="text-align: center; color: #bdc3c7; font-size: 0.85rem; padding-top: 20px;">
              Aucune règle détectée pour cette catégorie.
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="isModalOpen" @click.self="closeModal">
      <div class="modal">
        <h2 style="color: var(--primary); margin-bottom: 20px;">Modifier la Catégorie</h2>
        
        <div class="form-group">
          <label>ID Technique (LanguageTool) :</label>
          <input type="text" :value="currentCategory.lt_category_id" disabled style="background-color: #f5f5f5; color: #888;">
        </div>
        
        <div class="form-group">
          <label>Nom de la catégorie :</label>
          <input type="text" v-model="currentCategory.name" disabled style="background-color: #f5f5f5; color: #888;">
        </div>
        
        <div class="flex-row">
          <div class="form-group" style="flex: 1;">
            <label>Type Rousseau :</label>
            <select v-model="currentCategory.type_rousseau">
              <option value="Dessin">D (Dessin)</option>
              <option value="Règle">R (Règle)</option>
              <option value="Sens">S (Sens)</option>
              <option value="Autre">AUTRE</option>
            </select>
          </div>
          <div class="form-group" style="flex: 1;">
            <label>Malus appliqué :</label>
            <input type="number" v-model="currentCategory.penalty" step="0.25" min="0">
          </div>
        </div>
        
        <div class="modal-actions">
          <button class="btn btn-outline" @click="closeModal">Annuler</button>
          <button class="btn btn-primary" @click="saveCategory" :disabled="isSaving || !currentCategory.name">
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

// --- ÉTATS GLOBAUX. ---
const categories = ref<any[]>([]);
const isLoading = ref(true);
const isSaving = ref(false);
const isSavingRules = ref(false);

// --- CHARGEMENT DES DONNÉES. ---
const loadData = async () => {
  isLoading.value = true;
  try {
    const res = await api.getCategories();
    categories.value = res.data;
  } catch (error) {
    console.error("Erreur de chargement :", error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => { loadData(); });

const recalculateGlobal = async () => {
  const confirmSave = confirm("Voulez-vous recalculer les scores de TOUTES les dictées avec le barème actuel ?");
  if (!confirmSave) return;

  isSavingRules.value = true;

  try {
    await api.recalculateAllDictations(); 
    alert("✅ Toutes les copies ont été recalculées avec succès !");
  } catch (error) {
    console.error("Erreur lors du recalcul global :", error);
    alert("Une erreur est survenue lors de la mise à jour globale.");
  } finally {
    isSavingRules.value = false;
  }
};

const toggleRuleActive = async (rule: any) => {
  try {
    await api.updateRule(rule.id, { is_active: rule.is_active });
  } catch (error) {
    rule.is_active = !rule.is_active;
  }
};

// --- LOGIQUE MODAL CATÉGORIE. ---
const isModalOpen = ref(false);
const currentCategory = ref<any>({});

const openModal = (category: any) => {
  currentCategory.value = { ...category };
  isModalOpen.value = true;
};

const closeModal = () => { isModalOpen.value = false; };

const saveCategory = async () => {
  isSaving.value = true;

  const payload = {
    type_rousseau: currentCategory.value.type_rousseau,
    penalty: currentCategory.value.penalty
  };

  try {
    await api.updateCategory(currentCategory.value.id, payload);
    await loadData();
    closeModal();
  } catch (error) {
    console.error("Erreur sauvegarde :", error);
  } finally {
    isSaving.value = false;
  }
};
</script>

<style scoped>
/* CSS de base. */
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

/* Modification du layout. */
.workspace-layout { 
  display: block; 
}

/* Styles des catégories. */
.categories-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); 
  gap: 20px; 
}
.category-box { 
  background: white; 
  border-radius: 8px; 
  border: 1px solid #e1e8ed; 
  display: flex; 
  flex-direction: column; 
  min-height: 300px; 
  max-height: 500px; 
  box-shadow: 0 2px 4px rgba(0,0,0,0.02); 
}

.category-header { 
  padding: 15px; 
  border-bottom: 1px solid #eee; 
  font-weight: bold; 
  font-size: 0.95rem; 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  color: var(--primary); 
}
.category-header[data-type="Dessin"] { border-top: 4px solid var(--type-d, #e67e22); }
.category-header[data-type="Règle"] { border-top: 4px solid var(--type-r, #e74c3c); }
.category-header[data-type="Sens"] { border-top: 4px solid var(--type-s, #3498db); }
.category-header[data-type="Autre"] { border-top: 4px solid var(--type-autre, #9b59b6); }

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

.category-body { 
  padding: 15px; 
  flex: 1; 
  overflow-y: auto; 
  background: #fafafa; 
}

.rule-item { 
  background: white; 
  border: 1px solid #dcdde1; 
  padding: 12px; 
  margin-bottom: 10px; 
  border-radius: 6px; 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  box-shadow: 0 1px 2px rgba(0,0,0,0.05); 
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

/* Switch CSS. */
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

/* Modal CSS. */
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

/* Barre de chargement. */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e1e8ed;
}
.loading-content {
  text-align: center;
  color: #7f8c8d;
}
.spinner {
  display: inline-block;
  font-size: 2rem;
  margin-bottom: 10px;
  animation: rotate 2s linear infinite;
}
@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>