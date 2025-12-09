import { createRouter, createWebHistory } from 'vue-router'
import { authService } from '@/services/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { title: '登录', requiresAuth: false }
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue'),
      meta: { title: '主页', requiresAuth: true }
    }
  ]
})

router.beforeEach(async (to, from, next) => {
  document.title = `${to.meta.title || 'Litea'} - Litea`
  
  const requiresAuth = to.meta.requiresAuth !== false
  
  // Check if authentication is enabled and user needs to login
  const needsLogin = await authService.needsLogin()
  
  if (requiresAuth && needsLogin) {
    // 需要认证但未登录，跳转到登录页
    next('/login')
  } else if (to.path === '/login' && !needsLogin) {
    // 已登录或认证禁用时访问登录页，跳转到首页
    next('/')
  } else {
    next()
  }
})

export default router
