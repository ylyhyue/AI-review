<template>
  <div class="container mt-5">
    <h1>Class Management</h1>

    <!-- 添加班级 -->
    <div class="mb-3">
      <input v-model="newClass.classname" placeholder="Class Name" class="form-control mb-2">
      <button @click="addClass" class="btn btn-primary">Add Class</button>
    </div>

    <!-- 班级列表 -->
    <div class="mb-3">
      <h2>Class List</h2>
      <ul class="list-group">
        <li v-for="cls in classes" :key="cls.class_id" class="list-group-item">
          {{ cls.classname }}
          <button @click="deleteClass(cls.class_id)" class="btn btn-danger btn-sm float-end">Delete</button>
          <button @click="toggleExpand(cls.class_id)" class="btn btn-info btn-sm float-end me-2">
            {{ expandedClass === cls.class_id ? 'Collapse' : 'Expand' }}
          </button>
          <button @click="setCoursework(cls.class_id)" class="btn btn-warning btn-sm float-end me-2">Set Coursework</button>
          <button @click="checkStudents(cls.class_id)" class="btn btn-success btn-sm float-end me-2">Check Students</button>
          <!-- 展开的学生列表 -->
        <div v-if="expandedClass === cls.class_id" class="list-group-item bg-light">
          <div class="mb-3">
            <input v-model="searchQuery" placeholder="Search student by name" class="form-control mb-2" @input="searchStudentsNotInClass(cls.class_id)" @click="searchStudentsNotInClass(cls.class_id)">
            <p v-if="errorMessage" class="text-danger">{{ errorMessage }}</p>
            <!-- 显示搜索结果 -->
            <ul v-if="searchResults.length > 0" class="list-group mt-2 scrollable-list">
              <li v-for="student in searchResults" :key="student.student_id" class="list-group-item">
                {{ student.username }}
                <button @click="addStudentToClass(cls.class_id, student.student_id)" class="btn btn-success btn-sm float-end">Add</button>
              </li>
            </ul>
          </div>
          <ul class="list-group">
            <li v-for="student in studentsInClass" :key="student.student_id" class="list-group-item">
              {{ student.username }}
              <button @click="deleteStudentFromClass(cls.class_id, student.student_id)" class="btn btn-danger btn-sm float-end">Delete</button>
            </li>
          </ul>
        </div>
        </li>

      </ul>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue';
import axios from 'axios';
import { useUserStore } from '@/stores/user';

export default {
  methods: {
  setCoursework(classId) {
    // 可以在这里添加一些逻辑，例如验证用户权限
    this.$router.push(`/cw/${classId}`); // 跳转到设置作业页面
  },
    checkStudents(classId) {
    // 可以在这里添加一些逻辑，例如验证用户权限
    this.$router.push(`/check/${classId}`); // 跳转到设置作业页面
  },
},
  setup() {
    const userStore = useUserStore();
    const classes = ref([]);
    const expandedClass = ref(null);
    const studentsInClass = ref([]);
    const searchQuery = ref('');
    const searchResults = ref([]); // 存储搜索结果
    const errorMessage = ref('');
    const newClass = ref({ classname: '' });

    // 获取当前教师的班级
    const fetchClasses = async () => {
      const response = await axios.get(`/api/classes/${userStore.token}`);
      classes.value = response.data;
    };

    // 添加班级
    const addClass = async () => {
      if (!newClass.value.classname) {
        errorMessage.value = 'Class name cannot be empty';
        return;
      }
      const response = await axios.post('/api/class', { classname: newClass.value.classname, creator_id: userStore.token });
      classes.value.push(response.data);
      newClass.value.classname = '';
      errorMessage.value = '';
    };

    // 删除班级
    const deleteClass = async (classId) => {
      await axios.delete(`/api/class/${classId}`);
      classes.value = classes.value.filter(cls => cls.class_id !== classId);
    };

    // 切换展开/收起
    const toggleExpand = async (classId) => {
      if (expandedClass.value === classId) {
        expandedClass.value = null;
      } else {
        expandedClass.value = classId;
        const response = await axios.get(`/api/class/${classId}/students`);
        studentsInClass.value = response.data;
      }
    };

    // 实时搜索不在该班级的学生
    const searchStudentsNotInClass = async (classId) => {

      const response = await axios.get('/api/students/search/not_in_class', {
        params: {
          query: searchQuery.value,
          class_id: classId,
        },
      });
      searchResults.value = response.data;
    };

    // 添加学生到班级
    const addStudentToClass = async (classId, studentId) => {
      if (!studentId) {
        errorMessage.value = 'Please select a student to add';
        return;
      }
      await axios.post(`/api/class/${classId}/student`, { student_id: studentId });
      // 更新学生列表
      const response = await axios.get(`/api/class/${classId}/students`);
      studentsInClass.value = response.data;
      // 清空搜索框和结果
      searchQuery.value = '';
      searchResults.value = [];
      errorMessage.value = '';
    };

    // 从班级中删除学生
    const deleteStudentFromClass = async (classId, studentId) => {
      await axios.delete(`/api/class/${classId}/student/${studentId}`);
      studentsInClass.value = studentsInClass.value.filter(student => student.student_id !== studentId);
    };

    // 初始化数据
    fetchClasses();

    return {
      classes,
      expandedClass,
      studentsInClass,
      searchQuery,
      searchResults,
      errorMessage,
      newClass,
      addClass,
      deleteClass,
      toggleExpand,
      searchStudentsNotInClass,
      addStudentToClass,
      deleteStudentFromClass,
    };
  },
};
</script>
<style scoped>
.bg-light {
  margin-top: 14px;
}
.scrollable-list {
  max-height: 120px; /* 三个 <li> 的高度 */
  overflow-y: auto;  /* 添加垂直滚动条 */
  margin-bottom: 0;  /* 移除默认的外边距 */
  border: 1px solid #ddd; /* 可选：添加边框 */
  border-radius: 4px; /* 可选：添加圆角 */
}
</style>
