<script setup lang="ts">
import { computed } from 'vue'

defineProps<{
  status: 'vacant' | 'occupied' | 'maintenance'
}>()

const classes = computed(() => {
  return {
    vacant: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    occupied: 'bg-amber-100 text-amber-900 border-amber-300',
    maintenance: 'bg-rose-100 text-rose-800 border-rose-300'
  }
})
</script>

<template>
  <span
    class="inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide"
    :class="classes[status]"
  >
    {{ status }}
  </span>
</template>
