<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import RoomCard from '../components/RoomCard.vue'
import { apiClient } from '../utils/api'
import { authStore } from '../stores/auth'

type Room = {
  id: number
  room_number: string
  floor?: number
  rent_rate?: number
  status: 'vacant' | 'occupied' | 'maintenance'
  current_resident_name?: string | null
  current_resident_phone?: string | null
  has_related?: boolean | null
  is_my_room?: boolean
}

const rooms = ref<Room[]>([])
const loading = ref(true)
const error = ref('')

const form = ref({
  id: 0,
  room_number: '',
  floor: 1,
  rent_rate: 0,
  status: 'vacant' as Room['status']
})

const assignForm = ref({
  room_id: '',
  resident_user_id: '',
  resident_name: '',
  tenant_phone: '',
  move_in_date: ''
})

const uploadForm = ref({
  room_id: '',
  citizen_id: null as File | null,
  contract: null as File | null
})

const showRoomModal = ref(false)
const showAssign = ref(false)
const showUpload = ref(false)
const showView = ref(false)
const viewRoomId = ref('')

const isAdmin = computed(() => authStore.user.value?.role === 'admin')
const isStaff = computed(() => authStore.user.value?.role === 'staff')
const isResident = computed(() => authStore.user.value?.role === 'resident')

const loadRooms = async () => {
  loading.value = true
  error.value = ''
  try {
    if (isResident.value) {
      const publicRooms = await apiClient.get<Array<{ room_number: string; status: Room['status']; is_my_room?: boolean }>>(
        '/rooms/public'
      )
      rooms.value = publicRooms.map((room, idx) => ({
        id: idx + 1,
        room_number: room.room_number,
        status: room.status,
        is_my_room: room.is_my_room
      }))
    } else {
      rooms.value = await apiClient.get<Room[]>('/rooms')
    }
  } catch (err) {
    error.value = 'Failed to load rooms.'
  } finally {
    loading.value = false
  }
}

onMounted(loadRooms)

const resetRoomForm = () => {
  form.value = { id: 0, room_number: '', floor: 1, rent_rate: 0, status: 'vacant', tenant_name: '', tenant_phone: '' }
}

const submitRoom = async () => {
  if (!form.value.room_number.trim()) return
  try {
    if (form.value.id) {
      const payload = {
        floor: form.value.floor,
        rent_rate: form.value.rent_rate,
        status: form.value.status
      }
      await apiClient.patch(`/rooms/${form.value.id}`, payload)

    } else {
      await apiClient.post('/rooms', form.value)
    }
    await loadRooms()
    resetRoomForm()
    showRoomModal.value = false
  } catch (err) {
    error.value = 'Failed to save room.'
  }
}

const openCreateRoom = () => {
  resetRoomForm()
  showRoomModal.value = true
}

const editRoom = (room: Room) => {
  form.value = {
    id: room.id,
    room_number: room.room_number,
    floor: room.floor ?? 1,
    rent_rate: room.rent_rate ?? 0,
    status: room.status
  }
  showRoomModal.value = true
}

const openAssign = (roomId: number) => {
  assignForm.value.room_id = String(roomId)
  showAssign.value = true
}

const openUpload = (roomId: number) => {
  uploadForm.value.room_id = String(roomId)
  showUpload.value = true
}

const openView = (roomId: number) => {
  viewRoomId.value = String(roomId)
  showView.value = true
}

const deleteRoom = async (room: Room) => {
  const hasRelated = Boolean(room.has_related)
  const message = hasRelated
    ? 'This room already has data (tenancies, documents, readings, or bills). Deleting it will remove all related records. Continue?'
    : 'Delete this room?'
  if (!confirm(message)) return
  try {
    const force = hasRelated ? '?force=true' : ''
    await apiClient.delete(`/rooms/${room.id}${force}`)
    await loadRooms()
  } catch (err) {
    error.value = 'Failed to delete room.'
  }
}

const viewDocument = async (type: 'citizen-id' | 'contract') => {
  try {
    const roomId = Number(viewRoomId.value)
    const blob = await apiClient.getBlob(`/rooms/${roomId}/documents/${type}`)
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
    setTimeout(() => URL.revokeObjectURL(url), 5000)
  } catch (err) {
    error.value = `No ${type.replace('-', ' ')} found for this room.`
  }
}

const submitAssign = async () => {
  try {
    if (!assignForm.value.move_in_date) {
      error.value = 'Move-in date is required.'
      return
    }
    const payload = {
      room_id: Number(assignForm.value.room_id),
      resident_user_id: assignForm.value.resident_user_id
        ? Number(assignForm.value.resident_user_id)
        : null,
      resident_name: assignForm.value.resident_name || null,
      tenant_phone: assignForm.value.tenant_phone || null,
      move_in_date: assignForm.value.move_in_date
    }
    await apiClient.post('/tenancies/assign', payload)
    showAssign.value = false
    assignForm.value = {
      room_id: '',
      resident_user_id: '',
      resident_name: '',
      tenant_phone: '',
      move_in_date: ''
    }
    await loadRooms()
  } catch (err) {
    error.value = 'Failed to assign tenancy.'
  }
}

const submitUpload = async () => {
  try {
    const roomId = Number(uploadForm.value.room_id)
    if (uploadForm.value.citizen_id) {
      const formData = new FormData()
      formData.append('file', uploadForm.value.citizen_id)
      await apiClient.postFile(`/rooms/${roomId}/documents/citizen-id`, formData)
    }
    if (uploadForm.value.contract) {
      const formData = new FormData()
      formData.append('file', uploadForm.value.contract)
      await apiClient.postFile(`/rooms/${roomId}/documents/contract`, formData)
    }
    showUpload.value = false
    uploadForm.value = { room_id: '', citizen_id: null, contract: null }
  } catch (err) {
    error.value = 'Failed to upload documents.'
  }
}
</script>

<template>
  <section class="grid gap-4">
    <header class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">Rooms</h1>
      <div class="flex items-center gap-3">
        <button
          v-if="isAdmin"
          class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
          @click="openCreateRoom"
        >
          Create Room
        </button>
      </div>
    </header>

    <div v-if="error" class="text-xs text-rose-600">{{ error }}</div>
    <div v-if="loading" class="text-xs text-slate-500">Loading rooms...</div>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      <RoomCard
        v-for="room in rooms"
        :key="room.id"
        :room-number="room.room_number"
        :floor="room.floor"
        :rent-rate="Number(room.rent_rate ?? 0)"
        :status="room.status"
        :resident-name="room.current_resident_name"
        :show-details="!isResident"
        :can-edit="isAdmin"
        :is-my-room="room.is_my_room"
        @edit="editRoom(room)"
        @delete="deleteRoom(room)"
        @assign="openAssign(room.id)"
        @upload="openUpload(room.id)"
        @view="openView(room.id)"
      />
    </div>

    <div v-if="isAdmin && showRoomModal" class="fixed inset-0 z-10 grid place-items-center bg-slate-900/40">
      <div class="grid w-full max-w-md gap-3 rounded-2xl bg-white p-6 shadow-xl">
        <h3 class="text-lg font-semibold">{{ form.id ? 'Edit room' : 'Create room' }}</h3>
        <form class="grid gap-3" @submit.prevent="submitRoom">
          <label class="grid gap-1 text-xs font-semibold text-slate-600">
            Room number
            <input v-model="form.room_number" class="rounded-xl border border-slate-200 px-3 py-2" />
          </label>
          <label class="grid gap-1 text-xs font-semibold text-slate-600">
            Floor
            <input v-model.number="form.floor" type="number" min="0" class="rounded-xl border border-slate-200 px-3 py-2" />
          </label>
          <label class="grid gap-1 text-xs font-semibold text-slate-600">
            Rent rate
            <input v-model.number="form.rent_rate" type="number" min="0" class="rounded-xl border border-slate-200 px-3 py-2" />
          </label>
          <label class="grid gap-1 text-xs font-semibold text-slate-600">
            Status
            <select v-model="form.status" class="rounded-xl border border-slate-200 px-3 py-2">
              <option value="vacant">Vacant</option>
              <option value="occupied">Occupied</option>
              <option value="maintenance">Maintenance</option>
            </select>
          </label>
          <div class="flex gap-2">
            <button type="submit" class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white">
              {{ form.id ? 'Update' : 'Create' }}
            </button>
            <button
              type="button"
              class="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
              @click="showRoomModal = false"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="(isAdmin || isStaff) && showAssign" class="fixed inset-0 z-10 grid place-items-center bg-slate-900/40">
      <div class="grid w-full max-w-md gap-3 rounded-2xl bg-white p-6 shadow-xl">
        <h3 class="text-lg font-semibold">Assign tenancy</h3>
        <form class="grid gap-3" @submit.prevent="submitAssign">
          <label class="grid gap-1 text-xs font-semibold text-slate-600">
            Room ID
            <input v-model="assignForm.room_id" readonly class="rounded-xl border border-slate-200 px-3 py-2" />
          </label>
          <label class="grid gap-1 text-xs font-semibold text-slate-600">
            Resident user ID (optional)
            <input v-model="assignForm.resident_user_id" class="rounded-xl border border-slate-200 px-3 py-2" />
          </label>
          <label class="grid gap-1 text-xs font-semibold text-slate-600">
            Resident name (optional)
            <input v-model="assignForm.resident_name" class="rounded-xl border border-slate-200 px-3 py-2" />
          </label>
          <label class="grid gap-1 text-xs font-semibold text-slate-600">
            Tenant phone (optional)
            <input v-model="assignForm.tenant_phone" class="rounded-xl border border-slate-200 px-3 py-2" />
          </label>
          <label class="grid gap-1 text-xs font-semibold text-slate-600">
            Move-in date
            <input v-model="assignForm.move_in_date" type="date" class="rounded-xl border border-slate-200 px-3 py-2" />
          </label>
          <div class="flex gap-2">
            <button type="submit" class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white">Assign</button>
            <button
              type="button"
              class="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
              @click="showAssign = false"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="(isAdmin || isStaff) && showUpload" class="fixed inset-0 z-10 grid place-items-center bg-slate-900/40">
      <div class="grid w-full max-w-md gap-3 rounded-2xl bg-white p-6 shadow-xl">
        <h3 class="text-lg font-semibold">Upload room documents</h3>
        <form class="grid gap-3" @submit.prevent="submitUpload">
          <label class="grid gap-1 text-xs font-semibold text-slate-600">
            Room ID
            <input v-model="uploadForm.room_id" readonly class="rounded-xl border border-slate-200 px-3 py-2" />
          </label>
          <label class="grid gap-1 text-xs font-semibold text-slate-600">
            Citizen ID
            <input type="file" @change="uploadForm.citizen_id = ($event.target as HTMLInputElement).files?.[0] || null" />
          </label>
          <label class="grid gap-1 text-xs font-semibold text-slate-600">
            Contract
            <input type="file" @change="uploadForm.contract = ($event.target as HTMLInputElement).files?.[0] || null" />
          </label>
          <div class="flex gap-2">
            <button type="submit" class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white">Upload</button>
            <button
              type="button"
              class="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
              @click="showUpload = false"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="(isAdmin || isStaff) && showView" class="fixed inset-0 z-10 grid place-items-center bg-slate-900/40">
      <div class="grid w-full max-w-md gap-3 rounded-2xl bg-white p-6 shadow-xl">
        <h3 class="text-lg font-semibold">View room documents</h3>
        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            @click="viewDocument('citizen-id')"
          >
            View Citizen ID
          </button>
          <button
            type="button"
            class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            @click="viewDocument('contract')"
          >
            View Contract
          </button>
          <button
            type="button"
            class="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
            @click="showView = false"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
