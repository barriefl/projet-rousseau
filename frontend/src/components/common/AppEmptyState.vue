<template>
    <div class="empty-state">
        <div class="empty-content">
            <SearchX :size="48" class="empty-icon" />
            <h3>{{ title }}</h3>
            <p>{{ message }}</p>

            <button v-if="showRetry" class="btn btn-outline btn-with-icon" @click="$emit('retry')">
                <RotateCcw :size="16" />
                Réessayer
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { SearchX } from 'lucide-vue-next';

defineProps({
    title: { type: String, default: 'Aucune donnée trouvée' },
    message: { type: String, default: "Il n'y a rien à afficher pour le moment." },
    showRetry: { type: Boolean, default: false }
});

defineEmits(['retry']);
</script>

<style scoped>
.empty-state {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
    background: white;
    border-radius: 8px;
    border: 1px solid #e1e8ed;
}

.empty-content {
    text-align: center;
    color: #7f8c8d;
}

.empty-icon {
    margin: 0 auto 15px;
    color: #bdc3c7;
    display: block;
}

h3 {
    margin: 0 0 10px 0;
    color: var(--primary);
    font-size: 1.2rem;
}

p {
    margin-bottom: 20px;
    max-width: 300px;
}

.btn-with-icon {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    justify-content: center;
    margin: 0 auto;
}

.btn-outline {
    background: transparent;
    border: 1px solid #dcdde1;
    color: var(--text);
    padding: 8px 20px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 500;
}

.btn-outline:hover {
    background: #f8f9fa;
    border-color: var(--accent);
    color: var(--accent);
}
</style>