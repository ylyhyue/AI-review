import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    isLoggedIn: !!localStorage.getItem('token'),
    username: localStorage.getItem('username') || '',
    token: localStorage.getItem('token') || '',
    userRole: localStorage.getItem('userRole') || '' // 读取用户角色
  }),
  actions: {
    login(username, token, userRole) {
      this.isLoggedIn = true
      this.username = username
      this.token = token
      this.userRole = userRole
      // 存储到 localStorage
      localStorage.setItem('username', username)
      localStorage.setItem('token', token)
      localStorage.setItem('userRole', userRole) // 存储角色
    },
    logout() {
      this.isLoggedIn = false
      this.username = ''
      this.token = ''
      this.userRole = ''

      // 清除 localStorage
      localStorage.removeItem('username')
      localStorage.removeItem('token')
      localStorage.removeItem('userRole')
    }
  }
})
