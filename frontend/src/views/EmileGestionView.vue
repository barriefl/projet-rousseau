<template>
  <div class="emile-gestion">
    <div class="page-header">
      <h1>Gestion des Dictées</h1>
    </div>

    <div class="grid-3">
      <div class="action-card" @click="router.push('/correction')">
        <Eye :size="40" class="card-icon icon-primary" />
        <h3>Consulter une dictée</h3>
        <p>Consulter les corrections, les erreurs et le score d'un étudiant.</p>
      </div>

      <div class="action-card" @click="router.push('/import-dictee')">
        <FileUp :size="40" class="card-icon icon-accent" />
        <h3>Importer une dictée</h3>
        <p>Ajouter et analyser le texte d'un étudiant.</p>
      </div>

      <div class="action-card" @click="router.push('/dictee-referente')">
        <Star :size="40" class="card-icon icon-warning" />
        <h3>Dictée Référente</h3>
        <p>Définir le texte référent pour une session.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { Eye, FileUp, Star } from 'lucide-vue-next';

const router = useRouter();
</script>

<style scoped>
.action-card {
  background: white;
  padding: 30px;
  border-radius: 12px;
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.action-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.05);
  border-color: var(--accent);
}

.card-icon {
  margin: 0 auto 20px;
  display: block;
}

.icon-primary {
  color: var(--primary);
}

.icon-accent {
  color: var(--accent);
}

.icon-warning {
  color: var(--warning);
}

.action-card h3 {
  margin-bottom: 12px;
  color: var(--primary);
  font-size: 1.2rem;
}

.action-card p {
  color: #7f8c8d;
  font-size: 0.95rem;
  line-height: 1.5;
}
</style>