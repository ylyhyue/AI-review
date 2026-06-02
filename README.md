# IELTS Master - AI Powered Peer Review System

一个面向雅思写作教学的全栈 Web 应用，集成 DeepSeek AI 自动评分与学生 Peer Review 机制，帮助教师高效管理课堂、学生获得多维度写作反馈。

## 核心功能

### 学生端
- **IELTS Writing 练习**：支持 Task 1（图表题）和 Task 2（议论文），内置计时器模拟真实考试环境
- **AI 自动评分**：提交作文后由 DeepSeek Reasoner 按照官方 Band Descriptors 从 TA/CC/LR/GRA 四个维度打分（1-9 分），并给出具体改进建议
- **Peer Review**：学生之间匿名/实名互评，支持教师自定义评审规则（开放评审、匿名评审等）
- **IELTS 题库练习**：覆盖 Writing / Reading / Listening 三个科目，按 Test → Passage 分层浏览
- **学生仪表盘**：查看已提交作文、收到的 AI 评分和 Peer Review 反馈

### 教师端
- **班级管理**：创建班级、添加/移除学生、查看学生列表
- **题库管理（Bank Management）**：完整的 CRUD 操作，管理题库（Bank）、大题（BigQuestion）、小题（SmallQuestion）、资源（Resource，支持图片和文本）
- **作业发布（Coursework）**：为班级布置作业，关联题库，设置截止时间和评审规则
- **学生数据查看**：查看班级学生的提交记录和评分详情
- **教师仪表盘**：总览班级、作业、学生活动

### AI 评分系统
- 基于 DeepSeek Reasoner 模型，通过精心设计的 System Prompt 实现
- 评分标准严格对齐 IELTS 官方 Band Descriptors
- 支持 Task 1 和 Task 2 两套独立评分体系
- 返回结构化评分（四个维度分数）+ 详细文字反馈
- 自动验证分数范围（1-9），异常分数会被拦截

## 技术栈

### 后端
- **Python 3** + **Flask**
- **Flask-SQLAlchemy** + **SQLite**（数据库 ORM）
- **Flask-CORS**（跨域支持）
- **OpenAI Python SDK**（调用 DeepSeek API）
- Werkzeug（密码哈希、文件上传）

### 前端
- **Vue 3** + **TypeScript**
- **Vue Router**（路由管理，含角色守卫）
- **Pinia**（状态管理）
- **Element Plus**（UI 组件库）
- **Bootstrap 5**（布局和样式）
- **Vite**（构建工具）
- **Vitest** + **Cypress**（单元测试 + E2E 测试）

## 项目结构

```
.
├── app.py                          # Flask 后端（47 个 API 端点，15 个数据模型）
├── package.json                    # 根目录依赖
├── vue-project/                    # Vue 3 前端
│   ├── src/
│   │   ├── App.vue                 # 主布局（导航栏 + 路由视图 + 页脚）
│   │   ├── main.ts                 # 入口文件
│   │   ├── router/index.ts         # 路由配置（含角色权限守卫）
│   │   ├── stores/user.js          # 用户状态管理（Pinia）
│   │   ├── views/
│   │   │   ├── Practice.vue        # IELTS 写作练习页（计时器 + AI 评分）
│   │   │   ├── PeerReview.vue      # Peer Review 列表页
│   │   │   ├── Review.vue          # 评审详情页
│   │   │   ├── Submission.vue      # 提交详情页
│   │   │   ├── StudentDashboard.vue# 学生仪表盘
│   │   │   ├── TeacherDashboard.vue# 教师仪表盘
│   │   │   ├── BankManage.vue      # 题库管理（教师）
│   │   │   ├── BankList.vue        # 题库列表
│   │   │   ├── BankDetail.vue      # 题目详情
│   │   │   ├── Coursework.vue      # 作业管理
│   │   │   ├── CheckStudent.vue    # 学生查看
│   │   │   ├── LoginView.vue       # 登录
│   │   │   ├── RegisterView.vue    # 注册
│   │   │   └── HomeView.vue        # 首页
│   │   └── assets/                 # 静态资源
│   └── ...                         # Vite / TS / ESLint 配置
```

## 数据库设计

系统包含 15 个数据表：

| 表名 | 说明 |
|------|------|
| Student | 学生用户 |
| Teacher | 教师用户 |
| Class | 班级 |
| StudentCourses | 学生-班级关联 |
| Bank | 题库/试卷 |
| BigQuestion | 大题 |
| SmallQuestion | 小题 |
| Resource | 资源（图片/文本） |
| Coursework | 作业 |
| CwBank | 作业-题库关联 |
| Submission | 学生提交 |
| Answer | 答题记录 |
| PeerReview | Peer Review 记录（含 AI 评分） |
| Matching | 评审匹配关系 |
| DetectionResults | 评审检测结果 |

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- npm 或 pnpm

### 后端启动

```bash
# 安装依赖
pip install flask flask-sqlalchemy flask-cors openai werkzeug

# 配置 DeepSeek API Key（在 app.py 中修改）
# client = OpenAI(api_key="your-api-key", base_url="https://api.deepseek.com")

# 启动 Flask 服务
python app.py
```

### 前端启动

```bash
cd vue-project

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## API 概览

系统提供 47 个 RESTful API 端点，主要包括：

- `/api/register`, `/api/login` — 用户认证
- `/api/banks/<bank_type>` — 题库查询
- `/api/submit` — 作文提交（触发 AI 评分）
- `/api/peer_review` — Peer Review 相关
- `/api/class`, `/api/classes` — 班级管理
- `/api/coursework` — 作业管理
- `/api/resource`, `/api/bank` — 题库资源 CRUD
- `/api/check/<class_id>` — 学生数据查看