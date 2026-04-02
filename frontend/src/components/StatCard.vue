<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  trend?: string
}>()
</script>

<template>
  <div class="grid gap-1 rounded-2xl border border-slate-200/60 bg-white/70 p-4 shadow-sm backdrop-blur">
    <div class="text-[11px] uppercase tracking-[0.18em] text-slate-500">{{ label }}</div>
    <div class="text-2xl font-semibold text-slate-900">{{ value }}</div>
    <div v-if="trend" class="text-xs font-semibold text-emerald-600">{{ trend }}</div>
  </div>
</template>
