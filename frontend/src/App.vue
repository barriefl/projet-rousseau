<template>
  <div class="app-layout">
    <nav class="sidebar">
      <div class="logo">Projet <span>Rousseau</span></div>

      <div class="nav-group">
        <div class="nav-item emile-menu" :class="{ 'active': isRousseauOpen }">
          <RouterLink to="/" class="nav-link">
            <BarChart2 :size="20" />
            <span>Étude Rousseau</span>
          </RouterLink>
          <button class="toggle-btn" @click="toggleRousseauMenu">
            <ChevronDown :class="{ 'rotate': isRousseauOpen }" :size="16" />
          </button>
        </div>

        <div class="sub-nav" :class="{ 'open': isRousseauOpen }">
          <RouterLink to="/import-etude" class="sub-nav-item" active-class="active">
            <FileDown :size="16" /> Importer une étude
          </RouterLink>
          <RouterLink to="/import-resultats" class="sub-nav-item" active-class="active">
            <ClipboardList :size="16" /> Importer des résultats
          </RouterLink>
        </div>
      </div>

      <div class="nav-group">
        <div class="nav-item emile-menu" :class="{ 'active': isEmileOpen }">
          <RouterLink to="/emile" class="nav-link">
            <PenTool :size="20" />
            <span>É.M.I.L.E.</span>
          </RouterLink>
          <button class="toggle-btn" @click="toggleEmileMenu">
            <ChevronDown :class="{ 'rotate': isEmileOpen }" :size="16" />
          </button>
        </div>

        <div class="sub-nav" :class="{ 'open': isEmileOpen }">
          <RouterLink to="/gestion" class="sub-nav-item" active-class="active">
            <FolderEdit :size="16" /> Gestion des dictées
          </RouterLink>
          <RouterLink to="/analyse" class="sub-nav-item" active-class="active">
            <TrendingUp :size="16" /> Analyse des travaux
          </RouterLink>
          <RouterLink to="/regles" class="sub-nav-item" active-class="active">
            <Settings2 :size="16" /> Catégories & Règles
          </RouterLink>
        </div>
      </div>

      <div class="nav-separator"></div>

      <RouterLink to="/etudiants" class="nav-item" active-class="active">
        <div class="nav-link">
          <GraduationCap :size="20" />
          <span>Liste des Étudiants</span>
        </div>
      </RouterLink>

      <RouterLink to="/gestion-etudiants" class="nav-item" active-class="active">
        <div class="nav-link">
          <UserCog :size="20" />
          <span>Gestion des Étudiants</span>
        </div>
      </RouterLink>
    </nav>

    <main class="main-content">
      <RouterView />
    </main>

    <AppToast :show="ui.toast.show" :message="ui.toast.message" :type="ui.toast.type" @close="ui.toast.show = false" />

    <AppConfirm :show="ui.confirm.show" :title="ui.confirm.title" :message="ui.confirm.message"
      @resolve="ui.resolveConfirm" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useUiStore } from '@/stores/ui';
import AppToast from '@/components/common/AppToast.vue';
import AppConfirm from '@/components/common/AppConfirm.vue';
import {
  BarChart2, ChevronDown, FileDown, ClipboardList,
  PenTool, FolderEdit, TrendingUp, Settings2,
  GraduationCap, UserCog
} from 'lucide-vue-next';

const ui = useUiStore();

const isEmileOpen = ref(true);
const toggleEmileMenu = () => isEmileOpen.value = !isEmileOpen.value;

const isRousseauOpen = ref(true);
const toggleRousseauMenu = () => isRousseauOpen.value = !isRousseauOpen.value;
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
}

.sidebar {
  min-width: 280px;
  background-color: var(--primary);
  color: white;
  display: flex;
  flex-direction: column;
  padding: 20px;
  overflow-y: auto;
}

.logo {
  font-size: 1.4rem;
  font-weight: bold;
  margin-bottom: 30px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 15px;
}

.logo span {
  color: var(--accent);
}

.nav-group {
  margin-bottom: 10px;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  transition: all 0.2s;
  color: #ecf0f1;
  text-decoration: none;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  text-decoration: none;
  color: inherit;
}

.nav-item:hover,
.nav-item.active {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

.toggle-btn {
  background: none;
  border: none;
  color: #bdc3c7;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  transition: transform 0.3s;
}

.rotate {
  transform: rotate(180deg);
}

.sub-nav {
  display: none;
  flex-direction: column;
  margin-left: 22px;
  margin-top: 5px;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
}

.sub-nav.open {
  display: flex;
}

.sub-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 15px;
  font-size: 0.9rem;
  color: #bdc3c7;
  text-decoration: none;
  border-radius: 6px;
  margin: 2px 0;
}

.sub-nav-item:hover,
.sub-nav-item.active {
  color: var(--accent);
  background: rgba(255, 255, 255, 0.05);
}

.nav-separator {
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
  margin: 15px 0;
}

.main-content {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
  background: #f9fafb;
}
</style>