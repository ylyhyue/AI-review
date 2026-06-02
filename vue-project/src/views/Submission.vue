<template>
  <div class="container">
    <div v-if="isLoading" class="text-center">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div v-else class="row">
      <div class="col-md-12">
        <h2 class="text-center mt-2">Submission Results</h2>

        <!-- 作业信息 -->
        <div class="card mt-4">
          <div class="card-header bg-primary text-white">
            <h4>Assignment Information</h4>
          </div>
          <div class="card-body">
            <p><strong>Submission Time:</strong> {{ submissionTime }}</p>
            <p><strong>Completion Time:</strong> {{ completionTime }}</p>
            <p><strong>Bank Type:</strong> {{ bankInfo.bank_type }}</p>
            <p><strong>Location:</strong> {{ formatLocation(bankInfo.location) }}</p>
            <p><strong>Display Order:</strong> {{ bankInfo.display_order }} {{ bankInfo.bank_name }}</p>
          </div>
        </div>

        <!-- 非写作类型的内容 -->
        <template v-if="bankInfo.bank_type !== 'writing'">
          <!-- 结果统计表格 -->
          <div class="card mt-4">
            <div class="card-header bg-info text-white">
              <h4>Performance Summary</h4>
            </div>
            <div class="card-body">
              <table class="table">
                <thead>
                  <tr>
                    <th>Total</th>
                    <th>Correct</th>
                    <th>Incorrect</th>
                    <th>Unanswered</th>
                    <th>Accuracy</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>{{ performanceSummary.total }}</td>
                    <td>{{ performanceSummary.correct }}</td>
                    <td>{{ performanceSummary.incorrect }}</td>
                    <td>{{ performanceSummary.unanswered }}</td>
                    <td>{{ (performanceSummary.accuracy || 0).toFixed(2) }}%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 答题情况表格 -->
          <div class="card mt-4 mb-4">
            <div class="card-header bg-success text-white">
              <h4>Answer Details</h4>
            </div>
            <div class="card-body">
              <table class="table">
                <thead>
                  <tr>
                    <th>Question</th>
                    <th>Your Answer</th>
                    <th>Correct Answer</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(answer, num) in answerDetails" :key="num">
                    <td>{{ num }}</td>
                    <td :class="{
                      'text-success': answer.isCorrect,
                      'text-danger': !answer.isCorrect,
                      'text-muted': !answer.userAnswer
                    }">
                      {{ answer.userAnswer || 'Not Answered' }}
                    </td>
                    <td>{{ answer.correctAnswer }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>

        <!-- 写作类型的内容 -->
        <template v-else>
          <!-- AI 评价 -->
          <div class="card mt-4">
            <div class="card-header bg-info text-white">
              <h4>AI Evaluation</h4>
            </div>
            <div class="card-body">
              <table class="table table-bordered">
                <thead>
                  <tr>
                    <!-- Dynamic header based on available data -->
                    <th>{{ performanceSummary?.result?.task_response ? 'Task Response' : 'Task Achievement' }}</th>                    <th>Coherence & Cohesion</th>
                    <th>Lexical Resource</th>
                    <th>Grammatical Accuracy</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <!-- Dynamic field selection with fallback -->
                    <td class="text-center">
                      {{
                        performanceSummary?.result?.task_response ??
                        performanceSummary?.result?.task_achievement ??
                        'N/A'
                      }}
                    </td>
                    <td class="text-center">{{ performanceSummary.result?.coherence_cohesion || 'N/A' }}</td>
                    <td class="text-center">{{ performanceSummary.result?.lexical_resource || 'N/A' }}</td>
                    <td class="text-center">{{ performanceSummary.result?.grammatical_accuracy || 'N/A' }}</td>
                  </tr>
                </tbody>
              </table>
              <div class="mt-3">
                <h5>Detailed Feedback:</h5>
                <div class="card-body feedback-container">
                  <div v-html="formattedFeedback"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 用户答案 -->
          <div class="card mt-4 mb-4">
            <div class="card-header bg-success text-white">
              <h4>Your Writing</h4>
            </div>
            <div class="card-body">
              <pre class="p-3 bg-light rounded" style="white-space: pre-wrap;">{{ answerDetails }}</pre>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      isLoading: true,
      submissionTime: '',
      completionTime: '',
      bankInfo: { bank_type: '' }, // 初始化防止 undefined
      performanceSummary: {},
      answerDetails: {},
      formattedFeedback: ''
    };
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
    formatLocation(location) {
      if (!location || !location.includes(':')) return 'Unknown Location';
      const [a, b] = location.split(':');
      return `Cambridge IELTS ${a} Test ${b}`;
    },
    async fetchData() {
      try {
        this.isLoading = true;
        const response = await axios.get(`/api/submission/${this.$route.params.sub_id}`);

        if (response.status === 202) {
          setTimeout(() => this.fetchData(), 5000);
          return;
        }

        const data = response.data;
        this.submissionTime = data.submission_time;
        this.completionTime = data.completion_time;
        this.bankInfo = data.bank_info;
        this.performanceSummary = data.performance_summary;
        this.answerDetails = data.answer_details;
        if (response.data.performance_summary?.information) {
        this.formattedFeedback = this.formatFeedback(
          response.data.performance_summary.information
        )
      }
      } catch (error) {
        console.error('Error:', error);
        alert('Error: ' + error.message);
      } finally {
        this.isLoading = false;
      }
    }
  },
  created() {
    this.fetchData();
  }
};
</script>

<style scoped>
pre {
  font-family: inherit;
  line-height: 1.6;
  font-size: 16px;
}
</style>
