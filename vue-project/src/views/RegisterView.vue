<template>
  <div class="main-container">
    <div class="row justify-content-center">
      <div class="col-12 col-md-10 col-lg-8">
        <div class="auth-card">
          <div class="card-header text-center">
            <h2 class="mb-0">Create New Account</h2>
          </div>

          <div class="card-body">
            <div class="user-type-toggle mb-5">
              <button
                class="btn btn-lg"
                :class="userType === 'student' ? 'btn-primary' : 'btn-outline-primary'"
                @click="userType = 'student'"
              >
                Student Register
              </button>
              <button
                class="btn btn-lg"
                :class="userType === 'teacher' ? 'btn-primary' : 'btn-outline-primary'"
                @click="userType = 'teacher'"
              >
                Teacher Register
              </button>
            </div>

            <form @submit.prevent="handleRegister">
              <div class="mb-4">
                <label class="form-label fs-5">Username</label>
                <input
                  type="text"
                  class="form-control form-control-lg"
                  v-model.trim="formData.username"
                  required
                  placeholder="Enter username"
                >
              </div>

              <div class="mb-4">
                <label class="form-label fs-5">Email</label>
                <input
                  type="email"
                  class="form-control form-control-lg"
                  v-model.trim="formData.email"
                  required
                  placeholder="Enter email"
                  @blur="validateEmail"
                >
                <div v-if="emailTouched && !isEmailValid" class="text-danger mt-1">Invalid email format</div>
              </div>

              <div class="mb-4">
                <label class="form-label fs-5">Password</label>
                <input
                  type="password"
                  class="form-control form-control-lg"
                  v-model.trim="formData.password"
                  required
                  placeholder="Enter password (min 6 characters)"
                  @blur="passwordTouched = true"
                >
                <div v-if="passwordTouched && formData.password.length > 0 && formData.password.length < 6" class="text-danger mt-1">Password must be at least 6 characters</div>
              </div>

              <div class="mb-5">
                <label class="form-label fs-5">Confirm Password</label>
                <input
                  type="password"
                  class="form-control form-control-lg"
                  v-model.trim="formData.confirmPassword"
                  required
                  placeholder="Confirm your password"
                  @blur="confirmPasswordTouched = true"
                >
                <div v-if="confirmPasswordTouched && formData.confirmPassword.length > 0 && formData.confirmPassword !== formData.password" class="text-danger mt-1">Passwords do not match</div>
              </div>

              <button type="submit" class="btn btn-primary btn-lg w-100 mb-4" :disabled="!isFormValid">
                Register
              </button>

              <div class="text-center">
                <router-link to="/login" class="text-decoration-none">
                  Already have an account? Sign In
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

export default {
  data() {
    return {
      userType: 'student',
      formData: {
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
      },
      emailTouched: false,
      passwordTouched: false,
      confirmPasswordTouched: false
    }
  },
  computed: {
    isEmailValid() {
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailPattern.test(this.formData.email);
    },
    isFormValid() {
      return (
        this.formData.username &&
        this.isEmailValid &&
        this.formData.password.length >= 6 &&
        this.formData.password === this.formData.confirmPassword
      );
    }
  },
  methods: {
    validateEmail() {
      this.emailTouched = true;
    },
    async handleRegister() {
      if (!this.isFormValid) {
        alert('Please correct the errors before submitting.');
        return;
      }
      try {
        const response = await axios.post('/api/register', {
          user_type: this.userType,
          ...this.formData
        });
        if (response.status === 201) {
          alert('Registration successful, please login');
          this.$router.push('/login');
        }
      } catch (error) {
        alert(error.response?.data?.message || 'Registration failed');
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
