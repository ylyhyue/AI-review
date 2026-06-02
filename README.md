# IELTS Master — AI 驱动的雅思写作同行评审系统

一个面向雅思写作教学的全栈 Web 应用，集成 DeepSeek AI 自动评分与学生 Peer Review 机制，帮助教师高效管理课堂、学生获得多维度写作反馈。

## 核心功能

### 学生端
- **IELTS Writing 练习** — Task 1（图表题）和 Task 2（议论文），内置计时器模拟真实考试
- **AI 自动评分** — 提交后由 DeepSeek Reasoner 按官方 Band Descriptors 从 TA/CC/LR/GRA 四维度打分（1-9 分），给出具体改进建议
- **Peer Review** — 学生之间匿名/实名互评，教师可自定义评审规则
- **IELTS 题库** — 覆盖 Writing / Reading / Listening 三科，按 Test → Passage 分层浏览
- **学生仪表盘** — 查看已提交作文、AI 评分和 Peer Review 反馈

### 教师端
- **班级管理** — 创建班级、添加/移除学生
- **题库管理** — 完整 CRUD，管理 Bank / BigQuestion / SmallQuestion / Resource（图片和文本）
- **作业发布** — 为班级布置作业，关联题库，设置截止时间和评审规则
- **学生数据** — 查看班级学生的提交记录和评分详情

### AI 评分系统
- DeepSeek Reasoner 模型 + 精心设计的 System Prompt
- 评分标准严格对齐 IELTS 官方 Band Descriptors
- Task 1 和 Task 2 两套独立评分体系
- 返回结构化四维分数 + 详细文字反馈
- 自动验证分数范围（1-9），异常分数被拦截

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3 + Flask + Flask-SQLAlchemy + SQLite |
| AI | DeepSeek Reasoner（通过 OpenAI SDK 调用） |
| 前端 | Vue 3 + TypeScript + Vue Router + Pinia + Element Plus + Bootstrap 5 |
| 构建 | Vite |
| 测试 | Vitest（单元）+ Cypress（E2E） |
| 认证 | Werkzeug 密码哈希 + Token |

## 项目结构

```
.
├── app.py                    # Flask 后端（47 个 API 端点，15 个数据模型）
├── requirements.txt          # Python 依赖
├── .env.example              # 环境变量模板
├── package.json              # 根目录依赖
└── vue-project/              # Vue 3 前端
    ├── src/
    │   ├── App.vue           # 主布局（导航 + 路由 + 页脚）
    │   ├── main.ts           # 入口
    │   ├── router/index.ts   # 路由配置（含角色权限守卫）
    │   ├── stores/user.js    # 用户状态管理（Pinia）
    │   └── views/
    │       ├── Practice.vue          # 写作练习（计时器 + AI 评分）
    │       ├── PeerReview.vue        # Peer Review 列表
    │       ├── Review.vue            # 评审详情
    │       ├── Submission.vue        # 提交详情
    │       ├── StudentDashboard.vue  # 学生仪表盘
    │       ├── TeacherDashboard.vue  # 教师仪表盘
    │       ├── BankManage.vue        # 题库管理（教师）
    │       ├── BankList.vue          # 题库列表
    │       ├── BankDetail.vue        # 题目详情
    │       ├── Coursework.vue        # 作业管理
    │       ├── CheckStudent.vue      # 学生查看
    │       ├── Listening.vue         # 听力练习
    │       ├── LoginView.vue         # 登录
    │       ├── RegisterView.vue      # 注册
    │       └── HomeView.vue          # 首页
    └── ...
```

## 数据库设计

系统包含 15 个数据表：

| 表名 | 说明 |
|------|------|
| Student / Teacher | 用户（学生 + 教师） |
| Class / StudentCourses | 班级与学生关联 |
| Bank / BigQuestion / SmallQuestion / Resource | 题库层级结构 |
| Coursework / CwBank | 作业与题库关联 |
| Submission / Answer | 学生提交与答题记录 |
| PeerReview / Matching / DetectionResults | 评审、匹配与检测 |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
```

### 2. 启动后端

```bash
pip install -r requirements.txt
python app.py
# 默认运行在 http://localhost:5000
```

### 3. 启动前端

```bash
cd vue-project
npm install
npm run dev
# 默认运行在 http://localhost:5173
```

## API 概览

系统提供 47 个 RESTful API 端点：

| 模块 | 端点 | 说明 |
|------|------|------|
| 认证 | POST /api/register, /api/login | 注册、登录 |
| 题库 | GET /api/banks/{type} | 按类型查询题库 |
| 作业 | POST/GET /api/coursework | 作业 CRUD |
| 提交 | POST /api/submit | 作文提交（触发 AI 评分） |
| 评审 | GET /api/to-review, /api/received-reviews | Peer Review 管理 |
| 班级 | POST/GET/DELETE /api/class | 班级管理 |
| 资源 | POST/PUT/DELETE /api/resource | 题库资源 CRUD |
| 学生 | GET /api/check/{class_id} | 学生数据查看 |

## License

MIT
