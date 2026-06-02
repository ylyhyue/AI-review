<!-- 前端 components/ClassView.vue -->
<template>
  <div class="container py-4">
    <!-- 学生表格 -->
    <table class="table table-hover">
      <thead class="table-dark">
        <tr>
          <th>Student</th>
          <th>Listening</th>
          <th>Reading</th>
          <th>Writing</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="student in students" :key="student.id">
          <td>{{ student.name }}</td>
          <td>{{ formatScore(student.averages.listening) }}</td>
          <td>{{ formatScore(student.averages.reading) }}</td>
          <td>{{ formatScore(student.averages.writing) }}</td>
          <td>
            <button class="btn btn-sm btn-info me-2"
                    @click="showSubmissionModal(student)">
              <i class="bi bi-file-text"></i> Submissions
            </button>
            <button class="btn btn-sm btn-primary"
                    @click="showReviewModal(student)">
              <i class="bi bi-chat-dots"></i> Reviews
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 提交模态框 -->
    <div class="modal fade" id="submissionModal" tabindex="-1">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ currentStudent?.name }}'s Submissions</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div v-if="loading" class="text-center py-4">
              <div class="spinner-border"></div>
              <p class="mt-2">Loading...</p>
            </div>

            <table v-else class="table">
              <thead>
                <tr>
                  <th>Coursework ID</th>
                  <th>Assignment</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                <tr @click="submit(sub.bank_type, sub.sub_id)" v-for="sub in submissions" :key="sub.bank_id">
                  <td>CW{{ sub.cw_id }}</td>
                  <td>{{ sub.bank_name }}</td>
                  <td>{{ sub.bank_type }}</td>
                  <td :class="statusClass(sub)">
                    {{ sub.status }}
                    <span v-if="sub.is_late" class="badge bg-warning ms-2">Late</span>
                  </td>
                  <td>{{ sub.score ?? '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- 互评模态框 -->
    <div class="modal fade" id="reviewModal" tabindex="-1">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ currentStudent?.name }}'s Reviews</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <table class="table">
              <thead>
                <tr>
                  <th>Coursework ID</th>
                  <th>Assignment</th>
                  <th>Result</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  @click="submit(rev.bank_type, rev.sub_id)"
                  v-for="rev in reviews"
                  :key="rev.id"
                  :class="{
                    'valid-row': rev.is_fake === false,
                    'invalid-row': rev.is_fake === true
                  }"
                >
                  <td>CW{{ rev.cw_id }}</td>
                  <td>{{ rev.assignment }}</td>
                  <td>
                    <span v-if="rev.is_fake === null || rev.is_fake === undefined">Not evaluated</span>
                    <span v-else-if="rev.is_fake === false">Valid</span>
                    <span v-else>Not Valid</span>
                  </td>
                  <td>
                    <span v-if="rev.is_fake === null || rev.is_fake === undefined">Not evaluated</span>
                    <span v-else>{{ rev.confidence }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { Modal } from 'bootstrap'
import {useRoute, useRouter, onBeforeRouteLeave} from 'vue-router'
import { ref, onMounted } from 'vue'
export default {
  setup() {
    const submissionModal = ref(null)
    const reviewModal = ref(null)
    const route = useRoute()

    onMounted(() => {
      // 初始化 Bootstrap Modal 实例
      submissionModal.value = new Modal(document.getElementById('submissionModal'))
      reviewModal.value = new Modal(document.getElementById('reviewModal'))
    })

    onBeforeRouteLeave(() => {
      if (submissionModal.value) {
        submissionModal.value.hide()
      }
      if (reviewModal.value) {
        reviewModal.value.hide()
      }
      // 移除残留的 modal-backdrop
      document.querySelectorAll('.modal-backdrop').forEach(el => el.remove())
      document.body.classList.remove('modal-open')
    })
    const router = useRouter();
    return { route, router }
  },

  data() {
    return {
      students: [],          // 学生列表数据
      courseworks: [],       // 课程作业数据
      submissions: [],       // 当前学生的提交记录
      reviews: [],           // 当前学生的互评记录
      currentStudent: null,  // 当前选中学生
      submissionModal: null, // 提交模态框实例
      reviewModal: null,     // 互评模态框实例
      loading: false         // 加载状态
    }
  },

  methods: {
    // 格式化分数显示
    formatScore(score) {
      if (score === null || score === undefined) return 'N/A'
      return score.toFixed(2)
    },

    // 显示提交模态框
    async showSubmissionModal(student) {
      this.currentStudent = student
      this.loading = true
      this.submissionModal.show()

      try {
        const res = await axios.get(
          `/api/submissions/${student.id}?class_id=${this.route.params.classId}`
        )
        this.submissions = res.data
      } catch (error) {
        console.error('提交记录获取失败:', error)
        this.submissions = []
      } finally {
        this.loading = false
      }
    },
    async submit(bank_type, sub_id){
      if (sub_id !== 'None'){
        if (bank_type === 'writing'){
            this.router.push(`/review/${sub_id}`)
        } else {
           this.router.push(`/submission/${sub_id}`)
        }
      }
    },
    // 显示互评模态框
    async showReviewModal(student) {
      this.currentStudent = student
      this.loading = true
      this.reviewModal.show()

      try {
        const res = await axios.get(
          `/api/reviews/${student.id}?class_id=${this.route.params.classId}`
        )
        this.reviews = res.data
      } catch (error) {
        console.error('互评记录获取失败:', error)
        this.reviews = []
      } finally {
        this.loading = false
      }
    },

    // 提交状态样式
    statusClass(sub) {
      return {
        'text-success': sub.status === 'Submitted' && !sub.is_late,
        'text-danger': sub.status === 'Unsubmitted',
        'text-warning': sub.is_late
      }
    },

    // 互评结果样式
    resultClass(result) {
      return {
        'text-success': result === 'positive',
        'text-warning': result === 'neutral',
        'text-danger': result === 'negative'
      }
    }
  },

  async mounted() {
    // 初始化Bootstrap模态框
    this.submissionModal = new Modal('#submissionModal')
    this.reviewModal = new Modal('#reviewModal')
    // 加载班级初始数据
    try {
      const res = await axios.get(`/api/check/${this.route.params.classId}`)
      this.students = res.data.students
      this.courseworks = res.data.courseworks
    } catch (error) {
      console.error('班级数据加载失败:', error)
      this.students = []
      this.courseworks = []
    }
  }
}
</script>

<style scoped>
.table-hover tbody tr:hover {
  background-color: #f8f9fa;
}

.badge {
  font-size: 0.75em;
  vertical-align: middle;
}

.text-success { color: #28a745 !important; }
.text-danger { color: #dc3545 !important; }
.text-warning { color: #ffc107 !important; }

.modal-xl {
  max-width: 1200px;
}

:deep(.valid-row) {
  --bs-table-bg: #e6ffed !important; /* 浅绿色 */
}

:deep(.invalid-row) {
  --bs-table-bg: #ffebee !important; /* 浅红色 */
}

/* 如果需要 hover 效果 */
:deep(.valid-row:hover) {
  --bs-table-bg: #d4edda !important;
}

:deep(.invalid-row:hover) {
  --bs-table-bg: #f8d7da !important;
}

</style>
