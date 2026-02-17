<template>
  <div class="emile-gestion">
    <div class="header">
      <h1>Gestion des Dictées</h1>
    </div>

    <div class="grid-3">
      <div class="action-card" @click="router.push('/correction')">
        <i style="color: var(--primary);">👁️</i>
        <h3>Consulter une dictée</h3>
        <p>Consulter les corrections, les erreurs et le score d'un étudiant.</p>
      </div>

      <div class="action-card" @click="router.push('/import-dictee')">
        <i style="color: var(--accent);">📥</i>
        <h3>Importer une dictée</h3>
        <p>Ajouter et analyser le texte d'un étudiant.</p>
      </div>

      <div class="action-card" @click="router.push('/dictee-referente')">
        <i style="color: var(--warning);">⭐</i>
        <h3>Dictée Référente</h3>
        <p>Définir le texte parfait pour une session.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
const router = useRouter();
</script>

<style scoped>
.header { 
  margin-bottom: 20px; 
}
.header h1 { 
  font-size: 1.6rem; 
  color: var(--primary); 
}
.grid-3 { 
  display: grid; 
  grid-template-columns: repeat(3, 1fr); 
  gap: 20px; 
}

.action-card { 
  background: white; 
  border: 2px solid #e1e8ed; 
  border-radius: 10px; 
  padding: 30px 20px; 
  text-align: center; 
  cursor: pointer; 
  transition: 0.2s; 
  display: flex; 
  flex-direction: column; 
  align-items: center; 
  justify-content: center; 
  min-height: 200px;
}
.action-card:hover { 
  border-color: var(--accent); 
  transform: translateY(-3px); 
  box-shadow: 0 5px 15px rgba(0,0,0,0.05);
}
.action-card i { 
  font-size: 3rem; 
  margin-bottom: 15px; 
  font-style: normal; 
}
.action-card h3 { 
  color: var(--primary); 
  margin-bottom: 10px; 
}
.action-card p { 
  font-size: 0.9rem; 
  color: #7f8c8d; 
}
</style>