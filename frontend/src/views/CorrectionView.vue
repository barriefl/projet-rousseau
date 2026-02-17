<template>
  <div class="emile-workspace">
    <div class="header">
      <h1>É.M.I.L.E.</h1>
    </div>

    <div class="search-container">
      <input type="text" class="search-input" v-model="searchQuery" placeholder="Rechercher un étudiant par nom...">
      <select class="filter-select">
        <option value="">Trier par...</option>
        <option value="name_asc">Nom (A-Z)</option>
        <option value="score_asc">Score (Croissant)</option>
        <option value="group">Groupe (G0 - G5)</option>
      </select>
    </div>
    
    <div class="student-scroll-list">
      <div 
        v-for="student in students" 
        :key="student.id"
        class="student-card" 
        :class="{ 'selected': selectedStudent?.id === student.id }"
        @click="selectStudent(student)"
      >
        <h4 style="color: var(--primary);">{{ student.nom }}, {{ student.prenom }}</h4>
        <p>{{ student.promo }} - {{ student.groupe }}</p>
      </div>
    </div>

    <div v-if="selectedStudent" class="dictation-selector">
      <h4 style="margin-bottom: 10px;">Dictées de l'étudiant :</h4>
      <div>
        <button 
          class="dictation-btn" 
          :class="{ 'active': selectedDictation === 'initiale' }"
          @click="selectDictation('initiale')"
        >Dictée Initiale (02/09)</button>
        <button 
          class="dictation-btn" 
          :class="{ 'active': selectedDictation === 'finale' }"
          @click="selectDictation('finale')"
        >Dictée Finale (15/11)</button>
      </div>
    </div>

    <div v-if="selectedDictation" class="atelier-container">
      
      <div 
        class="text-editor" 
        @mouseover="handleMouseOver" 
        @mouseout="handleMouseOut"
      >
        <div v-html="dictationHtml"></div>
        
        <div 
          v-show="tooltip.visible" 
          class="reverso-tooltip"
          :style="{ top: tooltip.y + 'px', left: tooltip.x + 'px' }"
        >
          <h5>Type {{ tooltip.type }} <span style="color:#e74c3c">+{{ tooltip.malus }} pt</span></h5>
          <div class="correction">{{ tooltip.corr }}</div>
          <div class="desc">{{ tooltip.desc }}</div>
        </div>
      </div>

      <div class="panel">
        <div class="score-display">
          <small style="color: #333; font-size: 0.85rem;">Score de la dictée</small>
          <span>10.75 pts</span>
          <small style="color: #7f8c8d; font-size: 0.75rem;">(Accumulation de malus, 0 = Parfait)</small>
        </div>
        
        <h3 style="font-size: 1rem; margin-bottom: 10px;">Liste des erreurs ({{ mistakes.length }})</h3>
        
        <div class="error-list">
          <div 
            v-for="(mistake, index) in visibleMistakes" 
            :key="index"
            class="error-item" 
            :data-type="mistake.type"
          >
            <strong>{{ mistake.word }}</strong><br>
            Correction : {{ mistake.corr }} (+{{ mistake.malus }})
          </div>
        </div>
        
        <button 
          v-if="!showAllErrors && mistakes.length > 5" 
          class="btn btn-outline" 
          style="margin-top: 10px; width: 100%;" 
          @click="showAllErrors = true"
        >
          Charger plus d'erreurs
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

// --- ÉTATS. ---
const searchQuery = ref('');
const selectedStudent = ref<any>(null);
const selectedDictation = ref<string | null>(null);
const showAllErrors = ref(false);

// État de l'infobulle.
const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  type: '',
  malus: '',
  corr: '',
  desc: ''
});

// --- DONNÉES DE DÉMO. ---
const students = ref([
  { id: 1, nom: 'Dupont', prenom: 'Jean', promo: 'BUT1', groupe: 'G1' },
  { id: 2, nom: 'Martin', prenom: 'Sophie', promo: 'BUT1', groupe: 'G2' }
]);

// Texte avec balises pré-générées (simule le retour de l'API).
const dictationHtml = ref(`
  <p>L'impact de l'informatique sur notre société est incontestable. Aujourd'hui, les professionnels <span class="faute" data-type="D" data-corr="couraient" data-malus="1.0" data-desc="Erreur de doublement : consonne superflue.">courraient</span> de grands risques s'ils négligeaient la sécurité de leurs réseaux. Cependant, tout le monde <span class="faute" data-type="S" data-corr="n'est" data-malus="1.5" data-desc="Confusion homophonique probable (s'est/c'est/n'est).">n'est</span> pas conscient des enjeux réels. Lors de mon dernier audit, j'ai vu des <span class="faute" data-type="R" data-corr="étudiants" data-malus="1.0" data-desc="Erreur de terminaison (pluriel manquant).">étudiant</span> faire des erreurs de manipulation basiques.</p>
  <br>
  <p>Il est donc crucial d'organiser des formations <span class="faute" data-type="R" data-corr="dédiées" data-malus="1.0" data-desc="Erreur de terminaison (accord adjectif).">dédiée</span> <span class="faute" data-type="R" data-corr="à" data-malus="0.5" data-desc="Absence d'accent grave.">a</span> ce sujet très spécifique. Beaucoup de collaborateurs <span class="faute" data-type="S" data-corr="ont" data-malus="1.5" data-desc="Confusion homophonique (ont/on).">on</span> l'impression que le piratage n'arrive qu'aux autres. Nous devons <span class="faute" data-type="R" data-corr="sensibiliser" data-malus="1.0" data-desc="Mauvaise conjugaison (infinitif requis).">sensibilisé</span> le public. C'est un <span class="faute" data-type="AUTRE" data-corr="véritable" data-malus="0.25" data-desc="Mot inconnu / Erreur non classifiée.">véritabl</span> défi.</p>
`);

// Liste des erreurs pour le panneau latéral.
const mistakes = ref([
  { word: 'courraient', corr: 'couraient', malus: 1.0, type: 'D' },
  { word: 'n\'est', corr: 'n\'est', malus: 1.5, type: 'S' },
  { word: 'étudiant', corr: 'étudiants', malus: 1.0, type: 'R' },
  { word: 'dédiée', corr: 'dédiées', malus: 1.0, type: 'R' },
  { word: 'a', corr: 'à', malus: 0.5, type: 'R' },
  { word: 'on', corr: 'ont', malus: 1.5, type: 'S' },
  { word: 'sensibilisé', corr: 'sensibiliser', malus: 1.0, type: 'R' },
  { word: 'véritabl', corr: 'véritable', malus: 0.25, type: 'AUTRE' }
]);

const visibleMistakes = computed(() => showAllErrors.value ? mistakes.value : mistakes.value.slice(0, 5));

// --- ACTIONS. ---
const selectStudent = (student: any) => {
  selectedStudent.value = student;
  selectedDictation.value = null;
};

const selectDictation = (type: string) => {
  selectedDictation.value = type;
  showAllErrors.value = false;
};

// --- GESTION DE L'INFOBULLE. ---
const handleMouseOver = (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  
  if (target.classList.contains('faute')) {
    tooltip.value = {
      visible: true,
      x: target.offsetLeft,
      y: target.offsetTop + 30,
      type: target.getAttribute('data-type') || '',
      malus: target.getAttribute('data-malus') || '',
      corr: target.getAttribute('data-corr') || '',
      desc: target.getAttribute('data-desc') || ''
    };
  }
};

const handleMouseOut = (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  if (target.classList.contains('faute')) {
    tooltip.value.visible = false;
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

/* Recherche & Filtres. */
.search-container { 
    margin-bottom: 15px; 
    display: flex; 
    gap: 10px; 
}
.search-input { 
    flex: 1; 
    max-width: 400px; 
    padding: 10px 15px; 
    border-radius: 20px; 
    border: 1px solid #ccc; 
    outline: none; 
}
.filter-select { 
    padding: 10px 15px; 
    border-radius: 20px; 
    border: 1px solid #ccc; 
    outline: none; 
    background: white; 
    cursor: pointer; 
}

/* Liste Étudiants. */
.student-scroll-list { 
    display: flex; 
    gap: 15px; 
    overflow-x: auto; 
    padding-bottom: 10px; 
    margin-bottom: 20px; 
}
.student-card { 
    min-width: 200px; 
    background: white; 
    padding: 15px; 
    border-radius: 8px; 
    border: 1px solid #e1e8ed; 
    cursor: pointer; 
    transition: 0.2s; 
}
.student-card:hover { 
    transform: translateY(-2px); 
    border-color: var(--accent); 
    box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
}
.student-card.selected { 
    border: 2px solid var(--accent); 
    background-color: #f0f8ff; 
}

/* Sélecteur Dictées. */
.dictation-selector { 
    margin-bottom: 20px; 
    padding: 15px; 
    background: white; 
    border-radius: 8px; 
    border: 1px dashed #ccc; 
}
.dictation-btn { 
    padding: 8px 12px; 
    background: var(--light); 
    border: 1px solid #ccc; 
    border-radius: 4px; 
    cursor: pointer; 
    margin-right: 10px; 
    font-size: 0.9rem; 
    transition: 0.2s; 
}
.dictation-btn:hover, .dictation-btn.active { 
    background: var(--accent); 
    color: white; 
    border-color: var(--accent); 
}

/* Layout Atelier. */
.atelier-container { 
    display: grid; 
    grid-template-columns: 2fr 1fr; 
    gap: 20px; 
}

/* Éditeur de texte. */
.text-editor { 
  background: white; 
  padding: 30px; 
  border-radius: 8px; 
  border: 1px solid #e1e8ed; 
  font-family: 'Georgia', serif; 
  font-size: 1.15rem; 
  line-height: 2; 
  min-height: 400px; 
  position: relative;
}

:deep(.faute) { 
  cursor: pointer; 
  border-bottom: 2px dashed; 
  padding-bottom: 1px; 
  font-weight: 500; 
  transition: 0.2s;
}
:deep(.faute:hover) { 
    background-color: rgba(0,0,0,0.05); 
}
:deep(.faute[data-type="D"]) { 
    border-color: var(--type-d); 
    color: var(--type-d); 
}
:deep(.faute[data-type="R"]) { 
    border-color: var(--type-r); 
    color: var(--type-r); 
}
:deep(.faute[data-type="S"]) { 
    border-color: var(--type-s); 
    color: var(--type-s); 
}
:deep(.faute[data-type="AUTRE"]) { 
    border-color: var(--type-autre); 
    color: var(--type-autre); 
}

/* Infobulle. */
.reverso-tooltip { 
  position: absolute; 
  background: white; 
  border: 1px solid #ccc; 
  box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
  border-radius: 6px; 
  padding: 15px; 
  width: 280px; 
  z-index: 100; 
  font-family: 'Segoe UI', sans-serif; 
}
.reverso-tooltip h5 { 
    font-size: 0.95rem; 
    margin-bottom: 5px; 
    color: var(--primary); 
    display: flex; 
    justify-content: space-between; 
}
.reverso-tooltip .correction { 
    font-size: 1.1rem; 
    font-weight: bold; 
    color: var(--accent); 
    margin-bottom: 8px; 
}
.reverso-tooltip .desc { 
    font-size: 0.85rem; 
    color: #555; 
    line-height: 1.4; 
}

/* Panneau droit (Scores). */
.panel { 
    background: white; 
    padding: 20px; 
    border-radius: 8px; 
    border: 1px solid #e1e8ed; 
    display: flex; 
    flex-direction: column; 
    max-height: 600px; 
}
.score-display { 
    text-align: center; 
    margin-bottom: 15px; 
    padding: 15px; 
    background: #fff5f5; 
    border-radius: 8px; 
    border: 1px solid #fadbd8; 
}
.score-display span { 
    font-size: 2.2rem; 
    font-weight: bold; 
    color: var(--danger); 
    display: block; 
}

.error-list { 
    overflow-y: auto; 
    flex: 1; 
    padding-right: 5px; 
}
.error-item { 
    padding: 10px; 
    border-left: 4px solid; 
    background: #fdfdfd; 
    margin-bottom: 8px; 
    font-size: 0.85rem; 
    border-radius: 4px; 
    border: 1px solid #eee; 
}
.error-item[data-type="D"] { 
    border-left-color: var(--type-d); 
}
.error-item[data-type="R"] { 
    border-left-color: var(--type-r); 
}
.error-item[data-type="S"] { 
    border-left-color: var(--type-s); 
}
.error-item[data-type="AUTRE"] { 
    border-left-color: var(--type-autre); 
}

.btn { 
    padding: 8px 16px; 
    border-radius: 5px; 
    cursor: pointer; 
    font-weight: 500; 
    transition: 0.2s; 
    border: none; 
}
.btn-outline { 
    background: transparent; 
    border: 1px solid #ccc; 
    color: var(--text); 
}
.btn-outline:hover { 
    background: #f8f9fa; 
    border-color: var(--primary); 
}
</style>