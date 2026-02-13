<template>
  <div class="correction-tool">
    <h2>Nouvelle Correction</h2>
    
    <div class="input-section">
      <textarea 
        v-model="textStudent" 
        rows="10" 
        class="text-input"
        placeholder="Coller le texte de l'étudiant ici..."
      ></textarea>
      <div class="actions">
        <button @click="submitCorrection" :disabled="isSubmitting" class="btn-primary">
          {{ isSubmitting ? 'Correction en cours...' : 'Lancer la correction' }}
        </button>
      </div>
    </div>

    <div v-if="result" class="result-section">
      <div class="score-card">
        <h3>Note Finale (Pénalités) : <span class="score">{{ result.final_score }}</span></h3>
      </div>
      
      <div class="text-display" v-html="highlightedText"></div>

      <div class="mistakes-list">
        <h4>Détails des fautes ({{ result.mistakes.length }}) :</h4>
        <ul>
          <li v-for="(m, index) in result.mistakes" :key="index">
            <span :class="`badge mistake-${m.type_rousseau}`">{{ m.type_rousseau }}</span>
            <strong>{{ m.student_word }}</strong> : {{ m.message }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import api from '@/services/api';
import type { Submission } from '@/types';

const textStudent = ref("");
const result = ref<Submission | null>(null);
const isSubmitting = ref(false);

const highlightedText = computed(() => {
  if (!result.value || !result.value.mistakes) return textStudent.value;

  // On utilise le texte renvoyé ou celui saisi par défaut
  let original = result.value.content_student || textStudent.value;
  let html = "";
  let lastIndex = 0;

  // Tri des fautes par position
  const sortedMistakes = [...result.value.mistakes].sort((a, b) => a.position_index - b.position_index);

  sortedMistakes.forEach(mistake => {
    // Partie valide avant la faute
    html += original.substring(lastIndex, mistake.position_index);
    
    // Le mot fautif
    const mistakeContent = original.substring(mistake.position_index, mistake.position_index + mistake.length);
    const colorClass = `mistake-${mistake.type_rousseau}`; 
    
    html += `<span class="mistake ${colorClass}" title="${mistake.message}">${mistakeContent}</span>`;
    
    lastIndex = mistake.position_index + mistake.length;
  });

  // Reste du texte
  html += original.substring(lastIndex);
  
  return html.replace(/\n/g, '<br>');
});

const submitCorrection = async () => {
  if (!textStudent.value) return;
  
  isSubmitting.value = true;
  try {
    const payload = {
      student_id: 1, // À dynamiser plus tard
      dictation_id: 999, 
      assessment_type: "Initiale",
      content_student: textStudent.value
    };
    const response = await api.submitDictation(payload);
    result.value = response.data;
  } catch (e) {
    console.error(e);
    alert("Erreur lors de la correction.");
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style>
/* CSS Global pour les éléments injectés via v-html */
.mistake { text-decoration: underline; cursor: help; font-weight: bold; padding: 0 2px; border-radius: 2px; }
.mistake-D { background-color: #ffcccb; color: #8b0000; }
.mistake-R { background-color: #add8e6; color: #00008b; }
.mistake-S { background-color: #90ee90; color: #006400; }
.mistake-A { background-color: #f0e68c; }

.text-display { 
  margin-top: 20px; border: 1px solid #ccc; padding: 20px; 
  font-family: 'Courier New', monospace; background: #fff; line-height: 1.6;
}
.text-input { width: 100%; padding: 10px; margin-bottom: 10px; }
.btn-primary { background-color: #42b883; color: white; border: none; padding: 10px 20px; cursor: pointer; font-size: 1rem; }
.btn-primary:disabled { background-color: #a8d5c2; }
.badge { padding: 2px 6px; border-radius: 4px; font-size: 0.8em; margin-right: 5px; color: white; font-weight: bold;}
/* Couleurs badges identiques aux surlignages mais plus foncées pour le texte */
.badge.mistake-D { background-color: #d32f2f; }
.badge.mistake-R { background-color: #1976d2; }
.badge.mistake-S { background-color: #388e3c; }
</style>