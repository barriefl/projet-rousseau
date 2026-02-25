<template>
  <div class="app-layout">
    <nav class="sidebar">
      <div class="logo">Projet <span>Rousseau</span></div>
      
      <RouterLink to="/" class="nav-item" active-class="active">
        <div>📊 Étude Rousseau</div>
      </RouterLink>
      
      <div class="nav-item emile-menu" :class="{ 'active': isEmileOpen }">
        <RouterLink to="/emile" style="text-decoration: none; color: inherit; flex: 1;">
          <div>📝 É.M.I.L.E.</div>
        </RouterLink>
        <span style="font-size: 0.8rem; cursor: pointer; padding: 5px;" @click="toggleEmileMenu">
          {{ isEmileOpen ? '▲' : '▼' }}
        </span>
      </div>
      
      <div class="sub-nav" :class="{ 'open': isEmileOpen }">
        <RouterLink to="/gestion" class="sub-nav-item" active-class="active">📂 Gestion des dictées</RouterLink>
        <RouterLink to="/analyse" class="sub-nav-item" active-class="active">📈 Analyse des travaux</RouterLink>
        <RouterLink to="/regles" class="sub-nav-item" active-class="active">⚙️ Catégories & Règles</RouterLink>
      </div>

      <RouterLink to="/etudiants" class="nav-item" active-class="active">
        <div>🎓 Liste des Étudiants</div>
      </RouterLink>
    </nav>

    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { RouterLink, RouterView, useRoute } from 'vue-router';

const isEmileOpen = ref(true);

const toggleEmileMenu = () => {
  isEmileOpen.value = !isEmileOpen.value;
};
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
}

/* --- SIDEBAR. --- */
.sidebar { 
  min-width: 260px; 
  background-color: var(--primary); 
  color: white; 
  display: flex; 
  flex-direction: column; 
  padding: 20px; 
  z-index: 10; 
  overflow-y: auto;
}

.logo { 
  font-size: 1.4rem; 
  font-weight: bold; 
  margin-bottom: 30px; 
  border-bottom: 1px solid var(--secondary); 
  padding-bottom: 15px; 
}

.logo span { 
  color: var(--accent); 
}

.nav-item { 
  padding: 12px 15px; 
  cursor: pointer; 
  border-radius: 6px; 
  margin-bottom: 5px; 
  transition: 0.2s; 
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
  gap: 10px; 
  font-weight: 500;
  text-decoration: none;
  color: white;
}

.nav-item:hover, .nav-item.active { 
  background-color: var(--secondary); 
  border-left: 4px solid var(--accent); 
}

.emile-menu {
  user-select: none;
}

/* --- SOUS-MENU. --- */
.sub-nav { 
  display: none; 
  flex-direction: column; 
  margin-left: 15px; 
  margin-bottom: 10px; 
  border-left: 2px solid var(--secondary); 
  padding-left: 10px;
}

.sub-nav.open { 
  display: flex; 
}

.sub-nav-item { 
  padding: 10px 15px; 
  cursor: pointer; 
  border-radius: 6px; 
  margin-bottom: 2px; 
  transition: 0.2s; 
  font-size: 0.9rem; 
  color: #bdc3c7;
  text-decoration: none;
}

.sub-nav-item:hover, .sub-nav-item.active { 
  background-color: var(--secondary); 
  color: white;
}

/* --- CONTENU PRINCIPAL. --- */
.main-content { 
  flex: 1; 
  padding: 30px; 
  overflow-y: auto; 
  height: 100vh; 
  position: relative;
}
</style>