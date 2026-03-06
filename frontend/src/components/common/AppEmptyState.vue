<template>
    <div class="empty-state">
        <div class="empty-content">
            <SearchX :size="48" class="empty-icon" />
            <h3>{{ title }}</h3>
            <p>{{ message }}</p>

            <button v-if="showRetry" class="btn btn-outline btn-with-icon" :disabled="loading" @click="$emit('retry')">
                <RotateCcw :size="16" :class="{ 'animate-spin': loading }" />
                {{ loading ? 'Chargement...' : 'Réessayer' }}
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { SearchX, RotateCcw } from 'lucide-vue-next';

defineProps({
    title: { type: String, default: 'Aucune donnée trouvée' },
    message: { type: String, default: "Il n'y a rien à afficher pour le moment." },
    showRetry: { type: Boolean, default: false },
    loading: { type: Boolean, default: false }
});

defineEmits(['retry']);
</script>

<style scoped>
/* ==========================================================================
     STYLE EMPTY STATE.
     ========================================================================== */
h3 {
    margin: 0 0 10px 0;
    color: var(--primary);
    font-size: 1.2rem;
}

p {
    margin-bottom: 20px;
    max-width: 300px;
}

/* ==========================================================================
     ANIMATION LOADING.
     ========================================================================== */
.animate-spin {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from {
        transform: rotate(0deg);
    }

    to {
        transform: rotate(360deg);
    }
}
</style>