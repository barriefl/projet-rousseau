<template>
    <div class="empty-state" style="min-height: 100vh; border: none; border-radius: 0;">
        <div class="card" style="width: 400px; max-width: 90%; margin: auto;">
            <h2 class="modal-header-title" style="text-align: center; margin-bottom: 5px;">Projet Rousseau</h2>
            <p style="text-align: center; color: var(--text-light); margin-bottom: 25px;">
                Accès restreint. Veuillez saisir la clé administrateur.
            </p>

            <form @submit.prevent="handleLogin">
                <div class="form-group">
                    <input v-model="password" type="password" class="form-control" placeholder="Mot de passe" required
                        autofocus />
                </div>

                <button type="submit" class="btn btn-primary"
                    style="width: 100%; justify-content: center; margin-top: 10px;" :disabled="isLoading">
                    <span v-if="isLoading">Vérification...</span>
                    <span v-else>Déverrouiller</span>
                </button>
            </form>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useUiStore } from '@/stores/ui'

const password = ref('')
const isLoading = ref(false)
const router = useRouter()
const ui = useUiStore()

const handleLogin = async () => {
    if (!password.value) return

    try {
        isLoading.value = true
        const res = await api.login(password.value)

        localStorage.setItem('access_token', res.access_token)

        ui.notify('Authentification réussie', 'success')
        router.push('/')

    } catch (error) {
        console.error('Erreur : ', error)
        ui.notify('Mot de passe incorrect.', 'error')
        password.value = ''
    } finally {
        isLoading.value = false
    }
}
</script>