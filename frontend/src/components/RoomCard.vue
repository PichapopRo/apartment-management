<script setup lang="ts">
import StatusPill from './StatusPill.vue'

type RoomStatus = 'vacant' | 'occupied' | 'maintenance'

defineProps<{
  roomNumber: string
  floor?: number
  rentRate?: number
  status: RoomStatus
  residentName?: string | null
  showDetails: boolean
  canEdit: boolean
}>()

const emit = defineEmits<{
  (e: 'edit'): void
  (e: 'assign'): void
  (e: 'upload'): void
  (e: 'view'): void
  (e: 'delete'): void
}>()
</script>

<template>
  <div class="grid gap-3 rounded-2xl border border-slate-200/70 bg-white/80 p-4 shadow-[0_10px_26px_rgba(15,23,42,0.08)]">
    <div class="flex items-center justify-between gap-3">
      <div>
        <div class="text-lg font-semibold">{{ roomNumber }}</div>
        <div v-if="showDetails" class="text-xs text-slate-500">
          Floor {{ floor ?? '-' }} · {{ rentRate?.toLocaleString() ?? '—' }} THB
        </div>
      </div>
      <StatusPill :status="status" />
    </div>

    <div v-if="showDetails" class="text-xs text-slate-600">
      Resident: <span class="font-semibold">{{ residentName || '—' }}</span>
    </div>

    <div v-if="showDetails" class="flex flex-wrap gap-2">
      <button
        v-if="canEdit"
        class="rounded-xl bg-slate-900 px-3 py-2 text-xs font-semibold text-white shadow-sm transition hover:-translate-y-0.5"
        @click="emit('edit')"
      >
        Edit Room
      </button>
      <button
        v-if="canEdit"
        class="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700 transition hover:-translate-y-0.5"
        @click="emit('delete')"
      >
        Delete
      </button>
      <button
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:-translate-y-0.5"
        @click="emit('assign')"
      >
        Assign Tenant
      </button>
      <button
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:-translate-y-0.5"
        @click="emit('upload')"
      >
        Upload Docs
      </button>
      <button
        class="rounded-xl border border-slate-200 bg-transparent px-3 py-2 text-xs font-semibold text-slate-700 transition hover:-translate-y-0.5"
        @click="emit('view')"
      >
        View Docs
      </button>
    </div>
  </div>
</template>
