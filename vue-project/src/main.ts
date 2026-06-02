import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import ElementPlus from 'element-plus'; // 新增：引入 Element Plus
import 'element-plus/dist/index.css';
import axios from 'axios'
axios.defaults.baseURL = 'http://localhost:5000'
const app = createApp(App)
app.config.globalProperties.$axios = axios
app.use(createPinia())
app.use(router)
app.use(ElementPlus);
app.mount('#app')
