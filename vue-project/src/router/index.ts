import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import Login from '@/views/LoginView.vue'
import Register from '@/views/RegisterView.vue'
import StudentDashboard from '@/views/StudentDashboard.vue'
import TeacherDashboard from '@/views/TeacherDashboard.vue'
import BankList from '@/views/BankList.vue'
import BankDetail from '@/views/BankDetail.vue'
import Practice from '@/views/Practice.vue'
import Cw from '@/views/Coursework.vue'
import ListeningPractice from '@/views/Listening.vue'
import Submission from "@/views/Submission.vue";
import PeerReview from "@/views/PeerReview.vue";
import Review from "@/views/Review.vue";
import BankManage from "@/views/BankManage.vue";
import CheckStudent from "@/views/CheckStudent.vue";



const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: {}
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: {}
  },
  {
    path: '/register',
    name: 'register',
    component: Register,
    meta: {}
  },
  {
    path: '/:bank_type', // 动态路由，支持/reading和/listening
    component: BankList,
    props: true,
    name:'bank',
    meta: {}
  },
  {
    path: '/:bank_type/:a/:b', // 详情页路由
    component: BankDetail,
    props: true,
    name:'bank_detail',
    meta: {}
  },
  {
    path: '/peer_review', // 详情页路由
    component: PeerReview,
    props: true,
    name:'peer_review',
    meta: {requiresAuth: true, role: 'student'}
  },
  {
    path: '/review/:sub_id', // 详情页路由
    component: Review,
    props: true,
    name:'review',
    meta: {requiresAuth: true}
  },
  {
    path: '/submission/:sub_id', // 详情页路由
    component: Submission,
    props: true,
    name:'submission',
    meta: {requiresAuth: true}
  },
  {
    path: '/:bank_type/:a/:b/:display_order', // 详情页路由
    component: Practice,
    props: true,
    name:'practice',
    meta: { hideHeaderFooter: true }
  },
  {
    path: '/listening/:a/:b/:display_order', // 听力详情页
    component: ListeningPractice, // 使用单独的组件处理听力
    props: true,
    name: 'listening-practice',
    meta: { hideHeaderFooter: true }
  },
  {
    path: '/student',
    name: 'student-dashboard',
    component: StudentDashboard,
    meta: { requiresAuth: true, role: 'student'}
  },
  {
    path: '/teacher',
    name: 'teacher-dashboard',
    component: TeacherDashboard,
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/bank_management',
    name: 'bank-management',
    component: BankManage,
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/check/:classId',
    name: 'check-students',
    component: CheckStudent,
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/cw/:classId',
    name: 'Coursework',
    component: Cw,
    props: true,
    meta: { requiresAuth: true, role: 'teacher' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫示例（可根据需要扩展）
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {

    const isAuthenticated = localStorage.getItem('token') // 需要实际实现认证逻辑
      if (to.meta.role)
        if (to.meta.role != localStorage.getItem('userRole'))
          return next('/login')
    if (!isAuthenticated)
      return next('/login')
  }
  next()
})

export default router
