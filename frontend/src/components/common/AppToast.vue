<template>
    <Transition name="toast">
        <div v-if="show" class="toast-notification" :class="type">
            <CheckCircle v-if="type === 'success'" :size="20" />
            <AlertCircle v-else :size="20" />

            <span class="message">{{ message }}</span>

            <button class="close-btn" @click="$emit('close')">
                <X :size="16" />
            </button>
        </div>
    </Transition>
</template>

<script setup lang="ts">
import { CheckCircle, AlertCircle, X } from 'lucide-vue-next';

defineProps<{
    show: boolean;
    message: string;
    type: 'success' | 'error';
}>();

defineEmits(['close']);
</script>

<style scoped>
.toast-notification {
    position: fixed;
    top: 25px;
    right: 25px;
    padding: 16px 20px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 300px;
    max-width: 450px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    z-index: 10000;
    color: white;
}

.toast-notification.success {
    background: #10b981;
}

.toast-notification.error {
    background: #ef4444;
}

.message {
    flex: 1;
    font-weight: 500;
    font-size: 0.95rem;
}

.close-btn {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    border-radius: 4px;
    padding: 4px;
    cursor: pointer;
    display: flex;
    transition: 0.2s;
}

.close-btn:hover {
    background: rgba(255, 255, 255, 0.3);
}

.toast-enter-active,
.toast-leave-active {
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.toast-enter-from {
    transform: translateX(100%);
    opacity: 0;
}

.toast-leave-to {
    transform: translateX(50%);
    opacity: 0;
}
</style>