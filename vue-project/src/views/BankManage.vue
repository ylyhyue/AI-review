<template>
  <div class="container my-4">
    <!-- 搜索框 -->
    <div class="row align-items-center mb-3 g-3">  <!-- 网格行 + 垂直居中 -->
  <div class="col-auto">  <!-- 按钮自适应宽度 -->
    <button class="btn btn-success" @click="openAddBankModal">Add Bank</button>
  </div>
  <div class="col">  <!-- 输入框填充剩余空间 -->
    <input
      type="text"
      class="form-control"
      placeholder="Search by Bank Name, Type, or Location"
      v-model="searchQuery"
      @input="fetchBanks"
    />
  </div>
</div>
    <!-- 银行列表，按 bank_type 分组显示 -->
    <div v-for="(groupBanks, bankType) in banksByType" :key="bankType">
      <h3>{{ bankType }}</h3>
      <div class="row">
        <div class="col-md-4 mb-3" v-for="bank in groupBanks" :key="bank.bank_id">
          <div class="card">
            <div class="card-body">
              <h5 class="card-title">{{ bank.bank_name }}</h5>
              <p class="card-text">Location: {{ bank.location }}</p>
              <p class="card-text">Display Order: {{ bank.display_order }}</p>
              <button class="btn btn-primary btn-sm" @click="openBankDetails(bank)">View Details</button>
              <button class="btn btn-warning btn-sm ms-2" @click="openEditBankModal(bank)">Edit</button>
              <button class="btn btn-danger btn-sm ms-1" @click="deleteBank(bank)">Delete</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bank Details Modal -->
    <div class="modal fade" id="bankDetailsModal" tabindex="-1" ref="bankDetailsModal">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">

            <button type="button" class="btn-close" @click="closeBankDetailsModal"></button>
          </div>
          <div class="modal-body">
            <div v-if="currentBankDetails">
              <!-- 资源部分 -->
              <h6>Resources</h6>
              <ul>
                <li v-for="resource in currentBankDetails.resources" :key="resource.resource_id">
                  <!-- TEXT 类型直接显示文字 -->
                  <span v-if="resource.resource_type.toUpperCase() === 'TEXT'">
                    {{ resource.resource_information }}
                  </span>
                  <!-- PICTURE 类型显示图片 -->
                  <img
                    v-if="resource.resource_type.toUpperCase() === 'PICTURE'"
                    :src="resource.resource_information"
                    alt="Resource Image"
                    style="max-width:100px;"
                  />
                  <!-- 嵌套编辑操作 -->
                  <button class="btn btn-warning btn-sm ms-2" @click="openEditResourceModal(resource, currentBank.bank_id)">Edit</button>
                  <button class="btn btn-danger btn-sm ms-1" @click="deleteResource(resource, currentBank.bank_id)">Delete</button>
                </li>
              </ul>
              <button class="btn btn-success btn-sm" @click="openAddResourceModal(currentBank.bank_id)">Add Resource</button>

              <!-- 大题及小题部分 -->
              <h6 class="mt-3">Big Questions</h6>
              <div v-for="bq in currentBankDetails.big_questions" :key="bq.big_id" class="border p-2 mb-2">
                <p>
                  <strong>
                    Big Question {{ bq.start_number }} - {{ bq.end_number }} (Type: {{ bq.type }})
                  </strong>
                </p>
                <p v-html="bq.question_description"></p>
                <button class="btn btn-secondary btn-sm" @click="toggleNestedSmallQuestions(bq)">Toggle Small Questions</button>
                <div v-if="bq.showSmallQuestions" class="mt-2">
                  <div v-for="sq in bq.small_questions" :key="sq.small_id" class="border p-2 mb-1">
                    <p><strong>Question {{ sq.question_number }}:</strong></p>
                    <p v-html="sq.question_content"></p>
                    <p><em>Answer:</em> {{ sq.question_answer }}</p>
                    <p v-if="sq.question_options">Options: {{ sq.question_options }}</p>
                    <button class="btn btn-warning btn-sm" @click="openEditSmallQuestionModal(sq, bq.big_id)">Edit</button>
                    <button class="btn btn-danger btn-sm" @click="deleteSmallQuestion(sq, bq.big_id)">Delete</button>
                  </div>
                  <button class="btn btn-success btn-sm" @click="openAddSmallQuestionModal(bq.big_id)">Add Small Question</button>
                </div>
                <button class="btn btn-warning btn-sm mt-2" @click="openEditBigQuestionModal(bq, currentBank.bank_id)">Edit Big Question</button>
                <button class="btn btn-danger btn-sm mt-2" @click="deleteBigQuestion(bq, currentBank.bank_id)">Delete Big Question</button>
              </div>
              <button class="btn btn-success btn-sm" @click="openAddBigQuestionModal(currentBank.bank_id)">Add Big Question</button>
            </div>
            <div v-else>
              Loading details...
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closeBankDetailsModal">Close</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Resource Modal（嵌套模态框） -->
    <div class="modal fade" id="resourceModal" tabindex="-1" ref="resourceModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <form @submit.prevent="submitResource">
            <div class="modal-header">
              <h5 class="modal-title">{{ resourceForm.id ? 'Edit Resource' : 'Add Resource' }}</h5>
              <button type="button" class="btn-close" @click="closeResourceModal"></button>
            </div>
            <div class="modal-body">
              <!-- 当类型为 TEXT 时，输入文字 -->
              <div class="mb-3" v-if="resourceForm.resource_type !== 'PICTURE'">
                <label>Resource Information</label>
                <input type="text" class="form-control" v-model="resourceForm.resource_information" required />
              </div>
              <!-- 当类型为 PICTURE 时，显示文件上传 -->
              <div class="mb-3" v-if="resourceForm.resource_type === 'PICTURE'">
                <label>Upload Picture</label>
                <input type="file" class="form-control" @change="handleFileChange" accept="image/*" />
                <div v-if="resourceForm.previewUrl" class="mt-2">
                  <img :src="resourceForm.previewUrl" alt="Preview" style="max-width:100px;" />
                </div>
              </div>
              <div class="mb-3">
                <label>Resource Type</label>
                <select class="form-select" v-model="resourceForm.resource_type" required>
                  <option value="TEXT">TEXT</option>
                  <option value="PICTURE">PICTURE</option>
                  <option value="describe">DESCRIBE (only need when have chart)</option>
                </select>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closeResourceModal">Close</button>
              <button type="submit" class="btn btn-primary">{{ resourceForm.id ? 'Update' : 'Add' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
    <!-- 新增/编辑 Bank Modal -->
    <div class="modal fade" id="bankModal" tabindex="-1" ref="bankModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <form @submit.prevent="submitBank">
            <div class="modal-header">
              <h5 class="modal-title">{{ bankForm.bank_id ? 'Edit Bank' : 'Add Bank' }}</h5>
              <button type="button" class="btn-close" @click="closeBankModal"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                <label>Bank Name</label>
                <input type="text" class="form-control" v-model="bankForm.bank_name" required />
              </div>
              <div class="mb-3">
                <label>Bank Type</label>
                <input type="text" class="form-control" v-model="bankForm.bank_type" required />
              </div>
              <div class="mb-3">
                <label>Location (format X:Y)</label>
                <input type="text" class="form-control" v-model="bankForm.location" required />
              </div>
              <div class="mb-3">
                <label>Display Order</label>
                <input type="number" class="form-control" v-model="bankForm.display_order" required />
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closeBankModal">Close</button>
              <button type="submit" class="btn btn-primary">{{ bankForm.bank_id ? 'Update' : 'Add' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
    <!-- Big Question Modal（嵌套模态框） -->
    <div class="modal fade" id="bigQuestionModal" tabindex="-1" ref="bigQuestionModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <form @submit.prevent="submitBigQuestion">
            <div class="modal-header">
              <h5 class="modal-title">{{ bigQuestionForm.big_id ? 'Edit Big Question' : 'Add Big Question' }}</h5>
              <button type="button" class="btn-close" @click="closeBigQuestionModal"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                <label>Type</label>
                <input type="text" class="form-control" v-model="bigQuestionForm.type" required />
              </div>
              <div class="mb-3">
                <label>Question Description</label>
                <textarea class="form-control" v-model="bigQuestionForm.question_description" required></textarea>
              </div>
              <div class="mb-3">
                <label>Start Number</label>
                <input type="number" class="form-control" v-model="bigQuestionForm.start_number" />
              </div>
              <div class="mb-3">
                <label>End Number</label>
                <input type="number" class="form-control" v-model="bigQuestionForm.end_number" />
              </div>
              <div class="mb-3">
                <label>If NB (1 for yes, 0 for no)</label>
                <input type="number" class="form-control" v-model="bigQuestionForm.if_nb" required />
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closeBigQuestionModal">Close</button>
              <button type="submit" class="btn btn-primary">{{ bigQuestionForm.big_id ? 'Update' : 'Add' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Small Question Modal（嵌套模态框） -->
    <div class="modal fade" id="smallQuestionModal" tabindex="-1" ref="smallQuestionModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <form @submit.prevent="submitSmallQuestion">
            <div class="modal-header">
              <h5 class="modal-title">{{ smallQuestionForm.small_id ? 'Edit Small Question' : 'Add Small Question' }}</h5>
              <button type="button" class="btn-close" @click="closeSmallQuestionModal"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                <label>Question Number</label>
                <input type="number" class="form-control" v-model="smallQuestionForm.question_number" required />
              </div>
              <div class="mb-3">
                <label>Question Content</label>
                <textarea class="form-control" v-model="smallQuestionForm.question_content"></textarea>
              </div>
              <div class="mb-3">
                <label>Question Options</label>
                <input type="text" class="form-control" v-model="smallQuestionForm.question_options" />
              </div>
              <div class="mb-3">
                <label>Correct Answer</label>
                <input type="text" class="form-control" v-model="smallQuestionForm.question_answer"/>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closeSmallQuestionModal">Close</button>
              <button type="submit" class="btn btn-primary">{{ smallQuestionForm.small_id ? 'Update' : 'Add' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import axios from 'axios';
import { Modal } from 'bootstrap';
export default {
  name: 'BankManagement',
  data() {
    return {
      searchQuery: '',
      banks: [],
      currentBank: null,            // 当前选中的 bank（用于详情模态框）
      currentBankDetails: null,     // 当前 bank 的详细信息
      bankForm: { bank_id: null, bank_name: '', bank_type: '', location: '', display_order: 0 },
      // Resource 表单数据，额外添加 previewUrl 和 file 用于图片上传
      resourceForm: { id: null, resource_information: '', resource_type: 'TEXT', bank_id: null, previewUrl: '', file: null },
      // Big Question 表单数据
      bigQuestionForm: { big_id: null, type: '', question_description: '', start_number: '', end_number: '', if_nb: 0, bank_id: null },
      // Small Question 表单数据
      smallQuestionForm: { small_id: null, question_number: '', question_content: '', question_options: '', question_answer: '', big_id: null }
    };
  },
  computed: {
    banksByType() {
      const grouped = {};
      this.banks.forEach(bank => {
        const type = bank.bank_type || 'Undefined';
        if (!grouped[type]) grouped[type] = [];
        grouped[type].push(bank);
      });
      return grouped;
    }
  },
  methods: {
    fetchBanks() {
      axios.get('/api/banks', { params: { search: this.searchQuery } })
        .then(response => {
          let flatBanks = [];
          const data = response.data;
          for (const type in data) {
            data[type].forEach(bank => {
              flatBanks.push(bank);
            });
          }
          this.banks = flatBanks;
        })
        .catch(error => console.error('Error fetching banks:', error));
    },
    // 打开银行详情模态框
    openBankDetails(bank) {
      this.currentBank = bank;
      axios.get(`/api/banks/${bank.bank_id}`)
        .then(response => {
          this.currentBankDetails = response.data;
          // 为每个大题初始化小题显示状态
          this.currentBankDetails.big_questions.forEach(bq => bq.showSmallQuestions = false);
          new Modal(this.$refs.bankDetailsModal).show();
        })
        .catch(error => console.error('Error fetching bank details:', error));
    },
    closeBankDetailsModal() {
      Modal.getInstance(this.$refs.bankDetailsModal).hide();
      this.currentBank = null;
      this.currentBankDetails = null;
    },
    // 新增 Bank 相关操作
    openAddBankModal() {
      this.bankForm = { bank_id: null, bank_name: '', bank_type: '', location: '', display_order: 0 };
      new Modal(this.$refs.bankModal).show();
    },
    openEditBankModal(bank) {
      this.bankForm = { ...bank };
      new Modal(this.$refs.bankModal).show();
    },
    closeBankModal() {
      Modal.getInstance(this.$refs.bankModal).hide();
      this.bankForm = { bank_id: null, bank_name: '', bank_type: '', location: '', display_order: 0 };
    },
    submitBank() {
      if (this.bankForm.bank_id) {
        axios.put('/api/bank/' + this.bankForm.bank_id, this.bankForm)
          .then(response => {
            alert(response.data.message);
            this.fetchBanks();
            this.closeBankModal();
          })
          .catch(error => {
            console.error(error);
            alert('Error updating bank');
          });
      } else {
        axios.post('/api/bank', this.bankForm)
          .then(response => {
            alert(response.data.message);
            this.fetchBanks();
            this.closeBankModal();
          })
          .catch(error => {
            console.error(error);
            alert('Error adding bank');
          });
      }
    },
    deleteBank(bank) {
      if (confirm('Delete this bank?')) {
        axios.delete('/api/bank/' + bank.bank_id)
          .then(response => {
            alert(response.data.message);
            this.fetchBanks();
          })
          .catch(error => {
            console.error(error);
            alert('Error deleting bank');
          });
      }
    },
    // 切换大题下小题的显示
    toggleNestedSmallQuestions(bq) {
      bq.showSmallQuestions = !bq.showSmallQuestions;
    },
    // Resource 操作
    openAddResourceModal(bank_id) {
      this.resourceForm = { id: null, resource_information: '', resource_type: 'TEXT', bank_id, previewUrl: '', file: null };
      new Modal(this.$refs.resourceModal).show();
    },
    openEditResourceModal(resource, bank_id) {
      this.resourceForm = {
        id: resource.resource_id,
        resource_information: resource.resource_information,
        resource_type: resource.resource_type,
        bank_id,
        previewUrl: (resource.resource_type.toUpperCase() === 'PICTURE' ? resource.resource_information : ''),
        file: null
      };
      new Modal(this.$refs.resourceModal).show();
    },
    closeResourceModal() {
      Modal.getInstance(this.$refs.resourceModal).hide();
      this.resourceForm = { id: null, resource_information: '', resource_type: 'TEXT', bank_id: null, previewUrl: '', file: null };
    },
    handleFileChange(event) {
      const file = event.target.files[0];
      if (file) {
        this.resourceForm.file = file;
        this.resourceForm.previewUrl = URL.createObjectURL(file);
      }
    },
    async submitResource() {
      // 如果选择了 picture 类型并上传了文件，则先上传图片
      if (this.resourceForm.resource_type === 'PICTURE' && this.resourceForm.file) {
        try {
          const formData = new FormData();
          formData.append('file', this.resourceForm.file);
          // 调用上传接口，后端将文件保存到 src/assets 中，并返回文件路径
          const uploadResponse = await axios.post('/api/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
          if (uploadResponse.data.filePath) {
            this.resourceForm.resource_information = uploadResponse.data.filePath;
          } else {
            this.resourceForm.resource_information = this.resourceForm.previewUrl;
          }
        } catch (error) {
          console.error('Image upload failed:', error);
          alert('Image upload failed.');
          return;
        }
      }
      if (this.resourceForm.id) {
        axios.put('/api/resource/' + this.resourceForm.id, this.resourceForm)
          .then(response => {
            alert(response.data.message);
            this.refreshCurrentBankDetails();
            this.closeResourceModal();
          })
          .catch(error => {
            console.error(error);
            alert('Error updating resource');
          });
      } else {
        axios.post('/api/resource', this.resourceForm)
          .then(response => {
            alert(response.data.message);
            this.refreshCurrentBankDetails();
            this.closeResourceModal();
          })
          .catch(error => {
            console.error(error);
            alert('Error adding resource');
          });
      }
    },
    deleteResource(resource, bank_id) {
      if (confirm('Delete this resource?')) {
        axios.delete('/api/resource/' + resource.resource_id)
          .then(response => {
            alert(response.data.message);
            this.refreshCurrentBankDetails();
          })
          .catch(error => {
            console.error(error);
            alert('Error deleting resource');
          });
      }
    },
    // Big Question 操作
    openAddBigQuestionModal(bank_id) {
      this.bigQuestionForm = { big_id: null, type: '', question_description: '', start_number: '', end_number: '', if_nb: 0, bank_id };
      new Modal(this.$refs.bigQuestionModal).show();
    },
    openEditBigQuestionModal(bq, bank_id) {
      this.bigQuestionForm = { big_id: bq.big_id, type: bq.type, question_description: bq.question_description, start_number: bq.start_number, end_number: bq.end_number, if_nb: bq.if_nb, bank_id };
      new Modal(this.$refs.bigQuestionModal).show();
    },
    closeBigQuestionModal() {
      Modal.getInstance(this.$refs.bigQuestionModal).hide();
    },
    submitBigQuestion() {
      if (this.bigQuestionForm.big_id) {
        axios.put('/api/bigquestion/' + this.bigQuestionForm.big_id, this.bigQuestionForm)
          .then(response => {
            alert(response.data.message);
            this.refreshCurrentBankDetails();
            this.closeBigQuestionModal();
          })
          .catch(error => {
            console.error(error);
            alert('Error updating big question');
          });
      } else {
        axios.post('/api/bigquestion', this.bigQuestionForm)
          .then(response => {
            alert(response.data.message);
            this.refreshCurrentBankDetails();
            this.closeBigQuestionModal();
          })
          .catch(error => {
            console.error(error);
            alert('Error adding big question');
          });
      }
    },
    deleteBigQuestion(bq, bank_id) {
      if (confirm('Delete this big question?')) {
        axios.delete('/api/bigquestion/' + bq.big_id)
          .then(response => {
            alert(response.data.message);
            this.refreshCurrentBankDetails();
          })
          .catch(error => {
            console.error(error);
            alert('Error deleting big question');
          });
      }
    },
    // Small Question 操作
    openAddSmallQuestionModal(big_id) {
      this.smallQuestionForm = { small_id: null, question_number: '', question_content: '', question_options: '', question_answer: '', big_id };
      new Modal(this.$refs.smallQuestionModal).show();
    },
    openEditSmallQuestionModal(sq, big_id) {
      this.smallQuestionForm = { small_id: sq.small_id, question_number: sq.question_number, question_content: sq.question_content, question_options: sq.question_options, question_answer: sq.question_answer, big_id };
      new Modal(this.$refs.smallQuestionModal).show();
    },
    closeSmallQuestionModal() {
      Modal.getInstance(this.$refs.smallQuestionModal).hide();
    },
    submitSmallQuestion() {
      if (this.smallQuestionForm.small_id) {
        axios.put('/api/smallquestion/' + this.smallQuestionForm.small_id, this.smallQuestionForm)
          .then(response => {
            alert(response.data.message);
            this.refreshCurrentBankDetails();
            this.closeSmallQuestionModal();
          })
          .catch(error => {
            console.error(error);
            alert('Error updating small question');
          });
      } else {
        axios.post('/api/smallquestion', this.smallQuestionForm)
          .then(response => {
            alert(response.data.message);
            this.refreshCurrentBankDetails();
            this.closeSmallQuestionModal();
          })
          .catch(error => {
            console.error(error);
            alert('Error adding small question');
          });
      }
    },
    deleteSmallQuestion(sq, big_id) {
      if (confirm('Delete this small question?')) {
        axios.delete('/api/smallquestion/' + sq.small_id)
          .then(response => {
            alert(response.data.message);
            this.refreshCurrentBankDetails();
          })
          .catch(error => {
            console.error(error);
            alert('Error deleting small question');
          });
      }
    },
    // 辅助函数：刷新当前 bank 详情数据
    refreshCurrentBankDetails() {
      if (this.currentBank) {
        axios.get(`/api/banks/${this.currentBank.bank_id}`)
          .then(response => {
            this.currentBankDetails = response.data;
            this.currentBankDetails.big_questions.forEach(bq => bq.showSmallQuestions = false);
          })
          .catch(error => console.error(error));
      }
    }
  },
  mounted() {
    this.fetchBanks();
  }
};
</script>

<style scoped>
.container {
  max-width: 1200px;
}
.card {
  margin-bottom: 20px;
}
</style>
