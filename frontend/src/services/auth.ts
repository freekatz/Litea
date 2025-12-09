import api from '../api/client'

const TOKEN_KEY = 'litea_auth_token'
const USERNAME_KEY = 'litea_username'
const AUTH_ENABLED_KEY = 'litea_auth_enabled'

class AuthService {
  private authEnabled: boolean | null = null
  
  async login(username: string, password: string) {
    const response = await api.post('/auth/login', { username, password })
    const { access_token, username: user } = response.data
    
    // Save token and username
    localStorage.setItem(TOKEN_KEY, access_token)
    localStorage.setItem(USERNAME_KEY, user)
    
    // Set default auth header
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    
    return response.data
  }
  
  logout() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USERNAME_KEY)
    delete api.defaults.headers.common['Authorization']
  }
  
  getToken() {
    return localStorage.getItem(TOKEN_KEY)
  }
  
  getUsername() {
    return localStorage.getItem(USERNAME_KEY)
  }
  
  isAuthenticated() {
    return !!this.getToken()
  }
  
  async verify() {
    try {
      const response = await api.get('/auth/verify')
      return response.data.valid
    } catch (error) {
      return false
    }
  }
  
  /**
   * Check if authentication is enabled on the server
   */
  async checkAuthEnabled(): Promise<boolean> {
    // Use cached value if available
    if (this.authEnabled !== null) {
      return this.authEnabled
    }
    
    try {
      const response = await api.get('/auth/status')
      this.authEnabled = response.data.auth_enabled
      localStorage.setItem(AUTH_ENABLED_KEY, String(this.authEnabled))
      return this.authEnabled
    } catch (error) {
      // If we can't reach the server, assume auth is enabled for security
      return true
    }
  }
  
  /**
   * Check if user needs to login (auth enabled and not authenticated)
   */
  async needsLogin(): Promise<boolean> {
    const authEnabled = await this.checkAuthEnabled()
    if (!authEnabled) {
      return false
    }
    return !this.isAuthenticated()
  }
  
  initAuth() {
    const token = this.getToken()
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
    
    // Load cached auth enabled status
    const cachedAuthEnabled = localStorage.getItem(AUTH_ENABLED_KEY)
    if (cachedAuthEnabled !== null) {
      this.authEnabled = cachedAuthEnabled === 'true'
    }
  }
}

export const authService = new AuthService()
