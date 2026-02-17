<template>
  <div class="dashboard-etude">
    <div class="header">
      <h1>Étude Rousseau : Analyses et Conclusions</h1>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>Outils (Var. Secondaire) vs Dictée (Var. Principale)</h3>
        <div class="fake-chart">Transfert des acquis / Écriture spontanée</div>
      </div>

      <div class="card">
        <h3>Performance Comparée : Projet Voltaire vs Ecri+</h3>
        <div class="fake-chart">Vérification de la non-infériorité de l'outil gratuit.</div>
      </div>

      <div class="card">
        <h3>Impact de l'Accompagnement Enseignant</h3>
        <div class="fake-chart">Autonomie vs Accompagnement humain.</div>
      </div>

      <div class="card">
        <h3>Poids des Variables Socioculturelles</h3>
        <div class="fake-chart">Corrélation lectures/milieu familial et performances.</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Les appels API et l'intégration de vue-chartjs se feront ici.
</script>

<style scoped>
.header { 
  margin-bottom: 20px; 
}
.header h1 { 
  font-size: 1.6rem; 
  color: var(--primary); 
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

.fake-chart { 
  height: 250px;
  background: repeating-linear-gradient(45deg, #f8f9fa, #f8f9fa 10px, #fff 10px, #fff 20px); 
  border: 1px dashed #ccc; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  color: #7f8c8d; 
  font-size: 0.9rem; 
  text-align: center; 
  padding: 10px;
  border-radius: 4px;
}
</style>