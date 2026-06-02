<template>
  <div class="d-flex flex-column min-vh-100">
    <!-- 顶部导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm" v-if="!$route.meta.hideHeaderFooter">
      <div class="container">
        <!-- 品牌 Logo -->
        <a class="navbar-brand" href="#" @click.prevent="redirectBasedOnRole">IELTS Master</a>

        <!-- 始终显示的用户名 -->
        <span v-if="isLoggedIn" class="navbar-text text-white ms-auto d-lg-none">
          Hello, {{ username }}!<i class="bi bi-person-circle me-2"></i>
        </span>

        <!-- 折叠按钮 -->
        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <!-- 导航栏内容 -->
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link class="nav-link" to="/writing">Writing</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/reading">Reading</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/listening">Listening</router-link>
            </li>
            <li class="nav-item" v-if="userStore.userRole === 'student'">
              <router-link class="nav-link" to="/peer_review">Peer Review</router-link>
            </li>
            <li class="nav-item" v-if="userStore.userRole === 'teacher'">
              <router-link class="nav-link" to="/bank_management">Bank Management</router-link>
            </li>


          </ul>

          <!-- 登录 / 登出 -->
          <ul class="navbar-nav ms-auto">
            <!-- 非折叠状态下，Hello, username! 作为一个独立的 nav-item -->
            <li v-if="isLoggedIn" class="nav-item d-none d-lg-block">
              <span class="nav-link disabled text-white">
                <i class="bi bi-person-circle me-2"></i>Hello, {{ username }}!
              </span>
            </li>
            <li class="nav-item" v-if="!isLoggedIn">
              <router-link class="nav-link" to="/login">
                Login
              </router-link>
            </li>
            <li class="nav-item" v-else>
              <button class="nav-link" @click="handleLogout">
                Logout
              </button>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <!-- 主内容区域 -->
    <main class="flex-grow-1">
      <router-view/>
    </main>

    <!-- 页脚 -->
    <footer class="bg-dark text-white mt-auto py-3" v-if="!$route.meta.hideHeaderFooter">
      <div class="container">
        <div class="row">
          <div class="col-md-6">
            <h5>IELTS Master</h5>
            <p>Professional IELTS Training Platform</p>
          </div>
          <div class="col-md-6 text-end">
            <p class="mb-0">&copy; 2025 All rights reserved</p>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
import { useUserStore } from '@/stores/user';

export default {
  data() {
    return {
      userStore: null, // 存储 Pinia store
    };
  },
  created() {
    this.userStore = useUserStore(); // 初始化 Pinia store
  },
  computed: {
    isLoggedIn() {
      return this.userStore.isLoggedIn; // 直接访问 store
    },
    username() {
      return this.userStore.username;
    },
    userRole() {
      return this.userStore.userRole;
    },
  },
  methods: {
    redirectBasedOnRole() {
      const role = this.userRole; // 直接使用 computed 属性
      if (role === 'student') {
        this.$router.push('/student');
      } else if (role === 'teacher') {
        this.$router.push('/teacher');
      } else {
        this.$router.push('/');
      }
    },
    handleLogout() {
      this.userStore.logout(); // 直接调用 store 方法
      localStorage.removeItem('token');
      localStorage.removeItem('userRole');
      localStorage.removeItem('username');
      this.$router.push('/login');
    },
  },
};
</script>


<style>
/* 让 Logout 按钮看起来更像普通的 nav-link */
.navbar .btn-link {
  text-decoration: none;
  border: none;
  background: none;
  padding: 0;
}
</style>
