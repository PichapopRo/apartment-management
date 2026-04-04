import { createRouter, createWebHistory } from 'vue-router'

import DashboardPage from './views/DashboardPage.vue'
import LoginPage from './views/LoginPage.vue'
import RegisterPage from './views/RegisterPage.vue'
import RoomsPage from './views/RoomsPage.vue'
import MeterPage from './views/MeterPage.vue'
import { authStore } from './stores/auth'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', component: LoginPage, meta: { public: true } },
  { path: '/register', component: RegisterPage, meta: { public: true } },
  { path: '/dashboard', component: DashboardPage },
  { path: '/rooms', component: RoomsPage },
  { path: '/meters', component: MeterPage }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  const isPublic = Boolean(to.meta.public)
  const hasToken = authStore.token.value

  if (!isPublic && !hasToken) {
    return '/login'
  }

  if (hasToken && !authStore.user.value) {
    try {
      await authStore.fetchMe()
    } catch {
      authStore.logout()
      return '/login'
    }
  }
})
