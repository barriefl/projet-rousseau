<template>
  <div class="emile-analyse">
    <div class="header">
      <h1>Analyse des Travaux (Progression)</h1>
    </div>
    
    <table>
      <thead>
        <tr>
          <th>Étudiant</th>
          <th>Groupe</th>
          <th>Score Dictée Initiale</th>
          <th>Score Dictée Finale</th>
          <th>Progrès (Final - Initial)</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Dupont, Jean</strong></td>
          <td>G1 (Auto)</td>
          <td>12.5 pts</td>
          <td>8.0 pts</td>
          <td class="progress-positive">- 4.5 pts (Amélioration)</td>
        </tr>
        <tr>
          <td><strong>Martin, Sophie</strong></td>
          <td>G2 (Jalons)</td>
          <td>9.0 pts</td>
          <td>9.5 pts</td>
          <td class="progress-negative">+ 0.5 pts (Régression)</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
// Appel API pour lister les étudiants ici.
</script>

<style scoped>
.header { 
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
    margin-bottom: 20px; 
}
.header h1 { 
    font-size: 1.6rem; 
    color: var(--primary); 
}

table { 
  width: 100%; 
  border-collapse: collapse; 
  background: white; 
  border-radius: 8px; 
  overflow: hidden; 
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
th, td { 
  padding: 12px 15px; 
  text-align: left; 
  border-bottom: 1px solid #eee; 
  font-size: 0.95rem; 
  vertical-align: middle;
}
th { 
    background-color: var(--light); 
    color: var(--secondary); 
    font-weight: 600;
}
tr:hover { 
    background-color: #fcfcfc; 
}

.progress-positive { 
    color: #27ae60; 
    font-weight: bold; 
}
.progress-negative { 
    color: var(--danger); 
    font-weight: bold; 
}
</style>