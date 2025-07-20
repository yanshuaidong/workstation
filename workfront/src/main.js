import { createApp, markRaw } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import './assets/init.css'

const app = createApp(App)

// 使用 Element Plus
app.use(ElementPlus)

// 使用路由
app.use(router)

// 注册所有图标，使用 markRaw 避免响应式警告
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, markRaw(component))
}

app.mount('#app')
