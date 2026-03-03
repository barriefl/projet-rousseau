import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  // --- ÉTAT DU TOAST. ---
  const toast = ref({
    show: false,
    message: '',
    type: 'success' as 'success' | 'error',
  })

  const notify = (message: string, type: 'success' | 'error' = 'success') => {
    toast.value = { show: true, message, type }
    setTimeout(() => {
      toast.value.show = false
    }, 4000)
  }

  // --- ÉTAT DE LA CONFIRMATION. ---
  const confirm = ref({
    show: false,
    message: '',
    title: '',
    resolve: null as ((val: boolean) => void) | null,
  })

  const askConfirm = (message: string, title = 'Confirmation requise'): Promise<boolean> => {
    confirm.value.show = true
    confirm.value.message = message
    confirm.value.title = title

    return new Promise((res) => {
      confirm.value.resolve = res
    })
  }

  const resolveConfirm = (val: boolean) => {
    if (confirm.value.resolve) confirm.value.resolve(val)
    confirm.value.show = false
  }

  return { toast, notify, confirm, askConfirm, resolveConfirm }
})
