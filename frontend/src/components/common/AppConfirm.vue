<template>
    <Transition name="fade">
        <div v-if="show" class="modal-overlay" @click.self="$emit('resolve', false)">
            <div class="confirm-modal">
                <div class="confirm-header">
                    <div class="warning-icon">
                        <AlertTriangle :size="32" />
                    </div>
                    <h3>{{ title || 'Confirmation requise' }}</h3>
                </div>

                <p class="confirm-body">{{ message }}</p>

                <div class="confirm-actions">
                    <button class="btn btn-outline" @click="$emit('resolve', false)">Annuler</button>
                    <button class="btn btn-danger" @click="$emit('resolve', true)">Confirmer</button>
                </div>
            </div>
        </div>
    </Transition>
</template>

<script setup lang="ts">
import { AlertTriangle } from 'lucide-vue-next';

defineProps<{
    show: boolean;
    message: string;
    title?: string;
}>();

defineEmits(['resolve']);
</script>

<style scoped>
/* ==========================================================================
   STYLE MODAL.
   ========================================================================== */
.confirm-modal {
    background: white;
    width: 100%;
    max-width: 450px;
    border-radius: 16px;
    padding: 30px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
}

.confirm-header {
    text-align: center;
    margin-bottom: 20px;
}

.warning-icon {
    background: #fff7ed;
    color: #f97316;
    width: 64px;
    height: 64px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 15px;
}

.confirm-header h3 {
    font-size: 1.25rem;
    color: #1e293b;
    margin: 0;
}

.confirm-body {
    color: #64748b;
    line-height: 1.6;
    text-align: center;
    margin-bottom: 30px;
}

.confirm-actions {
    display: flex;
    gap: 12px;
}

.confirm-actions button {
    flex: 1;
    padding: 12px;
}

/* ==========================================================================
   TRANSITION.
   ========================================================================== */
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>