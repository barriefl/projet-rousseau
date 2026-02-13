<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app-container">
    <header>
      <div class="logo">Projet Rousseau</div>
      <nav>
        <RouterLink to="/">📊 Dashboard</RouterLink>
        <RouterLink to="/correction">✍️ Correction</RouterLink>
      </nav>
    </header>

    <main>
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background-color: #fff;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.logo {
  font-weight: 900;
  font-size: 1.2rem;
  color: #2c3e50;
}

nav a {
  margin-left: 20px;
  text-decoration: none;
  color: #57606a;
  font-weight: 500;
  transition: color 0.2s;
}

nav a:hover {
  color: #42b883; /* Vert Vue.js */
}

nav a.router-link-active {
  color: #42b883;
  font-weight: bold;
}

main {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}
</style>