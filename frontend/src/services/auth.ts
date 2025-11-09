import api from '../api/client'

const TOKEN_KEY = 'litea_auth_token'
const USERNAME_KEY = 'litea_username'

class AuthService {
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
  
  initAuth() {
    const token = this.getToken()
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
  }
}

export const authService = new AuthService()
