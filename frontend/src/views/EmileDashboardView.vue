<template>
  <div class="emile-dashboard">
    <div class="header">
      <h1>Tableau de Bord É.M.I.L.E.</h1>
    </div>
    
    <div class="grid-3">
      <div class="card">
        <h3>Total Étudiants Inscrits</h3>
        <div class="stat-val">342</div>
        <div class="stat-desc">Toutes promotions confondues</div>
      </div>
      
      <div class="card">
        <h3>Dictées Traitées</h3>
        <div class="stat-val">874</div>
        <div class="stat-desc">Analysées par LanguageTool</div>
      </div>
      
      <div class="card">
        <h3>Moyenne Globale (Malus)</h3>
        <div class="stat-val danger">6.4 pts</div>
        <div class="stat-desc">Amélioration de 1.2pt par rapport au S1</div>
      </div>
    </div>
    
    <div class="grid-2">
      <div class="card">
        <h3>Répartition par Groupes</h3>
        <div class="fake-chart">Graphique Camembert (Chart.js à venir)</div>
      </div>
      <div class="card">
        <h3>Erreurs fréquentes</h3>
        <div class="fake-chart">Top 3 des typologies (Chart.js à venir)</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Appeler l'API pour remplacer les nombres en dur (342, 874...) plus tard.
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
    gap: 20px; margin-bottom: 20px;
}
.grid-2 { 
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
}

.card { 
  background: white; 
  padding: 20px; 
  border-radius: 8px; 
  box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
  border: 1px solid #e1e8ed; 
}
.card h3 { 
  font-size: 1rem; 
  color: var(--primary); 
  margin-bottom: 15px; 
  border-bottom: 2px solid var(--light); 
  padding-bottom: 5px;
}

.stat-val { 
    font-size: 2rem; 
    font-weight: bold; 
    color: var(--accent); 
    margin-top: 10px;
}
.stat-val.danger { 
    color: var(--danger); 
}
.stat-desc { 
    font-size: 0.85rem; 
    color: #7f8c8d; 
}

.fake-chart { 
  height: 150px; 
  background: repeating-linear-gradient(45deg, #f8f9fa, #f8f9fa 10px, #fff 10px, #fff 20px); 
  border: 1px dashed #ccc; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  color: #7f8c8d; 
  font-size: 0.9rem; 
}
</style>