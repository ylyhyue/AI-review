<template>
  <!-- 首页容器 -->
  <div class="home-container">
    <h1>Welcome to IELTS Master</h1>
    <!-- 导航卡片容器 -->
    <div class="nav-cards">
      <!-- 学生入口 -->
      <router-link to="/login?type=student" class="nav-card student">
        <h2>Student Entrance</h2>
        <p>Start your IELTS practice journey</p>
      </router-link>

      <!-- 教师入口 -->
      <router-link to="/login?type=teacher" class="nav-card teacher">
        <h2>Teacher Entrance</h2>
        <p>Manage student progress and content</p>
      </router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HomeView'
}
</script>

<style scoped>
.home-container {
  padding: 2rem;
  text-align: center;
}

.nav-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 3rem;
}

.nav-card {
  padding: 2rem;
  border-radius: 8px;
  text-decoration: none;
  color: white;
  transition: transform 0.3s ease;
}

.nav-card:hover {
  transform: translateY(-5px);
}

.student {
  background: linear-gradient(135deg, #4a90e2, #0066cc);
}

.teacher {
  background: linear-gradient(135deg, #00c853, #009624);
}
</style>
