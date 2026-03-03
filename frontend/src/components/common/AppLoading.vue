<template>
    <div class="loading-container">
        <div class="loading-content">
            <Loader2 class="spinner" :size="40" />
            <p>{{ message }}</p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { Loader2 } from 'lucide-vue-next';
defineProps({
    message: {
        type: String,
        default: 'Chargement en cours...'
    }
});
</script>

<style scoped>
.loading-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
    background: white;
    border-radius: 8px;
    border: 1px solid #e1e8ed;
}

.loading-content {
    text-align: center;
    color: #7f8c8d;
}

.spinner {
    display: inline-block;
    color: var(--accent);
    font-size: 2rem;
    margin-bottom: 10px;
    animation: rotate 2s linear infinite;
}

@keyframes rotate {
    from {
        transform: rotate(0deg);
    }

    to {
        transform: rotate(360deg);
    }
}
</style>