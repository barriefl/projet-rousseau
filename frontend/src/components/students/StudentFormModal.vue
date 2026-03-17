<template>
    <Transition name="modal-scale">
        <div class="modal-overlay" v-if="show" @click.self="$emit('close')">
            <div class="modal-container">

                <header class="modal-header">
                    <div class="header-main">
                        <div class="header-icon" :class="isEdit ? 'edit-mode' : 'create-mode'">
                            <UserPlus v-if="!isEdit" :size="24" />
                            <GraduationCap v-else :size="24" />
                        </div>
                        <div>
                            <h2>{{ isEdit ? 'Modifier le profil' : 'Nouvel Étudiant' }}</h2>
                            <p class="subtitle">Analyse socioculturelle et académique</p>
                        </div>
                    </div>
                    <button class="close-x" @click="$emit('close')">
                        <X :size="20" />
                    </button>
                </header>

                <div class="modal-body">
                    <section class="content-card">
                        <div class="card-title">
                            <Fingerprint :size="16" /> <span>Identité</span>
                        </div>
                        <div class="input-grid">
                            <div class="field">
                                <label>Nom <span class="req">*</span></label>
                                <input class="form-control" type="text" v-model="form.last_name" placeholder="ROUSSEAU">
                            </div>
                            <div class="field">
                                <label>Prénom <span class="req">*</span></label>
                                <input class="form-control" type="text" v-model="form.first_name"
                                    placeholder="Jean-Jacques">
                            </div>
                            <div class="field">
                                <label>Promotion</label>
                                <select class="form-control" v-model="form.promotion_id" :disabled="!!lockPromotionId">
                                    <option v-for="promo in promotions" :key="promo.id" :value="promo.id">{{ promo.name
                                    }}</option>
                                </select>
                            </div>
                            <div class="field">
                                <label>Groupe</label>
                                <select class="form-control" v-model="form.group_id">
                                    <option :value="null">-- Non assigné --</option>
                                    <option v-for="grp in groups" :key="grp.id" :value="grp.id">{{ grp.name }}</option>
                                </select>
                            </div>
                            <div class="field">
                                <label>Outil utilisé</label>
                                <select class="form-control" v-model="form.tool_id">
                                    <option :value="null">-- Aucun --</option>
                                    <option v-for="t in tools" :key="t.id" :value="t.id">
                                        {{ t.full_name }}
                                    </option>
                                </select>
                            </div>
                        </div>
                    </section>

                    <section class="content-card">
                        <div class="card-title">
                            <BookOpen :size="16" /> <span>Habitudes de lecture</span>
                        </div>
                        <div class="input-grid">
                            <div class="field">
                                <label>Niveau d'appétence (1-4)</label>
                                <input class="form-control" type="number" v-model="form.appetence_level" min="1"
                                    max="4">
                            </div>
                            <div class="field">
                                <label>Bibliothèque à domicile ?</label>
                                <select class="form-control" v-model="form.has_library">
                                    <option value="">-- Sélectionner --</option>
                                    <option v-for="val in (Object.values(Library) as string[])" :key="val" :value="val">
                                        {{ val }}</option>
                                </select>
                            </div>
                            <div class="field full">
                                <label>Support favori</label>
                                <select class="form-control" v-model="form.reading_support">
                                    <option value="">-- Sélectionner un support --</option>
                                    <option v-for="val in (Object.values(ReadingSupport) as string[])" :key="val"
                                        :value="val">{{ val }}</option>
                                </select>
                            </div>
                        </div>

                        <div class="complex-field">
                            <label>Œuvres lues régulièrement</label>
                            <div class="selection-grid">
                                <label v-for="work in readingWorksOptions" :key="work" class="pill"
                                    :class="{ active: selectedReadingWorks.includes(work) }">
                                    <input class="form-control" type="checkbox" :value="work"
                                        v-model="selectedReadingWorks">
                                    <span>{{ work }}</span>
                                </label>
                            </div>
                        </div>

                        <div class="complex-field">
                            <label>Motifs de lecture</label>
                            <div class="selection-grid">
                                <label v-for="motive in motiveOptions" :key="motive" class="pill"
                                    :class="{ active: selectedMotives.includes(motive) }">
                                    <input class="form-control" type="checkbox" :value="motive"
                                        v-model="selectedMotives">
                                    <span>{{ motive }}</span>
                                </label>
                            </div>
                        </div>

                        <div class="complex-field">
                            <div class="card-title" style="margin-left: 0; margin-top: 10px;">
                                <Users :size="16" /> <span>Maîtrise de grammaire auto-déclarée</span>
                            </div>
                            <div class="segment-container">
                                <label v-for="level in declaredLevelOptions" :key="level" class="segment">
                                    <input class="form-control" type="radio" :value="level"
                                        v-model="form.declared_level">
                                    <div class="segment-box">{{ level }}</div>
                                </label>
                            </div>
                        </div>
                    </section>

                    <section class="content-card">
                        <div class="card-title">
                            <Users :size="16" /> <span>Environnement Familial</span>
                        </div>
                        <div class="parents-grid">
                            <div class="parent-subcard" v-for="p in [1, 2]" :key="p">
                                <div class="badge">Parent {{ p }}</div>
                                <div class="field">
                                    <label>Diplôme</label>
                                    <select class="form-control" v-model="form[`parent_${p}_degree` as keyof Student]">
                                        <option value="">-- Sélectionner --</option>
                                        <option v-for="v in (Object.values(Degree) as string[])" :key="v" :value="v">
                                            {{ v }}</option>
                                    </select>
                                </div>
                                <div class="field">
                                    <label>CSP</label>
                                    <select class="form-control" v-model="form[`parent_${p}_csp` as keyof Student]">
                                        <option value="">-- Sélectionner --</option>
                                        <option v-for="v in (Object.values(CSP) as string[])" :key="v" :value="v">{{ v
                                            }}
                                        </option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </section>
                </div>

                <footer class="modal-footer">
                    <button class="btn-text" @click="$emit('close')">Annuler</button>
                    <button class="btn-submit" @click="handleSave" :disabled="!form.first_name || !form.last_name">
                        <Save :size="18" />
                        <span>{{ isEdit ? 'Sauvegarder' : 'Créer l\'étudiant' }}</span>
                    </button>
                </footer>

            </div>
        </div>
    </Transition>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import {
    X, Save, UserPlus, BookOpen, GraduationCap,
    Library as Users, Fingerprint
} from 'lucide-vue-next';
import { CSP, Degree, Library, ReadingSupport } from '@/types/generated_enums';
import type { Student, Promotion, Group, Tool } from '@/types';

const props = defineProps<{
    show: boolean;
    studentData: Student | null;
    promotions: Promotion[];
    groups: Group[];
    tools: Tool[];
    isEdit?: boolean;
    lockPromotionId?: number | null;
}>();

const emit = defineEmits(['close', 'save']);

const form = ref<Partial<Student>>({ ...props.studentData });
const selectedReadingWorks = ref<string[]>([]);
const selectedMotives = ref<string[]>([]);

const readingWorksOptions = [
    "Romans / écrits littéraires", "Mangas / BD", "Livres de jeux, devinettes et énigmes",
    "Textes religieux et spirituels", "Presse / revues / articles", "Poésies, poèmes",
    "Réseaux sociaux", "Cours / livres éducatifs",
    "Ecrits publicitaires et marketing / modes d'emploi", "Autres livres"
];
const motiveOptions = ["Apprentissage", "Distraction", "Information"];
const declaredLevelOptions = ["Mauvais", "2", "3", "4", "5", "Excellent"];

watch(() => props.show, (isShown) => {
    if (isShown) {
        form.value = { ...props.studentData };
        if (props.lockPromotionId) form.value.promotion_id = props.lockPromotionId;
        selectedReadingWorks.value = form.value.reading_works ? form.value.reading_works.split(';').filter(Boolean) : [];
        selectedMotives.value = form.value.motive ? form.value.motive.split(';').filter(Boolean) : [];
    }
});

const handleSave = () => {
    const payload = {
        ...form.value,
        reading_works: selectedReadingWorks.value.join(';'),
        motive: selectedMotives.value.join(';'),
        promotion_id: form.value.promotion_id || null,
        group_id: form.value.group_id || null,
        tool_id: form.value.tool_id || null,
        appetence_level: form.value.appetence_level ? String(form.value.appetence_level) : null
    };
    emit('save', payload);
};
</script>

<style scoped>
/* ==========================================================================
     STYLE MODAL.
     ========================================================================== */
.modal-container {
    background: #f8fafc;
    border-radius: 24px;
    width: 900px;
    max-width: 95vw;
    display: flex;
    flex-direction: column;
    max-height: 90vh;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4);
    overflow: hidden;
}

.modal-header {
    padding: 24px 32px;
    background: white;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-main {
    display: flex;
    align-items: center;
    gap: 16px;
}

.header-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.create-mode {
    background: #f0fdf4;
    color: #16a34a;
}

.edit-mode {
    background: #eff6ff;
    color: #2563eb;
}

.header-main h2 {
    margin: 0;
    font-size: 1.25rem;
    color: #0f172a;
    font-weight: 800;
}

.subtitle {
    margin: 2px 0 0;
    font-size: 0.85rem;
    color: #64748b;
}

.close-x {
    background: #f1f5f9;
    border: none;
    padding: 8px;
    border-radius: 50%;
    cursor: pointer;
    transition: 0.2s;
}

.modal-body {
    padding: 32px;
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* ==========================================================================
     CARTES.
     ========================================================================== */
.content-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    border: 1px solid #e2e8f0;
}

.card-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 800;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    margin-bottom: 20px;
}

/* ==========================================================================
     PILL.
     ========================================================================== */
.pill {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    cursor: pointer;
    font-size: 0.8rem;
    transition: 0.2s;
}

.pill input {
    margin: 0;
    padding: 0;
    width: 16px;
    height: 16px;
    flex-shrink: 0;
    cursor: pointer;
    accent-color: #14b8a6;
}

.pill span {
    line-height: 1;
    margin-top: 1px;
}

.selection-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 8px;
}

.pill.active {
    background: #f0fdfa;
    border-color: #5eead4;
    color: #0d9488;
}

/* ==========================================================================
     INPUTS.
     ========================================================================== */
.input-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.input-grid .full {
    grid-column: span 2;
}

.field label {
    display: block;
    font-size: 0.8rem;
    font-weight: 700;
    color: #334155;
    margin-bottom: 6px;
}

.req {
    color: #ef4444;
}

input[type="text"],
input[type="number"],
select {
    width: 100%;
    padding: 10px 14px;
    border-radius: 10px;
    border: 1px solid #cbd5e1;
    background: #fff;
    font-size: 0.9rem;
}

.complex-field {
    margin-top: 24px;
}

.complex-field>label {
    display: block;
    margin-bottom: 12px;
    font-weight: 700;
    font-size: 0.8rem;
    color: #1e293b;
}

.segment-container {
    display: flex;
    background: #f1f5f9;
    padding: 4px;
    border-radius: 12px;
    gap: 4px;
}

.segment {
    flex: 1;
    cursor: pointer;
}

.segment input {
    display: none;
}

.segment-box {
    padding: 8px;
    text-align: center;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 700;
    color: #64748b;
}

.segment input:checked+.segment-box {
    border-color: #5eead4;
    color: #0d9488;
    background: #f0fdfa;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.parents-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}

.parent-subcard {
    background: #f8fafc;
    border: 1px dashed #cbd5e1;
    padding: 24px;
    border-radius: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    position: relative;
}

.badge {
    position: absolute;
    top: -10px;
    left: 16px;
    background: #1e293b;
    color: white;
    font-size: 0.65rem;
    font-weight: 900;
    padding: 2px 10px;
    border-radius: 6px;
}

.modal-footer {
    padding: 20px 32px;
    background: white;
    border-top: 1px solid #e2e8f0;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
}

/* ==========================================================================
     BOUTONS.
     ========================================================================== */
.btn-text {
    background: transparent;
    border: none;
    font-weight: 700;
    color: #64748b;
    cursor: pointer;
}

.btn-submit {
    background: #0f172a;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 12px;
    font-weight: 700;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: 0.2s;
}

.btn-submit:hover:not(:disabled) {
    background: #1e293b;
    transform: translateY(-1px);
}

/* ==========================================================================
     TRANSITIONS.
     ========================================================================== */
.modal-scale-enter-active,
.modal-scale-leave-active {
    transition: all 0.3s ease;
}

.modal-scale-enter-from,
.modal-scale-leave-to {
    opacity: 0;
    transform: scale(0.98);
}
</style>