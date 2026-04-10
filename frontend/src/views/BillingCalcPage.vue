<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiClient } from '../utils/api'
import { authStore } from '../stores/auth'

type Room = {
  id: number
  room_number: string
  rent_rate?: number
  status: 'vacant' | 'occupied' | 'maintenance'
}

type Reading = {
  room_id: number
  billing_month: string
  water_value: string | number
  electric_value: string | number
}

type Config = {
  water_rate: string | number
  electric_rate: string | number
  garbage_fee: string | number
  late_fee: string | number
}

const rooms = ref<Room[]>([])
const config = ref<Config | null>(null)
const editRates = ref({
  water_rate: '',
  electric_rate: '',
  garbage_fee: '',
  late_fee: ''
})
const showRateEdit = ref(false)
const selectedMonth = ref('')
const selectedRooms = ref<Record<number, boolean>>({})
const lateFees = ref<Record<number, boolean>>({})
const readingsByRoom = ref<Record<number, Reading[]>>({})
const error = ref('')
const loading = ref(false)
const saving = ref(false)
const saveMessage = ref('')

const canAccess = computed(() => {
  const role = authStore.user.value?.role
  return role === 'admin' || role === 'staff'
})
const isAdmin = computed(() => authStore.user.value?.role === 'admin')

const prevMonthKey = (month: string) => {
  const [y, m] = month.split('-').map(Number)
  if (!y || !m) return ''
  if (m === 1) return `${y - 1}-12`
  return `${y}-${String(m - 1).padStart(2, '0')}`
}

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    rooms.value = await apiClient.get<Room[]>('/rooms')
    config.value = await apiClient.get<Config>('/billing/config')
    if (config.value) {
      editRates.value = {
        water_rate: String(config.value.water_rate ?? ''),
        electric_rate: String(config.value.electric_rate ?? ''),
        garbage_fee: String(config.value.garbage_fee ?? ''),
        late_fee: String(config.value.late_fee ?? '')
      }
    }
  } catch (err) {
    error.value = 'Failed to load rooms/config.'
  } finally {
    loading.value = false
  }
}

const saveRates = async () => {
  if (!config.value) return
  try {
    await apiClient.put('/billing/config', {
      water_rate: Number(editRates.value.water_rate || 0),
      electric_rate: Number(editRates.value.electric_rate || 0),
      garbage_fee: Number(editRates.value.garbage_fee || 0),
      late_fee: Number(editRates.value.late_fee || 0)
    })
    await loadData()
    showRateEdit.value = false
  } catch (err) {
    error.value = 'Failed to update rates.'
  }
}

const loadReadingsForMonth = async () => {
  if (!selectedMonth.value) return
  const year = Number(selectedMonth.value.split('-')[0])
  const prevYear = Number(prevMonthKey(selectedMonth.value).split('-')[0])
  const uniqueYears = Array.from(new Set([year, prevYear]))

  const results = await Promise.all(
    rooms.value.map(async (room) => {
      const yearly = await Promise.all(
        uniqueYears.map((y) =>
          apiClient.get<Reading[]>(`/billing/readings/year?room_id=${room.id}&year=${y}`)
        )
      )
      const merged = yearly.flat()
      return [room.id, merged] as const
    })
  )
  readingsByRoom.value = Object.fromEntries(results)
}

const selectAll = (checked: boolean) => {
  for (const room of rooms.value) {
    selectedRooms.value[room.id] = checked && room.status !== 'vacant'
  }
}

const waterOverrides = ref<Record<number, string>>({})
const electricOverrides = ref<Record<number, string>>({})

const roomRows = computed(() => {
  if (!config.value || !selectedMonth.value) return []
  const prevKey = prevMonthKey(selectedMonth.value)
  const waterRate = Number(config.value.water_rate || 0)
  const electricRate = Number(config.value.electric_rate || 0)
  const garbage = Number(config.value.garbage_fee || 0)
  const lateFee = Number(config.value.late_fee || 0)

  return rooms.value.map((room) => {
    const readings = readingsByRoom.value[room.id] || []
    const current = readings.find((r) => r.billing_month === selectedMonth.value)
    const previous = readings.find((r) => r.billing_month === prevKey)
    const calcWater = Number(current?.water_value || 0) - Number(previous?.water_value || 0)
    const calcElectric = Number(current?.electric_value || 0) - Number(previous?.electric_value || 0)
    const overrideWater = waterOverrides.value[room.id]
    const overrideElectric = electricOverrides.value[room.id]
    const waterUnits = overrideWater !== undefined && overrideWater !== ''
      ? Number(overrideWater)
      : calcWater
    const electricUnits = overrideElectric !== undefined && overrideElectric !== ''
      ? Number(overrideElectric)
      : calcElectric
    const rent = Number(room.rent_rate || 0)
    const waterAmount = Math.max(0, waterUnits) * waterRate
    const electricAmount = Math.max(0, electricUnits) * electricRate
    const late = lateFees.value[room.id] ? lateFee : 0
    const total = rent + waterAmount + electricAmount + garbage + late

    return {
      ...room,
      waterUnits: Math.max(0, waterUnits),
      electricUnits: Math.max(0, electricUnits),
      waterAmount,
      electricAmount,
      garbage,
      late,
      total
    }
  })
})

const grandTotal = computed(() => {
  return roomRows.value.reduce((sum, room) => {
    if (selectedRooms.value[room.id]) return sum + room.total
    return sum
  }, 0)
})

const saveBills = async () => {
  if (!selectedMonth.value) {
    error.value = 'Please select a month first.'
    return
  }
  const selected = roomRows.value.filter((room) => selectedRooms.value[room.id])
  if (!selected.length) {
    error.value = 'Please select at least one room.'
    return
  }
  saving.value = true
  error.value = ''
  saveMessage.value = ''
  try {
    const items = selected.map((room) => {
      const overrideWater = waterOverrides.value[room.id]
      const overrideElectric = electricOverrides.value[room.id]
      return {
        room_id: room.id,
        billing_month: selectedMonth.value,
        late_fee_applied: !!lateFees.value[room.id],
        water_units_override: overrideWater !== undefined && overrideWater !== '' ? Number(overrideWater) : null,
        electric_units_override: overrideElectric !== undefined && overrideElectric !== '' ? Number(overrideElectric) : null
      }
    })
    await apiClient.post('/billing/bills/bulk', { items })

    const bills = await Promise.all(
      selected.map(async (room) => {
        const result = await apiClient.get<any[]>(
          `/billing/bills?room_id=${room.id}&month=${selectedMonth.value}`
        )
        return result[0] || null
      })
    )
    const billIds = bills.filter(Boolean).map((bill: any) => bill.id)
    if (billIds.length) {
      const blob = await apiClient.postBlob('/receipts/bulk/pdf', { bill_ids: billIds })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `receipts-${selectedMonth.value}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    }
    saveMessage.value = 'Saved bills and generated receipts.'
  } catch (err) {
    error.value = 'Failed to save bills or generate receipts.'
  } finally {
    saving.value = false
  }
}

const exportBills = async () => {
  if (!selectedMonth.value) {
    error.value = 'Please select a month first.'
    return
  }
  try {
    const blob = await apiClient.getBlob(`/reports/bills/export?month=${selectedMonth.value}`)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `bills-${selectedMonth.value}.xlsx`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } catch (err) {
    error.value = 'Failed to export bills.'
  }
}

onMounted(async () => {
  await loadData()
})
</script>

<template>
  <section class="grid gap-4">
    <header class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-semibold">Rent Calculation</h1>
        <p class="text-sm text-slate-500">Admin and staff only.</p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <div v-if="config" class="flex items-center gap-2 text-xs text-slate-600">
          Water: {{ Number(config.water_rate) }} /unit · Electric: {{ Number(config.electric_rate) }} /unit
          <button
            v-if="isAdmin"
            class="rounded-full border border-slate-200 px-2 py-1 text-[11px] font-semibold text-slate-700"
            @click="showRateEdit = !showRateEdit"
          >
            Edit
          </button>
        </div>
        <input
          v-model="selectedMonth"
          type="month"
          class="rounded-xl border border-slate-200 px-3 py-2 text-sm"
          @change="loadReadingsForMonth"
        />
        <button
          class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
          :disabled="saving"
          @click="saveBills"
        >
          Save & Print
        </button>
        <button
          class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700"
          @click="exportBills"
        >
          Export Bills
        </button>
        <button
          class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700"
          @click="selectAll(true)"
        >
          Select All
        </button>
        <button
          class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700"
          @click="selectAll(false)"
        >
          Clear
        </button>
      </div>
    </header>

    <div v-if="!canAccess" class="text-sm text-rose-600">You don’t have access to this page.</div>
    <div v-else>
      <div v-if="error" class="text-xs text-rose-600">{{ error }}</div>
      <div v-if="saveMessage" class="text-xs text-emerald-600">{{ saveMessage }}</div>
      <div v-if="loading" class="text-xs text-slate-500">Loading...</div>

      <div v-if="isAdmin && showRateEdit" class="fixed inset-0 z-10 grid place-items-center bg-slate-900/40">
        <div class="grid w-full max-w-lg gap-3 rounded-2xl bg-white p-6 shadow-xl">
          <div class="text-lg font-semibold text-slate-800">Edit Rates</div>
          <div class="grid gap-2 md:grid-cols-2">
            <label class="grid gap-1 text-xs font-semibold text-slate-600">
              Water / unit
              <input v-model="editRates.water_rate" type="number" class="rounded-xl border border-slate-200 px-3 py-2" />
            </label>
            <label class="grid gap-1 text-xs font-semibold text-slate-600">
              Electric / unit
              <input v-model="editRates.electric_rate" type="number" class="rounded-xl border border-slate-200 px-3 py-2" />
            </label>
            <label class="grid gap-1 text-xs font-semibold text-slate-600">
              Garbage fee
              <input v-model="editRates.garbage_fee" type="number" class="rounded-xl border border-slate-200 px-3 py-2" />
            </label>
            <label class="grid gap-1 text-xs font-semibold text-slate-600">
              Late fee
              <input v-model="editRates.late_fee" type="number" class="rounded-xl border border-slate-200 px-3 py-2" />
            </label>
          </div>
          <div class="flex gap-2">
            <button class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white" @click="saveRates">
              Save Rates
            </button>
            <button
              class="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
              @click="showRateEdit = false"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>

      <div class="overflow-auto rounded-2xl border border-slate-200 bg-white/80 shadow-sm">
        <table class="min-w-full text-sm">
          <thead class="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500">
            <tr>
              <th class="px-4 py-3">Select</th>
              <th class="px-4 py-3">Room</th>
              <th class="px-4 py-3">Water Units</th>
              <th class="px-4 py-3">Water Amount</th>
              <th class="px-4 py-3">Electric Units</th>
              <th class="px-4 py-3">Electric Amount</th>
              <th class="px-4 py-3">Override</th>
              <th class="px-4 py-3">Late Fee</th>
              <th class="px-4 py-3">Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="room in roomRows" :key="room.id" class="border-t border-slate-200">
              <td class="px-4 py-3">
                <input
                  type="checkbox"
                  v-model="selectedRooms[room.id]"
                  :disabled="room.status === 'vacant'"
                />
              </td>
              <td class="px-4 py-3 font-semibold text-slate-700">{{ room.room_number }}</td>
              <td class="px-4 py-3">{{ room.waterUnits }}</td>
              <td class="px-4 py-3">{{ room.waterAmount }}</td>
              <td class="px-4 py-3">{{ room.electricUnits }}</td>
              <td class="px-4 py-3">{{ room.electricAmount }}</td>
              <td class="px-4 py-3">
                <div class="grid gap-2">
                  <input
                    v-model="waterOverrides[room.id]"
                    type="number"
                    class="w-24 rounded-lg border border-slate-200 px-2 py-1"
                    placeholder="Water"
                    :disabled="room.status === 'vacant'"
                  />
                  <input
                    v-model="electricOverrides[room.id]"
                    type="number"
                    class="w-24 rounded-lg border border-slate-200 px-2 py-1"
                    placeholder="Electric"
                    :disabled="room.status === 'vacant'"
                  />
                </div>
              </td>
              <td class="px-4 py-3">
                <input
                  type="checkbox"
                  v-model="lateFees[room.id]"
                  :disabled="room.status === 'vacant'"
                />
              </td>
              <td class="px-4 py-3 font-semibold text-slate-800">
                {{ room.total }}
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="border-t border-slate-300 bg-slate-100">
              <td colspan="8" class="px-4 py-3 text-right font-semibold">Grand Total</td>
              <td class="px-4 py-3 font-semibold">{{ grandTotal }}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </section>
</template>
