<template>

  <div class="container mt-4">
    <!-- 标题 -->
    <h1 class="mb-4">Cambridge IELTS {{ bankType.charAt(0).toUpperCase() + bankType.slice(1) }} Subject training</h1>

    <div class="d-flex flex-wrap align-items-center mb-4">
    <!-- All Test 链接 -->
    <router-link
      :to="`/${bankType}`"
      class="me-3 mb-2 text-decoration-none small"
      :class="{ 'active-link': !route.params.a }"
    >
      All Test
    </router-link>

    <!-- 每个a分组的链接 -->
    <router-link
      v-for="a in sortedA"
      :key="a"
      :to="`/${bankType}/${a}/1`"
      class="me-3 mb-2 text-decoration-none small"
      :class="{ 'active-link': route.params.a === a }"
    >
      Cambridge IELTS {{ a }}
    </router-link>
  </div>
    <!-- 渲染所有b分组 -->
    <div v-for="(group, b) in groupedData" :key="b" class="mb-4">
      <!-- 每个b分组的标题 -->
      <h3 :ref="setGroupRef(b)" class="mb-3">
       Test {{ b }}
      </h3>

      <!-- 每个b分组的内容 -->
      <div v-for="item in group" :key="item.display_order" class="card mb-2 hover-card">
    <!-- 整个盒子是超链接 -->
    <router-link
      :to="`/${bankType}/${route.params.a}/${b}/${item.display_order}`"
      class="text-decoration-none text-dark"
    >
      <div class="card-body">
        <!-- Passage {{ item.display_order }} -->
        <h5 class="card-title mb-1">
          Passage {{ item.display_order }}
        </h5>
        <!-- 小一点的字体，颜色淡一点的 {{ item.bank_name }} -->
        <p class="card-text text-muted small">
          {{ item.bank_name }}
        </p>
      </div>
    </router-link>
  </div>

    </div>
  </div>
</template>

<script setup>
import {ref, onMounted, watch, computed} from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const groupedData = ref({}) // 存储分组后的数据
const groupRefs = ref({}) // 存储每个b分组的DOM引用
const grouped = ref({})
const sortedA = ref([])

// 从路由参数中获取bank_type
const bankType = computed(() => route.params.bank_type)
// 加载数据的函数
const loadData = async () => {
  try {
    // 请求1：获取分组数据
    const response1 = await axios.get(`/api/banks/${bankType.value}`);
    grouped.value = response1.data.grouped;
    sortedA.value = response1.data.sorted_a;

    // 请求2：获取当前a分组的详细数据
    if (route.params.a) {
      const response2 = await axios.get(
        `/api/banks/${route.params.bank_type}/${route.params.a}`
      );
      groupedData.value = response2.data;
    }
  } catch (error) {
    console.error('加载数据失败:', error);
  }
};

// 设置每个b分组的DOM引用
const setGroupRef = (b) => (el) => {
  if (el) {
    groupRefs.value[b] = el
  }
}

// 滚动到指定的b分组
const scrollToGroup = (b) => {
  const target = groupRefs.value[b]
  if (target) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// 监听路由参数变化
watch(
  () => route.params, // 监听所有路由参数的变化
  async () => {
    await loadData() // 重新加载数据
    scrollToGroup(route.params.b) // 滚动到指定的b分组
  },
  { immediate: true } // 立即执行一次
)
</script>
<style scoped>
/* 鼠标悬停效果 */
.hover-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.hover-card:hover {
  transform: scale(1.02); /* 盒子稍微扩大 */
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3); /* 蓝光阴影 */
}

/* 卡片链接样式 */
.card {
  cursor: pointer; /* 鼠标悬停时显示手型 */
}

/* 小字体样式 */
.small {
  font-size: 0.875rem; /* 14px */
}

/* 链接样式 */
.text-decoration-none {
  text-decoration: none; /* 去掉下划线 */
}

.text-dark {
  color: inherit; /* 继承父元素颜色 */
}
.active-link {
  font-weight: bold; /* 高亮样式 */
  text-decoration: underline!important; /* 下划线 */
}
</style>
