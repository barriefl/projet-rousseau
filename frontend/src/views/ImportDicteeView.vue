<template>
  <div class="import-view">
    <div class="header">
      <button class="btn btn-outline" @click="router.push('/gestion')">← Retour à la gestion</button>
      <h1>📥 Importer une dictée étudiant</h1>
    </div>

    <div class="form-card">
      <div class="grid-2">
        <div class="form-group">
          <label>1. Associer à un étudiant :</label>
          <select>
            <option value="">Sélectionner un étudiant...</option>
            <option>Dupont, Jean (G1)</option>
            <option>Martin, Sophie (G2)</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>2. Associer à une dictée référente :</label>
          <select>
            <option value="">-- Aucune (Analyse libre) --</option>
            <option>Dictée Initiale (Septembre)</option>
            <option>Dictée Finale (Novembre)</option>
          </select>
        </div>
      </div>

      <div class="form-group" style="margin-top: 25px;">
        <label>3. Source du texte :</label>
        
        <div class="upload-zone">
          <i>📄</i>
          <h3>Cliquez ou glissez-déposez un fichier .txt ici</h3>
          <p>Le fichier sera lu et son contenu inséré ci-dessous.</p>
          <input type="file" style="display: none;" accept=".txt">
        </div>
        
        <div class="separator"><span>OU</span></div>
        
        <textarea rows="8" placeholder="Saisissez ou collez le texte de l'étudiant ici..."></textarea>
      </div>
      
      <div class="actions">
        <button class="btn btn-primary btn-large">Lancer l'analyse LanguageTool 🚀</button>
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
    display: flex; 
    align-items: center; 
    gap: 20px; 
    margin-bottom: 30px; 
}
.header h1 { 
    font-size: 1.6rem; 
    color: var(--primary); 
    margin: 0; 
}

.form-card { 
  background: white; 
  padding: 40px; 
  border-radius: 12px; 
  box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
  border: 1px solid #e1e8ed;
  max-width: 900px;
}

.grid-2 { 
    display: grid; 
    grid-template-columns: 1fr 1fr; 
    gap: 20px; 
}

.form-group { 
    margin-bottom: 15px; 
}
.form-group label { 
    display: block; 
    margin-bottom: 8px; 
    font-size: 1rem; 
    font-weight: 600; 
    color: var(--primary); 
}
.form-group select, .form-group textarea { 
  width: 100%; 
  padding: 12px; 
  border: 2px solid #ecf0f1; 
  border-radius: 8px; 
  font-family: inherit; 
  font-size: 1rem; 
  transition: border-color 0.2s;
}
.form-group select:focus, .form-group textarea:focus { 
    border-color: var(--accent); 
    outline: none; 
}

.upload-zone { 
  border: 2px dashed #bdc3c7; 
  border-radius: 8px; 
  padding: 40px 20px; 
  text-align: center; 
  background: #f8f9fa; 
  cursor: pointer; 
  transition: 0.2s; 
}
.upload-zone:hover { 
    border-color: var(--accent); 
    background: #f0f8ff; 
}
.upload-zone i { 
    font-size: 3rem; 
    color: #bdc3c7; 
    margin-bottom: 10px; 
    display: block; 
    font-style: normal; 
}
.upload-zone h3 { 
    color: var(--primary); 
    margin-bottom: 5px; 
}
.upload-zone p { 
    color: #7f8c8d; 
    font-size: 0.9rem; 
}

.separator { 
    text-align: center; 
    margin: 25px 0; 
    position: relative; 
}
.separator::before { 
    content: ""; 
    position: absolute; 
    left: 0; 
    top: 50%; 
    width: 100%; 
    height: 1px; 
    background: #e1e8ed; 
    z-index: 1; 
}
.separator span { 
    background: white; 
    padding: 0 15px; 
    color: #7f8c8d; 
    font-weight: bold; 
    position: relative; 
    z-index: 2; 
}

.actions { display: flex; justify-content: flex-end; margin-top: 30px; }
.btn { padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; transition: 0.2s; border: none; }
.btn-large { padding: 12px 24px; font-size: 1.1rem; }
.btn-primary { background: var(--accent); color: white; }
.btn-primary:hover { background: #12876f; transform: translateY(-2px); }
.btn-outline { background: transparent; border: 1px solid #ccc; color: var(--text); }
.btn-outline:hover { background: #f8f9fa; border-color: var(--primary); }
</style>