<template>
    <div class="empty-state" style="min-height: 100vh; border: none; border-radius: 0;">
        <div class="card" style="width: 500px; max-width: 90%; margin: auto; text-align: center; padding: 40px 20px;">

            <MapPinOff :size="64" style="color: var(--text-light, #6b7280); margin-bottom: 20px;" />

            <h1 class="modal-header-title" style="font-size: 2.5rem; margin-bottom: 10px;">404</h1>
            <h2 style="font-size: 1.2rem; margin-bottom: 15px;">Page introuvable</h2>

            <p style="color: var(--text-light, #6b7280); margin-bottom: 30px;">
                Oups ! Il semblerait que vous vous soyez égaré en chemin. La page que vous cherchez n'existe pas ou a
                été déplacée.
            </p>

            <button @click="goHome" class="btn btn-primary" style="justify-content: center; margin: 0 auto;">
                Retourner à l'accueil
            </button>

        </div>
    </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { MapPinOff } from 'lucide-vue-next'

const router = useRouter()

const goHome = () => {
    router.push('/')
}
</script>