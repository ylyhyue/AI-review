<template>
  <div class="container mt-4">
    <h1 class="mb-4">My Assignments</h1>
    <!-- 显示错误信息 -->
    <div v-if="errorMessage" class="alert alert-danger">
      {{ errorMessage }}
    </div>
    <!-- 加载状态 -->
    <div v-if="isLoading" class="text-center">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <!-- 按状态和类型显示题库 -->
    <div v-else>
      <!-- 待提交部分 (status 0,1) -->
      <div class="mb-5">
        <h2 class="mb-3 text-primary">Pending Submission</h2>
        <div v-for="(banks, type) in pendingByType" :key="'pending-'+type" class="mb-4">
          <h3 class="mb-3">{{ type.toUpperCase() }}</h3>
          <div class="row">
            <div
              v-for="bank in banks"
              :key="bank.bank_id"
              class="col-md-6 mb-4"
              @dblclick="navigateToBank(type, bank.location, bank.display_order)"
            >
              <div class="card h-100" :class="{'bg-light-blue': bank.status === 1}">
                <div class="card-body">
                  <h5 class="card-title">{{ bank.bank_name }}</h5>
                  <p class="card-text">
                    <strong>Class:</strong> {{ bank.classname }}<br>
                    <strong>Location:</strong> {{ formatLocation(bank.location) }}<br>
                    <strong>Order:</strong> {{ bank.display_order }}<br>
                    <strong>Deadline:</strong> {{ formatDate(bank.deadline) }}<br>
                    <strong>Status:</strong> <span :class="statusClass(bank.status)">{{ statusText(bank.status) }}</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div v-if="banks.length === 0" class="alert alert-info">
            No pending assignments for {{ type.toUpperCase() }} type.
          </div>
        </div>
        <div v-if="Object.keys(pendingByType).length === 0" class="alert alert-success">
          No pending assignments - all caught up!
        </div>
      </div>

      <!-- 已提交部分 (status 2,3) -->
      <div class="mb-5">
        <h2 class="mb-3 text-success">Submitted Assignments</h2>
        <div v-for="(banks, type) in submittedByType" :key="'submitted-'+type" class="mb-4">
          <h3 class="mb-3">{{ type.toUpperCase() }}</h3>
          <div class="row">
            <div
              v-for="bank in banks"
              :key="bank.bank_id"
              class="col-md-6 mb-4"
              @dblclick="navigateToBank(type, bank.location, bank.display_order)"
            >
              <div class="card h-100" :class="{'bg-light-blue': bank.status === 3}">
                <div class="card-body">
                  <h5 class="card-title">{{ bank.bank_name }}</h5>
                  <p class="card-text">
                    <strong>Class:</strong> {{ bank.classname }}<br>
                    <strong>Location:</strong> {{ formatLocation(bank.location) }}<br>
                    <strong>Order:</strong> {{ bank.display_order }}<br>
                    <strong>Deadline:</strong> {{ formatDate(bank.deadline) }}<br>
                    <strong>Status:</strong> <span :class="statusClass(bank.status)">{{ statusText(bank.status) }}</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div v-if="banks.length === 0" class="alert alert-info">
            No submitted assignments for {{ type.toUpperCase() }} type.
          </div>
        </div>
        <div v-if="Object.keys(submittedByType).length === 0" class="alert alert-info">
          No submitted assignments yet.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';

const userStore = useUserStore();
const router = useRouter();
const allBanks = ref([]);
const errorMessage = ref('');
const isLoading = ref(true);

// 计算属性：按类型分组的待提交作业
const pendingByType = computed(() => {
  return groupByType(allBanks.value.filter(bank => bank.status === 0 || bank.status === 1));
});

// 计算属性：按类型分组的已提交作业
const submittedByType = computed(() => {
  return groupByType(allBanks.value.filter(bank => bank.status === 2 || bank.status === 3));
});

// 按类型分组辅助函数
const groupByType = (banks) => {
  return banks.reduce((acc, bank) => {
    const type = bank.bank_type.toLowerCase();
    if (!acc[type]) acc[type] = [];
    acc[type].push(bank);

    // 排序：过期在前，然后按截止日期
    acc[type].sort((a, b) => {
      if (a.status !== b.status) return b.status - a.status; // 状态1排在前面
      return new Date(a.deadline) - new Date(b.deadline);
    });

    return acc;
  }, {});
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return 'No deadline';
  const date = new Date(dateString);
  return date.toLocaleString();
};

// 拆分 location 为 a 和 b
const splitLocation = (location) => {
  const [a, b] = location.split(':');
  return { a, b };
};

const formatLocation = (location) => {
  const [a, b] = location.split(':');
  return `Cambridge IELTS ${a} Test ${b}`;
};

// 状态文本
const statusText = (status) => {
  const statusMap = {
    0: 'Pending (on time)',
    1: 'Pending (overdue)',
    2: 'Submitted (on time)',
    3: 'Submitted (late)'
  };
  return statusMap[status] || 'Unknown';
};

// 状态样式
const statusClass = (status) => {
  return {
    'text-primary': status === 0,
    'text-danger': status === 1,
    'text-success': status === 2,
    'text-warning': status === 3
  };
};

// 处理双击事件
const navigateToBank = (type, location, order) => {
  const { a, b } = splitLocation(location);
  router.push(`/${type}/${a}/${b}/${order}`);
};

// 获取学生的班级、作业和题库信息
const fetchAssignments = async () => {
  try {
    const studentId = userStore.token;

    // 1. 获取学生的班级信息
    const classResponse = await axios.get(`/api/student/${studentId}/classes`);
    const classes = classResponse.data;

    // 2. 获取每个班级的作业信息
    const assignments = [];
    for (const cls of classes) {
      const cwResponse = await axios.get(`/api/coursework?classId=${cls.class_id}`);
      const coursework = cwResponse.data;
      assignments.push(...coursework.map(cw => ({ ...cw, classname: cls.classname })));
    }

    // 3. 获取每个作业的题库信息
    const banks = [];
    for (const assignment of assignments) {
      const bankResponse = await axios.get(`/api/coursework/${assignment.cw_id}/banks/${studentId}`);
      const bankDetails = bankResponse.data;
      banks.push(...bankDetails.map(bank => ({
        ...bank,
        classname: assignment.classname,
        deadline: assignment.deadline
      })));
    }

    allBanks.value = banks;
  } catch (error) {
    console.error('Error fetching assignments:', error);
    errorMessage.value = error.response?.data?.error || error.message;
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  fetchAssignments();
});
</script>

<style scoped>
.card {
  border: 1px solid #ddd;
  border-radius: 8px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}
.card:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
}
.card-title {
  font-size: 1.25rem;
  font-weight: bold;
}

.card-text {
  font-size: 0.9rem;
  color: #555;
}

.alert {
  margin-bottom: 1rem;
}

.spinner-border {
  width: 3rem;
  height: 3rem;
}

.bg-light-blue {
  background-color: #e7f3ff;
}

.text-primary {
  color: #0d6efd !important;
}

.text-danger {
  color: #dc3545 !important;
}

.text-success {
  color: #198754 !important;
}

.text-warning {
  color: #fd7e14 !important;
}
</style>
