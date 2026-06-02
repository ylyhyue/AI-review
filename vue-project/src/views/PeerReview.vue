<template>
  <div class="container mt-4">
    <!-- 待评价文章 -->
    <section class="mb-5">
      <h2 class="text-primary mb-4">Pending Reviews</h2>
      <div v-if="pendingReviews.length" class="row g-4">
        <div v-for="review in pendingReviews" :key="review.sub_id" class="col-md-6">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5 class="card-title">{{ review.bank_name }}</h5>
              <p class="mb-1">Author: {{ review.review_set.includes('Type: open') ? review.student_name : 'Anonymous' }}</p>
              <p class="mb-1">Location: {{formatLocation(review.location)}} Passage {{ review.display_order}} </p>
              <p class="mb-1">Class: {{ review.class_name }}</p>
              <p class="mb-2 text-muted">Submitted: {{ formatTime(review.sub_time) }}</p>
              <button class="btn btn-primary" @click="startReview(review)">Start Review</button>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-muted">No pending reviews available</div>
    </section>

    <!-- 收到的评价 -->
    <section class="mb-5">
      <h2 class="text-primary mb-4">Received Reviews</h2>
      <div v-if="receivedReviews.length" class="row g-4">
        <div v-for="review in receivedReviews" :key="review.peer_id" class="col-md-6">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5 class="card-title">{{ review.bank_name }}</h5>
              <p class="mb-1">Reviewer: {{ review.reviewer_name }}</p>
<p class="mb-1">Sub id: {{ review.sub_id }}</p>
              <p class="mb-1">Review Time: {{ formatTime(review.review_time) }}</p>
              <p class="mb-1">Location: {{formatLocation(review.location)}} Passage {{ review.display_order}} </p>
              <button class="btn btn-primary" @click="startReview(review)">View Details</button>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-muted">No received reviews yet</div>
    </section>

    <!-- 已做出的评价 -->
    <section class="mb-5">
      <h2 class="text-primary mb-4">My Reviews</h2>
      <div v-if="myReviews.length" class="row g-4">
        <div v-for="review in myReviews" :key="review.peer_id" class="col-md-6">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5 class="card-title">{{ review.bank_name }}</h5>
              <p class="mb-1">Reviewee: {{ review.reviewee_name }}</p>
              <p class="mb-1">Review Time: {{ formatTime(review.review_time) }}</p>
              <p class="mb-1">Location: {{formatLocation(review.location)}} Passage {{ review.display_order}} </p>
              <button class="btn btn-primary" @click="startReview(review)">View Details</button>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-muted">No reviews submitted yet</div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useUserStore } from '@/stores/user';
import axios from 'axios';
import dayjs from 'dayjs';
import {useRouter} from "vue-router";
const router = useRouter();
const userStore = useUserStore();
const studentId = userStore.token;

const pendingReviews = ref([]);
const receivedReviews = ref([]);
const myReviews = ref([]);

// 时间格式化函数
const formatTime = (timeStr) => {
  return dayjs(timeStr).format('YYYY-MM-DD HH:mm');
};

// 获取待评价数据
const fetchPendingReviews = async () => {
  try {
    const response = await axios.get('/api/to-review', {
      params: { student_id: studentId }
    });
    pendingReviews.value = response.data;
  } catch (error) {
    console.error('Error fetching pending reviews:', error);
  }
};

// 获取收到的评价
const fetchReceivedReviews = async () => {
  try {
    const response = await axios.get('/api/received-reviews', {
      params: { student_id: studentId }
    });
    receivedReviews.value = response.data;
  } catch (error) {
    console.error('Error fetching received reviews:', error);
  }
};

// 获取已做出的评价
const fetchMyReviews = async () => {
  try {
    const response = await axios.get('/api/my-reviews', {
      params: { student_id: studentId }
    });
    myReviews.value = response.data;
  } catch (error) {
    console.error('Error fetching my reviews:', error);
  }
};

// 开始评价
const startReview = (review) => {
  router.push(`/review/${review.sub_id}`);
};
const formatLocation = (location) => {
  const [a, b] = location.split(':');
  return `Cambridge IELTS ${a} Test ${b}`;
};
// 初始化数据
onMounted(() => {
  fetchPendingReviews();
  fetchReceivedReviews();
  fetchMyReviews();
});
</script>

<style scoped>
.card {
  transition: transform 0.2s;
}
.card:hover {
  transform: translateY(-5px);
}
.text-primary {
  color: #0d6efd !important;
}
.bg-light {
  background-color: #f8f9fa !important;
}
</style>
