<template>
  <div class="main-container">
    <div class="row justify-content-center">
      <div class="col-12 col-md-10 col-lg-8">
        <div class="auth-card">
          <div class="card-header text-center">
            <h2 class="mb-0">Welcome Back!</h2>
          </div>

          <div class="card-body">
            <!-- 用户类型切换 -->
            <div class="user-type-toggle mb-5">
              <button
                class="btn btn-lg"
                :class="userType === 'student' ? 'btn-primary' : 'btn-outline-primary'"
                @click="userType = 'student'"
              >
                Student Login
              </button>
              <button
                class="btn btn-lg"
                :class="userType === 'teacher' ? 'btn-primary' : 'btn-outline-primary'"
                @click="userType = 'teacher'"
              >
                Teacher Login
              </button>
            </div>

            <!-- 登录表单 -->
            <form @submit.prevent="handleLogin">
              <div class="mb-4">
                <label class="form-label fs-5">Username/Email</label>
                <input
                  type="text"
                  class="form-control form-control-lg"
                  v-model="credentials.identifier"
                  required
                  placeholder="Enter username or email"
                >
              </div>

              <div class="mb-5">
                <label class="form-label fs-5">Password</label>
                <input
                  type="password"
                  class="form-control form-control-lg"
                  v-model="credentials.password"
                  required
                  placeholder="Enter password"
                >
              </div>

              <button type="submit" class="btn btn-primary btn-lg w-100 mb-4">
                Sign In
              </button>

              <div class="text-center">
                <router-link to="/register" class="text-decoration-none">
                  Create New Account
                </router-link>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { useUserStore } from '@/stores/user'

export default {
  data() {
    return {
      userType: 'student',
      credentials: {
        identifier: '',
        password: ''
      }
    }
  },
  methods: {
    async handleLogin() {
      try {
        const response = await axios.post('/api/login', {
          user_type: this.userType,
          ...this.credentials
        })

        if (response.status === 200) {
          const userType = response.data.user_type; // 根据实际接口调整\
          const userStore = useUserStore()
          userStore.login(response.data.username, response.data.token,userType)
          localStorage.setItem('token', response.data.token); // 存储 token
          localStorage.setItem('userRole', userType);
          localStorage.setItem('username', response.data.username);

          const redirectPath = this.userType === 'student'
            ? '/student'
            : '/teacher'
          this.$router.push(redirectPath)
        }
      } catch (error) {
        alert(error.response?.data?.message || 'Login failed')
      }
    }
  }
}
</script>

<style scoped>
.user-type-toggle {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.btn-lg {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  transition: all 0.3s ease;
}

.form-control-lg {
  padding: 1rem;
  border-radius: 0.5rem;
}

.auth-card {
  margin: 3rem 0;
}
</style>
