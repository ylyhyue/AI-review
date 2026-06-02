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

    <!-- 每个a分组 -->
    <div v-for="a in sortedA" :key="a" class="mb-4">
      <h2 class="mb-3">Cambridge IELTS {{ a }}</h2>
      <!-- 每行最多4个b（Bootstrap网格系统） -->
      <div class="row">
        <div v-for="(item, index) in grouped[a]" :key="index" class="col-md-3 mb-3">
          <!-- 带样式的链接 -->
          <router-link
            :to="`/${bankType}/${a}/${item.b}`"
            class="btn btn-outline-primary w-100 text-truncate"
          >
            Test {{ item.b || '未命名' }}
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const grouped = ref({})
const sortedA = ref([])

// 从路由参数中获取bank_type
const bankType = computed(() => route.params.bank_type)

// 加载数据的函数
const loadData = async () => {
  const response = await axios.get(`/api/banks/${bankType.value}`)
  grouped.value = response.data.grouped
  sortedA.value = response.data.sorted_a
}

// 监听路由参数变化
watch(
  () => route.params.bank_type, // 监听bank_type的变化
  () => {
    loadData() // 重新加载数据
  },
  { immediate: true } // 立即执行一次
)
</script>

<style scoped>
.small {
  font-size: 0.875rem; /* 小一点的字体 */
}

.active-link {
  font-weight: bold; /* 高亮样式 */
  text-decoration: underline; /* 下划线 */
}
</style>
