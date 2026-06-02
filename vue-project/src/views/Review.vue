<template>
  <div class="container-fluid bg-light-blue" style="min-height: 100vh;">
    <!-- 顶部资源展示区 -->
    <div class="row p-4">
      <!-- 左侧资源区 -->
      <div class="col-md-6 bg-white rounded shadow-sm p-3">
        <h4 class="text-primary mb-3">Reference Materials</h4>
        <!-- 图片资源 -->
        <div v-if="pictures.length" class="mb-4">
          <h5>Pictures</h5>
          <div v-for="(img, index) in pictures" :key="'img-'+index">
            <img :src="img" class="img-fluid mb-2 border border-primary">
          </div>
        </div>
        <!-- 文本资源 -->
        <div v-if="texts" class="mb-4">
          <h5>Text Content</h5>
          <div :key="'text-0'" class="p-3 bg-light rounded" v-html="texts"></div>
        </div>
      </div>

      <!-- 右侧用户答案 -->
      <div class="col-md-6 bg-white rounded shadow-sm ml-2 p-3">
        <h4 class="text-primary mb-3">Student Answer</h4>
        <div class="p-3 bg-light rounded">
          {{ userAnswer || 'Loading answer...' }}
        </div>
      </div>
    </div>

    <!-- 评分表单区（新评审） -->
    <div class="row p-4" v-if="showReviewForm|| userStore.userRole === 'teacher'">
      <div class="col-md-12 bg-white rounded shadow-sm p-4">
        <!-- 原有评分表单内容 -->
        <div class="row mb-4">
          <div v-for="(criteria, index) in criteriaList"
               :key="criteria"
               class="col-3 text-center">
            <label class="d-block text-primary font-weight-bold mb-2"
                   style="height: 40px; display: flex; align-items: center; justify-content: center;">
              {{ formatCriteriaName(criteria) }}
            </label>
            <input type="number"
                   v-model="scores[criteria]"
                   class="form-control"
                   step="0.5"
                   min="0"
                   max="9"
                   @input="validateScore(criteria)"
                   required>
          </div>
        </div>

        <div class="form-group">
          <label class="text-primary font-weight-bold">Comments</label>
          <textarea v-model="comments"
                    class="form-control"
                    rows="5"
                    placeholder="Enter your feedback..."></textarea>
        </div>

        <button @click="submitReview"
                class="btn btn-primary btn-lg btn-block mt-4"
                :disabled="isSubmitting">
          {{ isSubmitting ? 'Submitting...' : 'Submit Review' }}
        </button>
      </div>
    </div>

    <!-- 评审详情展示区 -->
    <div class="row p-4" v-if="!showReviewForm|| userStore.userRole === 'teacher'">
      <div class="col-12">
        <h4 class="text-primary mb-4">Review Details</h4>
          <div v-for="(review, index) in reviewDetails" :key="index" class="card mb-4 shadow-sm">
  <div class="card-body">
    <!-- 评分结果展示 -->
    <h4 class="card-title text-primary mb-3">{{ review.reviewer_name }}'s Comments</h4>

    <!-- 评分项（横向排列） -->
    <div class="row mb-4">
      <div v-for="(criteria, index) in criteriaList"
           :key="criteria"
           class="col-3 text-center">
        <label class="d-block text-primary font-weight-bold mb-2"
               style="height: 40px; display: flex; align-items: center; justify-content: center;">
          {{ formatCriteriaName(criteria) }}
        </label>
        <input
          type="number"
          :value="getReviewScore(review.review_result, criteria)"
          class="form-control"
          step="0.5"
          readonly>
      </div>
    </div>

    <!-- 评语展示 -->
    <div class="form-group">
  <label class="text-primary font-weight-bold">Comments</label>
  <div
    class="form-control-plaintext border rounded p-2 bg-light"
    style="min-height: 100px; white-space: pre-wrap;"
    v-html="formatFeedback(review.review_info) || 'No comments'">
  </div>
</div>

    <!-- 检测结果（AI 验证） -->
    <div v-if="review.detection" class="mt-4 p-3 rounded"
         :class="review.detection.is_fake ? 'bg-danger-light' : 'bg-success-light'">
      <h5 class="mb-3">Fake Review Verification</h5>

      <!-- 第一行：Validation + Confidence Level -->
      <div class="row mb-2">
        <div class="col-md-6">
          <span>Validation:</span>
          <strong :class="review.detection.is_fake ? 'text-danger' : 'text-success'">
            {{ review.detection.is_fake ? 'Needs Review' : 'Approved' }}
          </strong>
        </div>
        <div class="col-md-6">
          <span>Confidence Level:</span>
          <strong>{{ (review.detection.confidence).toFixed(1) }}%</strong>
        </div>
      </div>

      <!-- 第二行：AI Analysis -->
      <div class="row">
        <div class="col-12">
          <span>AI Analysis:</span>
          <strong>{{ review.detection.evaluation || 'No additional notes' }}</strong>
        </div>
      </div>
    </div>
  </div>
</div>

      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user.js";

export default {
  name: 'ReviewPage',
  setup() {
    const userStore = useUserStore();
    const router = useRouter();
    return { userStore, router };
  },
  data() {
    return {
      criteriaList: [],
      scores: {},
      comments: '',
      userAnswer: '',
      studentId: '',
      texts: null,
      pictures: [],
      reviewDetails: [],
      isSubmitting: false,
      isLoading: true,
      criteriaMapping: {
        'task_achievement': 'Task Achievement',
        'task_response': 'Task Response',
        'coherence_cohesion': 'Coherence and Cohesion',
        'lexical_resource': 'Lexical Resource',
        'grammatical_accuracy': 'Grammatical Accuracy'
      }
    };
  },
  computed: {
    isSubmitter() {
      return String(this.studentId) === this.userStore.token;
    },
    showReviewForm() {
      if (this.isSubmitter) {
        return false;
      }

      if (this.reviewDetails.length >= 1) {
        if (this.reviewDetails.length === 1) {
          // 只有1条评论时，检查是否是AI评论
          return this.reviewDetails[0].reviewer_name === 'AI';
        } else {
          // 多于1条评论时直接返回true
          return true;
        }
      }
      // 默认情况（没有评论时）
      return true;
    }
  },
  mounted() {
    this.fetchData();
  },
  methods: {
    formatFeedback(text) {
      // 1. 移除开头的**和空行
      let formatted = text.replace(/^\*\*\s*\n/, '')

      // 2. 处理**包围的标题（如**Task Response (TR):**）
      formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

      // 3. 保留段落换行
      formatted = formatted.replace(/\n\n/g, '<br><br>')

      // 4. 将单换行转换为空格（保持段落内换行）
      formatted = formatted.replace(/\n(?!\n)/g, ' ')

      return formatted
    },
    formatCriteriaName(key) {
      return this.criteriaMapping[key] || key.split('_').map(word =>
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ');
    },

    getReviewScore(reviewResult, criteria) {
      // 1. 将JSON字符串转为对象
      const resultObj = typeof reviewResult === 'string'
        ? JSON.parse(reviewResult)
        : reviewResult;

      // 2. 查找匹配的键
      const apiKey = Object.keys(this.criteriaMapping).find(
        key => this.criteriaMapping[key] === criteria
      );

      return apiKey ? resultObj[apiKey] : 'N/A';
    },

    async fetchData() {
      const subId = this.$route.params.sub_id;

      try {
        // 获取基础数据
        const res = await axios.get(`/api/review/${subId}`);
        const data = res.data;
        this.studentId = data.student_id;
        this.texts = data.text;
        this.userAnswer = data.user_answer;
        this.pictures = data.pictures || [];

        // 设置评分标准
        this.criteriaList = data.bank_order === 1 ?
          ['Task Achievement', 'Coherence and Cohesion', 'Lexical Resource', 'Grammatical Accuracy'] :
          ['Task Response', 'Coherence and Cohesion', 'Lexical Resource', 'Grammatical Accuracy'];

        // 获取评审数据
        const params = {};

          params.reviewer_id = this.userStore.token;
          params.reviewer_type = this.userStore.userRole;


        const detailRes = await axios.get(`/api/review-details/${subId}`, {params});
        this.reviewDetails = detailRes.data;
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    },

    // 原有validateScore和submitReview方法保持不变
    validateScore(criteria) {
      let value = this.scores[criteria];
      if (value === null || value === '') return;

      // 确保是数字
      value = Number(value);

      // 限制范围
      value = Math.max(0, Math.min(9, value));

      // 检查小数部分
      const decimal = value % 1;
      if (decimal !== 0 && decimal !== 0.5) {
        // 四舍五入到最近的0.5
        value = Math.round(value * 2) / 2;
      }

      this.scores[criteria] = value;
    },

    async submitReview() {
      // 验证所有评分已填写
      const missingScores = this.criteriaList.filter(
        criteria => this.scores[criteria] === null
      );

      if (missingScores.length > 0) {
        alert(`Please complete all scores: ${missingScores.join(', ')}`);
        return;
      }

      this.isSubmitting = true;

      // Transform scores to API format
      const apiScores = {};
      this.criteriaList.forEach(displayName => {
        const apiName = Object.keys(this.criteriaMapping).find(
        key => this.criteriaMapping[key] === displayName
      );
        apiScores[apiName] = this.scores[displayName];
      });
      const payload = {
        scores: apiScores,
        comments: this.comments,
        sub_id: this.$route.params.sub_id,
        reviewer_id: this.userStore.token,
        reviewer_role: this.userStore.userRole,
        reviewee_id: this.studentId,
        texts: this.userAnswer
      };

      try {
        const response = await axios.post('/api/submit-review', payload);

        if (response.status === 200) {
          this.$notify({
            type: 'success',
            title: 'Success',
            text: 'Review submitted successfully!'
          });
          // 重置表单
          this.comments = '';
          this.criteriaList.forEach(criteria => {
            this.scores[criteria] = null;
          });
          this.router.push(`/peer_review`);
        }
      } catch (error) {
        console.error('Error submitting review:', error);

        let errorMessage = 'Submission failed';
        if (error.response) {
          errorMessage += ` (Status: ${error.response.status})`;
          if (error.response.data && error.response.data.message) {
            errorMessage += ` - ${error.response.data.message}`;
          }
        }

        this.$notify({
          type: 'error',
          title: 'Error',
          text: errorMessage
        });
      } finally {
        this.isSubmitting = false;
      }
    }
  }
};
</script>

<style scoped>
.bg-light-blue {
  background-color: #f0f8ff;
}

.bg-danger-light {
  background-color: #fee2e2;
  border: 1px solid #fca5a5;
}

.bg-success-light {
  background-color: #dcfce7;
  border: 1px solid #86efac;
}

.text-danger {
  color: #dc2626;
}

.text-success {
  color: #16a34a;
}

.form-control[readonly] {
  background-color: #f8f9fa;
  opacity: 1;
}

pre {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
