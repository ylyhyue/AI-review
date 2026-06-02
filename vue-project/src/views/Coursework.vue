<template>
  <div class="container mt-5">
    <!-- 班级名称 -->
    <h1>Class: {{ className }}</h1>

    <!-- 创建作业 -->
    <div class="mb-5">
      <h2>Create Coursework</h2>
      <div class="mb-3">
        <label for="courseworkType" class="form-label">Coursework Type</label>
        <select v-model="newCoursework.type" id="courseworkType" class="form-select" @change="resetSearch">
          <option value="writing">Writing</option>
          <option value="listening">Listening</option>
          <option value="reading">Reading</option>
        </select>
      </div>

      <!-- 选择 location A -->
      <div class="mb-3">
        <label for="locationA" class="form-label">Cambridge IELTS</label>
        <select v-model="bankSearch.locationA" id="locationA" class="form-select" @change="fetchUniqueB">
          <option v-for="a in uniqueA" :key="a" :value="a">{{ a }}</option>
        </select>
      </div>

      <!-- 选择 location B -->
      <div class="mb-3">
        <label for="locationB" class="form-label">Test</label>
        <select v-model="bankSearch.locationB" id="locationB" class="form-select" @change="fetchUniqueOrder">
          <option v-for="b in uniqueB" :key="b" :value="b">{{ b }}</option>
        </select>
      </div>

      <!-- 选择 order 和 bank_name -->
      <div class="mb-3">
        <label for="order" class="form-label">Order and Bank Name</label>
        <select v-model="bankSearch.selectedOrder" id="order" class="form-select">
          <option v-for="order in uniqueOrder" :key="order.bank_id" :value="order">
            {{ order.order }} - {{ order.bank_name }}
          </option>
        </select>
      </div>

      <!-- 添加题库到作业 -->
      <button @click="addBankToCoursework" class="btn btn-primary">Add Bank</button>

      <!-- 已添加的题库 -->
      <div v-if="newCoursework.banks.length > 0" class="mb-3">
        <h3>Added Banks</h3>
        <ul class="list-group">
          <li v-for="(bank, index) in newCoursework.banks" :key="index" class="list-group-item">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <p>Type: {{ bank.type }}</p>
                <p>Location: {{ bank.locationA }}:{{ bank.locationB }}</p>
                <p>Order: {{ bank.order }}</p>
                <p>Bank Name: {{ bank.bank_name }}</p>
              </div>
              <button @click="removeBankFromCoursework(index)" class="btn btn-danger btn-sm">Delete</button>
            </div>
          </li>
        </ul>
      </div>

      <!-- 设置截止日期 -->
      <div class="mb-3">
        <label for="deadline" class="form-label">Deadline</label>
        <input v-model="newCoursework.deadline" type="datetime-local" id="deadline" class="form-control">
      </div>

      <!-- 互评设置（仅当 Added Banks 中有 Writing 类型时显示） -->
      <div v-if="hasWritingBank" class="mb-3">
        <label for="reviewCount" class="form-label">Number of Peer Reviews</label>
        <input v-model="newCoursework.reviewCount" type="number" id="reviewCount" class="form-control mb-2">
        <label for="reviewType" class="form-label">Review Type</label>
        <select v-model="newCoursework.reviewType" id="reviewType" class="form-select">
          <option value="single-blind">Single-blind</option>
          <option value="double-blind">Double-blind</option>
          <option value="open">Open</option>
        </select>
      </div>

      <!-- 发布作业 -->
      <button @click="publishCoursework" class="btn btn-primary">Publish Coursework</button>
    </div>

    <!-- 已发布作业列表 -->
    <div>
      <h2>Published Coursework</h2>
      <ul class="list-group">
        <li v-for="coursework in courseworkList" :key="coursework.cw_id" class="list-group-item">
          <div @click="toggleCourseworkDetail(coursework.cw_id)" class="d-flex justify-content-between align-items-center">
            <span>Deadline: {{ formatDate(coursework.deadline) }}</span>
            <button class="btn btn-info btn-sm">
              {{ expandedCoursework === coursework.cw_id ? 'Collapse' : 'Expand' }}
            </button>
          </div>
          <!-- 作业详情 -->
          <div v-if="expandedCoursework === coursework.cw_id" class="mt-2">
            <p>Created At: {{ formatDate(coursework.create_time) }}</p>
            <p v-if="coursework.review_set">Review Set: {{ coursework.review_set }}</p>
            <p>Banks:</p>
            <!-- 按 type 分类显示 banks -->
            <div v-for="type in ['writing', 'listening', 'reading']" :key="type">
              <div v-if="getBanksByType(coursework.banks, type).length > 0">
                <h5>{{ type.charAt(0).toUpperCase() + type.slice(1) }}</h5>
                <ul>
                  <li v-for="bank in getBanksByType(coursework.banks, type)" :key="bank.bank_id">
                    <p>Cambridge IELTS  {{ bank.location_a }} Test {{ bank.location_b }} {{ bank.display_order }}. {{ bank.bank_name }}</p>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      classId: this.$route.params.classId, // 从路由参数获取 classId
      className: '', // 班级名称
      studentCount: 0, // 班级学生人数
      newCoursework: {
        type: 'writing', // 作业类型
        banks: [], // 已添加的题库
        deadline: '', // 截止日期
        reviewCount: 1, // 互评数量
        reviewType: 'single-blind', // 互评类型
      },
      bankSearch: {
        locationA: '', // 题库搜索的 Location A
        locationB: '', // 题库搜索的 Location B
        selectedOrder: null, // 选择的 order 和 bank_name
      },
      uniqueA: [], // 唯一的 location A 列表
      uniqueB: [], // 唯一的 location B 列表
      uniqueOrder: [], // 唯一的 order 和 bank_name 列表
      courseworkList: [], // 已发布的作业列表
      expandedCoursework: null, // 当前展开的作业 ID
    };
  },
  computed: {
    // 判断 Added Banks 中是否有 Writing 类型
    hasWritingBank() {
      return this.newCoursework.banks.some(bank => bank.type === 'writing');
    },
  },
  created() {
    this.fetchClassName();
    this.fetchCourseworkList();
    this.fetchUniqueA(); // 默认加载 writing 的 location A
  },
  watch: {
    // 监听作业类型变化
    'newCoursework.type': function () {
      this.resetSearch();
      this.fetchUniqueA();
    },
  },
  methods: {
    // 获取班级名称和学生人数
    async fetchClassName() {
      const response = await axios.get(`/api/class/${this.classId}`);
      this.className = response.data.classname;
      this.studentCount = response.data.student_count;
    },
    // 获取唯一的 location A
    async fetchUniqueA() {
      const response = await axios.get('/api/bank/unique_a', {
        params: { type: this.newCoursework.type },
      });
      this.uniqueA = response.data;
    },
    // 获取唯一的 location B
    async fetchUniqueB() {
      if (!this.bankSearch.locationA) return;
      const response = await axios.get('/api/bank/unique_b', {
        params: { type: this.newCoursework.type, a: this.bankSearch.locationA },
      });
      this.uniqueB = response.data;
      this.bankSearch.locationB = ''; // 清空 location B
      this.bankSearch.selectedOrder = null; // 清空 order
    },
    // 获取唯一的 order 和 bank_name
    async fetchUniqueOrder() {
      if (!this.bankSearch.locationB) return;
      const response = await axios.get('/api/bank/unique_order', {
        params: {
          type: this.newCoursework.type,
          a: this.bankSearch.locationA,
          b: this.bankSearch.locationB,
        },
      });
      this.uniqueOrder = response.data;
      this.bankSearch.selectedOrder = null; // 清空 order
    },
    // 按 type 分类获取 banks
    getBanksByType(banks, type) {
      return banks.filter(bank => bank.bank_type === type);
    },
    // 重置搜索条件
    resetSearch() {
      this.bankSearch = { locationA: '', locationB: '', selectedOrder: null };
      this.uniqueB = [];
      this.uniqueOrder = [];
    },
    // 添加题库到作业
    addBankToCoursework() {
      if (this.bankSearch.selectedOrder) {
        // 检查是否已添加
        const isDuplicate = this.newCoursework.banks.some(
          bank => bank.bank_id === this.bankSearch.selectedOrder.bank_id
        );
        if (isDuplicate) {
          alert('This bank has already been added.');
          return;
        }
        const bank = {
          type: this.newCoursework.type,
          locationA: this.bankSearch.locationA,
          locationB: this.bankSearch.locationB,
          order: this.bankSearch.selectedOrder.order,
          bank_name: this.bankSearch.selectedOrder.bank_name,
          bank_id: this.bankSearch.selectedOrder.bank_id, // 添加 bank_id
        };
        this.newCoursework.banks.push(bank);
        this.resetSearch(); // 清空搜索条件
      }
    },
    // 从作业中移除题库
    removeBankFromCoursework(index) {
      this.newCoursework.banks.splice(index, 1);
    },
    // 发布作业
    async publishCoursework() {
      // 验证截止日期是否晚于当前时间
      if (new Date(this.newCoursework.deadline) <= new Date()) {
        alert('Deadline must be later than current time.');
        return;
      }
      // 验证互评数量是否合法
      if (this.hasWritingBank) {
        if (this.newCoursework.reviewCount <= 0 || this.newCoursework.reviewCount >= this.studentCount) {
          alert('Number of peer reviews must be greater than 0 and less than the number of students.');
          return;
        }
      }
      // 准备数据
      const payload = {
        class_id: this.classId,
        type: this.newCoursework.type,
        banks: this.newCoursework.banks.map(bank => bank.bank_id), // 使用 bank_id
        deadline: this.newCoursework.deadline,
        review_set: this.hasWritingBank
          ? `Reviews: ${this.newCoursework.reviewCount}, Type: ${this.newCoursework.reviewType}`
          : null,
        student_count: this.studentCount,
      };
      // 提交数据
      try {
        await axios.post('/api/coursework', payload);
        this.newCoursework = { type: 'writing', banks: [], deadline: '', reviewCount: 1, reviewType: 'single-blind' };
        this.fetchCourseworkList(); // 刷新作业列表
      } catch (error) {
        alert('Failed to publish coursework.');
      }
    },
    // 获取作业列表
    async fetchCourseworkList() {
      const response = await axios.get('/api/coursework', { params: { classId: this.classId } });
      this.courseworkList = response.data;
    },
    // 切换作业详情
    toggleCourseworkDetail(cwId) {
      this.expandedCoursework = this.expandedCoursework === cwId ? null : cwId;
    },
    // 格式化日期
    formatDate(dateString) {
      return new Date(dateString).toLocaleString();
    },
  },
};
</script>

<style scoped>
.list-group-item {
  cursor: pointer;
}
</style>
