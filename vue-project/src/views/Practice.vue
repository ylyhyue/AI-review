<template>
  <div class="container-fluid">
    <!-- 顶部导航栏 -->
    <nav class="navbar navbar-light bg-light fixed-top">
      <div class="container-fluid">
        <!-- 计时器 -->
        <div class="mx-auto">
          <span class="navbar-text">
            Timer : {{ formattedTime }}
          </span>
        </div>
         <!-- 暂停按钮 -->
        <button class="btn btn-warning me-2" @click="pauseTimer">
          Pause
        </button>
        <!-- 提交按钮 -->
        <button class="btn btn-primary" @click="submit">
          Submit
        </button>
      </div>
    </nav>
  <!-- 暂停模态框 -->
    <div class="modal fade" id="pauseModal" tabindex="-1" aria-labelledby="pauseModalLabel" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="pauseModalLabel">Pause</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            The timer is paused. Click "Continue" to resume the timer.
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
              Continue
            </button>
          </div>
        </div>
      </div></div>

    <!-- 主要内容 -->
    <div class="row mt-5 pt-3">
      <!-- 左半边 -->
      <div class="col-md-6 left-column">
        <h2 class="text-center">{{ bank.bank_name }}</h2>

        <!-- 图片资源 -->
        <div v-if="hasPicture">
          <img
            v-for="resource in pictureResources"
            :key="resource.resource_id"
            :src="resource.resource_information"
            class="img-fluid mb-3"
            alt="picture"
          />
        </div>

        <!-- 文本资源 -->
        <div v-if="hasText">
          <p
            v-for="resource in textResources"
            :key="resource.resource_id"
            class="mb-3"
            v-html="formatText(resource.resource_information)"
          ></p>
        </div>
      </div>

      <!-- 右半边 -->
      <div class="col-md-6 right-column">
        <div v-for="(bigQuestion) in bigQuestions" :key="bigQuestion.big_id" class="mb-4">
          <!-- 大题标题 -->
          <h4 v-if="bigQuestion.start_number != null">Question {{ bigQuestion.start_number }}-{{ bigQuestion.end_number }}</h4>

          <!-- 题目描述 -->
          <p class="mb-2" v-html="formatText1(bigQuestion.question_description)"></p>

          <!-- NB提示 -->
          <p v-if="bigQuestion.if_nb === 1" class="text-muted fst-italic mb-3">
            <b>NB</b> You may use any letter more than once.
          </p>

          <!-- 小题内容 -->
          <div v-for="smallQuestion in bigQuestion.small_questions" :key="smallQuestion.question_number" class="mb-3">
            <!-- 判断题型 -->
            <div v-if="bigQuestion.type === 'judgement'">
              <p class="fw-bold">Question {{ smallQuestion.question_number }}</p>
              <p v-html="formatText(smallQuestion.question_content)"></p>
              <div class="ms-3">
                <!-- 从 question_options 中读取选项 -->
                <div v-for="(option, optIndex) in parseOptions(smallQuestion.question_options)"
                     :key="optIndex"
                     class="form-check">
                  <input class="form-check-input"
                         type="radio"
                         :name="'q'+smallQuestion.question_number"
                         :id="'q'+smallQuestion.question_number+'_'+optIndex"
                         v-model="judgementAnswers[smallQuestion.question_number]"
                  :value="option">
                  <label class="form-check-label"
                         :for="'q'+smallQuestion.question_number+'_'+optIndex"
                         v-html="option"></label>
                </div>
              </div>
            </div>
            <div v-if="bigQuestion.type === 'fill_in'">
    <p>
      <span v-for="(part, index) in parseFillInText(smallQuestion.question_content, smallQuestion.question_number)"
            :key="index">
        <template v-if="part.isInput">
          <input
            type="text"
            class="fill-in-input"
            :placeholder="part.placeholder"
            v-model="fillInInputs[part.questionNumber]"
          />
        </template>
        <template v-else>
          {{ part.text }}
        </template>
      </span>
    </p>
  </div>
<div v-if="bigQuestion.type === 'choice'">
  <p class="fw-bold">Question {{ smallQuestion.question_number }}</p>
              <p v-html="formatText(smallQuestion.question_content)"></p>
              <div class="ms-3">
                <!-- 从 question_options 中读取选项 -->
                <div v-for="(option, optIndex) in parseOptions(smallQuestion.question_options)"
                     :key="optIndex"
                     class="form-check">
                  <input class="form-check-input"
                         type="radio"
                         :name="'q'+smallQuestion.question_number"
                         :id="'q'+smallQuestion.question_number+'_'+optIndex"
                         v-model="chooseAnswers[smallQuestion.question_number]"
                  :value="option">
                  <label class="form-check-label"
                         :for="'q'+smallQuestion.question_number+'_'+optIndex"
                         v-html="option"></label>
                </div>
              </div>
  </div>






          </div>

 <!-- 小题内容 -->
  <div v-if="bigQuestion.type === 'matching'">
    <!-- 匹配题表格（仅渲染一次） -->
    <div class="ms-3">
      <table class="table table-bordered">
        <!-- 表头（第一行是选项） -->
        <thead>
          <tr>
            <th></th> <!-- 第一格空着 -->
            <th v-for="(option, colIndex) in parseOptions(bigQuestion.small_questions[0].question_options)"
                :key="colIndex">
              {{ option }}
            </th>
          </tr>
        </thead>
        <!-- 表格内容（每行对应一个 smallQuestion.question_content） -->
        <tbody>
          <tr v-for="(smallQuestion, rowIndex) in bigQuestion.small_questions"
              :key="rowIndex">
            <td><b>{{smallQuestion.question_number}}</b>  {{ smallQuestion.question_content }}</td> <!-- 第一列是问题描述 -->
            <td v-for="(_, colIndex) in parseOptions(bigQuestion.small_questions[0].question_options)"
                :key="colIndex">
              <input
                type="checkbox"
                :checked="matchAnswers[smallQuestion.question_number]?.[colIndex]"
                @click="handleCheckboxClick(smallQuestion.question_number, colIndex)"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>



          <div v-if="bigQuestion.type === 'multiple_choice'">
  <template v-for="(smallQuestion, index) in bigQuestion.small_questions" :key="smallQuestion.question_number">
    <div v-if="index === 0">
      <p class="fw-bold">Question {{ smallQuestion.question_number }}-{{ smallQuestion.question_number + 1 }}</p>
      <p v-html="formatText(smallQuestion.question_content)"></p>
      <div class="ms-3">
        <div v-for="(option, optIndex) in parseOptions(smallQuestion.question_options)"
             :key="optIndex"
             class="form-check">
          <input class="form-check-input"
                 type="checkbox"
                 :name="'q'+smallQuestion.question_number"
                 :id="'q'+smallQuestion.question_number+'_'+optIndex"
                 :disabled="isOptionDisabled(smallQuestion.question_number, optIndex)"
                 v-model="multiChoiceAnswers[smallQuestion.question_number]"
                 :value="optIndex"> <!-- 绑定选项的索引 -->
          <label class="form-check-label"
                 :for="'q'+smallQuestion.question_number+'_'+optIndex"
                 v-html="option"></label>
        </div>
      </div>
    </div>
  </template>
</div>
<div v-if="bigQuestion.type === 'summary'">
    <!-- 无选项的 summary -->

    <div v-if="!hasOptions(bigQuestion)">
      <p class="summary-paragraph">
        <span v-for="(part, index) in parseSummaryText(bigQuestion.small_questions[0].question_content)"
              :key="index">
          <!-- 如果是输入框 -->
          <template v-if="part.isInput">
            <input
              type="text"
              class="fill-in-input"
              :placeholder="part.placeholder"
              v-model="summaryAnswers[part.index+1]"
            />
          </template>
          <!-- 如果是普通文本 -->
          <template v-else>
            {{ part.text }}
          </template>
        </span>
      </p>
    </div>

    <!-- 有选项的 summary -->
    <div v-else>
   <p class="summary-paragraph">
      <span v-for="(part, index) in parseSummaryText(bigQuestion.small_questions[0].question_content)"
          :key="index">
      <template v-if="part.isInput">
        <span class="input-wrapper" @dragover.prevent
               @drop="handleDrop($event, bigQuestion, part.index)">
          <input
            type="text"
            class="fill-in-input"
            v-model="summaryAnswers[part.index+1]"
            :placeholder="part.placeholder"
            readonly
            :title="summaryAnswers[part.index+1]"
          />
        </span>
      </template>
      <template v-else>
        {{ part.text }}
      </template>
    </span>
    </p>

    <!-- 选项区域 -->
    <div class="options-container">
      <div
         v-for="(option, optionIndex) in bigQuestion.if_nb === 1
             ? parseOptions(bigQuestion.small_questions[0].question_options)
             : getAvailableOptions(bigQuestion)"
        :key="optionIndex"
        class="option-box"
        draggable="true"
        @dragstart="handleDragStart($event, option)"
      >
        {{ option }}
      </div>
    </div>
  </div>
  </div>

          <div v-if="bigQuestion.type === 'write'">


        <!-- 单词计数器 -->
        <div class="mb-3">
          <span class="text-muted">Word Count: {{ wordCount(bigQuestion.big_id) }}</span>
        </div>

        <!-- 大的输入框 -->
        <textarea
          class="write-input"
          v-model="writeAnswers[bigQuestion.big_id]"
          placeholder="Type your answer here..."
        ></textarea>
      </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from "vue";
import { useRoute, useRouter,onBeforeRouteLeave } from "vue-router";
import axios from "axios";
import { Modal } from "bootstrap";
const route = useRoute();
const router = useRouter();
const bank = ref({});
const resources = ref([]);
const bigQuestions = ref([]);
const timer = ref(0);
let interval = null;
const isPaused = ref(false);
// 定义各题型的答案存储
const judgementAnswers = ref({});
const fillInInputs = ref({});
const multiChoiceAnswers = ref({});
const matchAnswers = ref([]);
const summaryAnswers = ref({});
const writeAnswers = ref({});
const chooseAnswers = ref({});
// 定义存储键（可根据题库、显示顺序等生成唯一键）
const storageKey = computed(() => {
  return `timer-${route.params.bank_type}-${route.params.a}-${route.params.b}-${route.params.display_order}`;
});

// 为各类型答案定义独立的存储键
const storageKeyFillIn = computed(() => `${storageKey.value}-fillIn`);
const storageKeyMultiChoice = computed(() => `${storageKey.value}-multiChoice`);
const storageKeyMatch = computed(() => `${storageKey.value}-match`);
const storageKeySummary = computed(() => `${storageKey.value}-summary`);
const storageKeyJudgement = computed(() => `${storageKey.value}-judgement`);
const storageKeyWrite = computed(() => `${storageKey.value}-write`);
const storageKeyChoose = computed(() => `${storageKey.value}-choose`);

// 加载数据
const loadData = async () => {
  const response = await axios.get(
    `/api/bank-details/${route.params.bank_type}/${route.params.a}/${route.params.b}/${route.params.display_order}`
  );
  bank.value = response.data.bank;
  resources.value = response.data.resources;
  bigQuestions.value = response.data.big_questions;
};

// 解析选项（处理 JSON 字符串）
const parseOptions = (options) => {
  try {
    return JSON.parse(options) || [];
  } catch (e) {
    return options ? [options] : [];
  }
};

// 过滤图片资源和文本资源
const pictureResources = computed(() =>
  resources.value.filter(resource => resource.resource_type === "picture")
);
const textResources = computed(() =>
  resources.value.filter(resource => resource.resource_type === "TEXT")
);
const hasPicture = computed(() => pictureResources.value.length > 0);
const hasText = computed(() => textResources.value.length > 0);

// 格式化计时器
const formattedTime = computed(() => {
  const minutes = Math.floor(timer.value / 60);
  const seconds = timer.value % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
});

// 格式化文本（将换行符替换为 <br>）
const formatText = (text) => {
  return text.replace(/\n/g, "<br>");
};
const formatText1 = (text) => {
  // 1. 将换行符替换为 <br>
  let formattedText = text.replace(/\n/g, "<br>");

  // 2. 检测全部由大写字母组成的单词，并加粗
  formattedText = formattedText.replace(/\b([A-Z]+)\b/g, "<strong>$1</strong>");

  return formattedText;
};

// 解析填空题内容
const parseFillInText = (text, questionNumber) => {
  const parts = [];
  const regex = /{{question_number}}/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // 添加普通文本
    if (match.index > lastIndex) {
      parts.push({
        text: text.slice(lastIndex, match.index),
        isInput: false,
      });
    }
    // 添加输入框
    parts.push({
      isInput: true,
      placeholder: questionNumber,
      questionNumber: questionNumber,
    });
    lastIndex = regex.lastIndex;
  }
  // 添加剩余的普通文本
  if (lastIndex < text.length) {
    parts.push({
      text: text.slice(lastIndex),
      isInput: false,
    });
  }
  return parts;
};
// 计算单词数量
const wordCount = (bigId) => {
  const answer = writeAnswers.value[bigId];
  // 安全处理
  const words = (typeof answer === 'string' ? answer.trim() : '')
               .split(/[\s,.!?;:]+/)
               .filter(word => word.length > 0);
  return words.length;
};
// 解析 Summary 题型内容
const parseSummaryText = (text) => {
  const parts = [];
  const regex = /\{\{(\d+)\}\}/g; // 匹配 {{n}} 占位符
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // 添加普通文本
    if (match.index > lastIndex) {
      parts.push({
        text: text.slice(lastIndex, match.index),
        isInput: false,
      });
    }
    // 添加输入框
    parts.push({
      isInput: true,
      placeholder: match[1], // 占位符中的数字
      index: parseInt(match[1]) - 1, // 转换为数组索引
    });
    lastIndex = regex.lastIndex;
  }
  // 添加剩余的普通文本
  if (lastIndex < text.length) {
    parts.push({
      text: text.slice(lastIndex),
      isInput: false,
    });
  }
  return parts;
};
// 判断是否有选项
const hasOptions = (bigQuestion) => {
  return bigQuestion.small_questions[0]?.question_options?.length > 0;
};


// 获取当前问题的可用选项（改为函数形式接收bigQuestion参数）
const getAvailableOptions = (bigQuestion) => {
  const allOptions = parseOptions(bigQuestion.small_questions[0]?.question_options || []);
  // 直接提取所有已使用的选项值（忽略键的前缀）
  const usedOptions = Object.values(summaryAnswers.value);
  return allOptions.filter(opt => !usedOptions.includes(opt));
};

// 处理拖拽开始
const handleDragStart = (event, option) => {
  event.dataTransfer.setData('option', option);
};

// 处理拖拽放入（增加bigQuestion参数）
const handleDrop = (event, bigQuestion, partIndex) => {
  event.preventDefault();
  const option = event.dataTransfer.getData('option');
  if (option) {
    summaryAnswers.value[partIndex+1] = option;
  }
};


// 提交按钮
// 定义一个函数用于预处理答案数据
const transformAnswers = () => {
  // 复制各个答案对象（注意这里假设各个答案都是响应式数据的 .value）
  const processed = {
    judgement: { ...judgementAnswers.value },
    fillIn: { ...fillInInputs.value },
    multiChoice: { ...multiChoiceAnswers.value },
    match: { ...matchAnswers.value },
    summary: { ...summaryAnswers.value },
    write: { ...writeAnswers.value },
    choose: { ...chooseAnswers.value }
  };

  // 处理 choose 和 summary 题型：如果答案字符串开头是大写字母加点，只保留该大写字母
  const processTextAnswer = (obj) => {
    const result = {};
    for (const key in obj) {
      let ans = obj[key];
      if (typeof ans === 'string') {
        ans = ans.trim();
        // 使用正则匹配格式：大写字母 + 点，比如 "C.xxx"
        const regex = /^([A-Z])\./;
        const match = ans.match(regex);
        result[key] = match ? match[1] : ans;
      }
    }
    return result;
  };

  processed.choose = processTextAnswer(processed.choose);
  processed.summary = processTextAnswer(processed.summary);

  // 处理多选题答案：按大题（bigQuestion）分组，在组内执行继承逻辑
  // 假设每个大题的 small_questions 顺序即为需要处理的顺序
  const processedMultiChoice = {};
  bigQuestions.value.forEach((bigQuestion) => {
    if (bigQuestion.type === 'multiple_choice') {
      let groupAnswer = null; // 当前大题组的答案（来自组内第一道有答案的题）
      bigQuestion.small_questions.forEach((smallQuestion) => {
        const qNum = smallQuestion.question_number;
        const answerArr = multiChoiceAnswers.value[qNum];
        if (Array.isArray(answerArr) && answerArr.length > 0) {
          // 非空答案：先排序再转换为字母
          const sortedArr = [...answerArr].sort((a, b) => a - b);
          const converted = sortedArr.map(num => String.fromCharCode(65 + num)).join('');
          processedMultiChoice[qNum] = converted;
          groupAnswer = converted; // 更新组内答案
        } else {
          // 空答案：如果已有本组答案则继承，否则保持空字符串
          processedMultiChoice[qNum] = groupAnswer !== null ? groupAnswer : "";
        }
      });
    }
  });
  processed.multiChoice = processedMultiChoice;

  // 处理 match 题型：每个题目对应一个布尔数组，找到 true 所在的下标并转换成字母
  const processMatchAnswer = (boolArr) => {
    const trueIndex = boolArr.findIndex(val => val === true);
    return trueIndex !== -1 ? String.fromCharCode(65 + trueIndex) : "";
  };

  for (const key in processed.match) {
    const ans = processed.match[key];
    if (Array.isArray(ans)) {
      processed.match[key] = processMatchAnswer(ans);
    }
  }

  // 处理 judgement 题型：将答案转换成规定的字母
  // YES -> Y, NO -> N, FALSE -> F, TRUE -> T, NOT GIVEN -> NG
  const judgementMapping = {
    'YES': 'Y',
    'NO': 'N',
    'FALSE': 'F',
    'TRUE': 'T',
    'NOT GIVEN': 'NG'
  };

  for (const key in processed.judgement) {
    let ans = processed.judgement[key];
    if (typeof ans === 'string') {
      ans = ans.trim().toUpperCase();
      if (judgementMapping.hasOwnProperty(ans)) {
        processed.judgement[key] = judgementMapping[ans];
      }
    }
  }

  // 最后，如果某个题型的答案对象为空（即 {}），则删除该字段，不传给后台
  for (const key in processed) {
    if (typeof processed[key] === 'object' && !Array.isArray(processed[key])) {
      if (Object.keys(processed[key]).length === 0) {
        delete processed[key];
      }
    }
  }

  return processed;
};

// 在提交数据时，调用转换函数
const submit = async () => {
  try {
    // 从本地存储获取用户信息
    const token = localStorage.getItem('token'); // 或 sessionStorage
    const username = localStorage.getItem('username');
    const userRole = localStorage.getItem('userRole');

    // 预处理答案数据
    const processedAnswers = transformAnswers();

    // 组装提交数据
    const submissionData = {
      user: { // 添加用户信息
        token,
        username,
        role: userRole
      },
      exercise: { // 练习信息
        bank_type: route.params.bank_type,
        a: route.params.a,
        b: route.params.b,
        display_order: route.params.display_order
      },
      performance: { // 表现数据
        timer: timer.value,
        answers: processedAnswers
      }
    };
    const response = await axios.post('/api/submit', submissionData);

    router.push(`/submission/${response.data.sub_id}`);
    if (token != null){
      clearSessionStorage();
    }
  } catch (error) {
    console.error('提交失败:', error);
    alert('提交失败，请重试');
  }
};


// 清除会话存储
const clearSessionStorage = () => {
  // 清除所有相关存储键
  // 停止计时器
clearInterval(interval);

  const keys = [
    storageKey.value,
    storageKeyFillIn.value,
    storageKeyMultiChoice.value,
    storageKeyMatch.value,
    storageKeySummary.value,
    storageKeyJudgement.value,
    storageKeyWrite.value,
    storageKeyChoose.value
  ];

  keys.forEach(key => sessionStorage.removeItem(key));

};

// 初始化计时器
const initTimer = () => {
  const savedData = sessionStorage.getItem(storageKey.value);
  if (savedData) {
    const { accumulated } = JSON.parse(savedData);
    timer.value = accumulated ;
  }
  interval = setInterval(() => {
    if (!isPaused.value) {
    timer.value++;
    sessionStorage.setItem(
      storageKey.value,
      JSON.stringify({
        startTime: Math.floor(Date.now() / 1000),
        accumulated: timer.value,
      })
    );}
  }, 1000);
};
// 暂停计时器
const pauseTimer = () => {
  isPaused.value = true;
  clearInterval(interval);
  // 显示模态框
  const modal = new Modal(document.getElementById("pauseModal"));
  modal.show();
};


// 初始化题
const initializeAnswers = () => {
  if (bigQuestions.value.length > 0) {

    // 初始化多选题答案（每个题都初始化为空数组）
  bigQuestions.value.forEach((bigQuestion) => {
    if (bigQuestion.type === 'multiple_choice') {
      bigQuestion.small_questions.forEach((smallQuestion) => {
        multiChoiceAnswers.value[smallQuestion.question_number] = [];
      });
    }
    if (bigQuestion.type === 'matching') {
       const options = parseOptions(bigQuestion.small_questions?.[0]?.question_options || []);
  matchAnswers.value = {};
  bigQuestion.small_questions?.forEach(question => {
    matchAnswers.value[question.question_number] =
      Array(options.length).fill(false);
  });
    }
    if (bigQuestion.type === 'judgement') {
      bigQuestion.small_questions.forEach((smallQuestion) => {
        judgementAnswers.value[smallQuestion.question_number] = "";
      });
    }
    if (bigQuestion.type === 'summary') {
      bigQuestion.small_questions.forEach((smallQuestion) => {
        summaryAnswers.value[smallQuestion.question_number] = "";
      });
    }
    if (bigQuestion.type === 'choice') {
      bigQuestion.small_questions.forEach((smallQuestion) => {
        chooseAnswers.value[smallQuestion.question_number] = "";
      });
    }
    if (bigQuestion.type === 'fill_in') {
      bigQuestion.small_questions.forEach((smallQuestion) => {
        fillInInputs.value[smallQuestion.question_number] = "";
      });
    }
    if (bigQuestion.type === 'write') {
        writeAnswers.value[bigQuestion.bank_id] = "";
    }
  });
  }
};

// 页面加载时执行
onMounted(async () => {
  await loadData();
  initTimer();
  initializeAnswers();
  const modalElement = document.getElementById("pauseModal");
  modalElement.addEventListener("hidden.bs.modal", () => {
    isPaused.value = false; // 恢复计时器
    initTimer(); // 重新启动计时器
  });
  // 恢复各题答案数据（如果存在）
  const savedFillIn = sessionStorage.getItem(storageKeyFillIn.value);
  if (savedFillIn) {
    fillInInputs.value = JSON.parse(savedFillIn);
  }
  const savedMultiChoice = sessionStorage.getItem(storageKeyMultiChoice.value);
  if (savedMultiChoice) {
    multiChoiceAnswers.value = JSON.parse(savedMultiChoice);
  }
  const savedMatch = sessionStorage.getItem(storageKeyMatch.value);
  if (savedMatch) {
    matchAnswers.value = JSON.parse(savedMatch);
  }
  const savedSummary = sessionStorage.getItem(storageKeySummary.value);
  if (savedSummary) {
    summaryAnswers.value = JSON.parse(savedSummary);
  }
  const savedJudgement = sessionStorage.getItem(storageKeyJudgement.value);
  if (savedJudgement) {
    judgementAnswers.value = JSON.parse(savedJudgement);
  }
  const savedChoose = sessionStorage.getItem(storageKeyChoose.value);
  if (savedChoose) {
    chooseAnswers.value = JSON.parse(savedChoose);
  }
  const savedWrite = sessionStorage.getItem(storageKeyWrite.value);
  if (savedWrite) {
    writeAnswers.value = JSON.parse(savedWrite);
  }
});

// 利用 watch 实时保存答案状态
watch(fillInInputs, (newVal) => {
  sessionStorage.setItem(storageKeyFillIn.value, JSON.stringify(newVal));
}, { deep: true });

watch(multiChoiceAnswers, (newVal) => {
  sessionStorage.setItem(storageKeyMultiChoice.value, JSON.stringify(newVal));
}, { deep: true });

watch(matchAnswers, (newVal) => {
  sessionStorage.setItem(storageKeyMatch.value, JSON.stringify(newVal));
}, { deep: true });

watch(summaryAnswers, (newVal) => {
  sessionStorage.setItem(storageKeySummary.value, JSON.stringify(newVal));
}, { deep: true });

watch(judgementAnswers, (newVal) => {
  sessionStorage.setItem(storageKeyJudgement.value, JSON.stringify(newVal));
}, { deep: true });

watch(chooseAnswers, (newVal) => {
  sessionStorage.setItem(storageKeyChoose.value, JSON.stringify(newVal));
}, { deep: true });

watch(writeAnswers, (newVal) => {
  sessionStorage.setItem(storageKeyWrite.value, JSON.stringify(newVal));
}, { deep: true });
// 处理匹配题的复选框点击事件
const handleCheckboxClick = (rowIndex, colIndex) => {
  matchAnswers.value[rowIndex].forEach((_, index) => {
    matchAnswers.value[rowIndex][index] = index === colIndex;
  });
};

// 判断多选题选项是否禁用
const isOptionDisabled = (questionId, optionIndex) => {
  const selectedOptions = multiChoiceAnswers.value[questionId] || [];
  return selectedOptions.length >= 2 && !selectedOptions.includes(optionIndex);
};

onUnmounted(() => {
  clearInterval(interval);
});

onBeforeRouteLeave(() => {
  // 可根据需求决定是否清除答案数据
  // sessionStorage.removeItem(storageKey.value);
  clearInterval(interval);
  sessionStorage.setItem(
    storageKey.value,
    JSON.stringify({
      startTime: Math.floor(Date.now() / 1000),
      accumulated: timer.value,
    })
  );
});
</script>


<style scoped>
/* 导航栏样式 */
.navbar {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 图片样式 */
.img-fluid {
  max-width: 100%;
  height: auto;
}

/* 边框样式 */
.border {
  border: 1px solid #dee2e6 !important;
  border-radius: 0.25rem;
}

/* 左右列样式 */
.left-column,
.right-column {
  height: calc(100vh - 70px); /* 根据实际导航栏高度调整 */
  overflow-y: auto; /* 启用垂直滚动条 */
  padding: 15px;
}
.right-column h4 {
  color: #0d6efd;
  border-bottom: 2px solid #0d6efd;
  padding-bottom: 0.5rem;
}

.form-check {
  margin-bottom: 0.5rem;
}

.form-check-input {
  margin-top: 0.3em;
}

.fst-italic {
  font-style: italic;
}

.text-muted {
  color: #6c757d !important;
}


/* 输入框样式 */
::v-deep .fill-in-input {
  border: 2px solid #ccc; /* 浅色边框 */
  border-radius: 4px;
  padding: 6px 12px;
  margin: 4px;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
  text-align: center; /* 文字居中 */
}

/* 输入框聚焦状态 */
::v-deep .fill-in-input:focus {
  border-color: #007bff; /* 蓝色边框 */
  box-shadow: 0 0 5px rgba(0, 123, 255, 0.5); /* 蓝色光晕 */
  outline: none;
}
.summary-paragraph {
  line-height: 1.8; /* 增加行距（默认通常是1.2-1.5） */
  margin-bottom: 1em; /* 段落间距 */
}
/* placeholder 样式 */
::v-deep .fill-in-input::placeholder {
  color: #007bff; /* 蓝色文字 */
  font-weight: bold; /* 加粗 */
  text-align: center; /* 居中 */
}


/* 表格样式 */
.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  border: 1px solid #dee2e6;
  padding: 8px;

}

.table th {
  background-color: #f8f9fa;
}

.table input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}
.table input[type="checkbox"] {
  accent-color: #007bff; /* 适用于大多数现代浏览器 */
}
.table input[type="checkbox"]:hover {
  box-shadow: 0 0 5px rgba(0, 123, 255, 0.5); /* 浅蓝色光晕 */
  border-color: #66b0ff; /* 改变边框颜色 */
}

/* 复选框样式 */
.form-check-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.write-input {
  width: 100%; /* 占满父容器宽度 */
  height: 400px; /* 设置一个固定高度，可以根据需要调整 */
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-family: inherit;
  font-size: 16px;
  resize: vertical; /* 允许垂直调整大小 */
}

.write-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 5px rgba(0, 123, 255, 0.5);
  outline: none;
}

.text-muted {
  color: #6c757d;
}
/* 强制模态框居中 */
.modal-dialog {
  display: flex;
  align-items: center;
  min-height: calc(100% - 1rem); /* 避免模态框超出视口 */
}

.modal-content {
  width: 100%; /* 确保内容宽度正常 */
}

/* 选项容器样式 */
.options-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 15px;
}

/* 单个选项框样式 - 美化版 */
.option-box {
  min-width: 220px;  /* 稍微加宽一点 */
  padding: 12px 16px;  /* 增加内边距 */
  border: 1px solid #e0e0e0;  /* 更浅的边框色 */
  border-radius: 6px;  /* 更大的圆角 */
  background-color: #ffffff;  /* 纯白背景 */
  cursor: grab;
  transition: all 0.2s ease-in-out;  /* 更平滑的过渡 */

  /* 蓝色元素 */
  border-left: 4px solid #4285f4;  /* 左侧蓝色边框 */
  box-shadow: 0 1px 3px rgba(66, 133, 244, 0.1);  /* 浅蓝色阴影 */

  /* 文字样式 */
  color: #333;
  font-size: 14px;
  font-weight: 500;
}

/* 悬停效果 */
.option-box:hover {
  transform: translateY(-2px);  /* 轻微上浮 */
  box-shadow: 0 4px 8px rgba(66, 133, 244, 0.15);  /* 更明显的阴影 */
  border-color: #c2d6ff;  /* 悬停时边框变浅蓝 */
}

/* 拖动时的样式 */
.option-box:active {
  cursor: grabbing;
  transform: scale(0.98);  /* 轻微缩小 */
  box-shadow: 0 2px 5px rgba(66, 133, 244, 0.2);  /* 蓝色阴影 */
  background-color: #f8fbff;  /* 浅蓝色背景 */
}

/* 选中状态（可选） */
.option-box.selected {
  background-color: #e8f0fe;  /* 更深的蓝色背景 */
  border-color: #aecbfa;
}
</style>
