import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { authService } from './services/auth'
import './style.css'

// Initialize auth token from localStorage
authService.initAuth()

const app = createApp(App)
app.use(router)

app.mount('#app')
