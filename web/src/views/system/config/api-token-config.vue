<script lang="ts" setup>
import type { FormInst } from 'naive-ui'
import { NButton, NSwitch, useDialog, useMessage } from 'naive-ui'
import { h, onMounted, reactive, ref } from 'vue'
import {
  addApiToken,
  deleteApiToken,
  disableApiToken,
  enableApiToken,
  queryApiTokenList,
} from '@/api/api-token'
import { queryUserList } from '@/api/user'

const dialog = useDialog()
const message = useMessage()

const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const searchName = ref('')
const filterStatus = ref<number | null>(null)

const adminUsers = ref<{ label: string, value: number }[]>([])

const showCreateModal = ref(false)
const showTokenModal = ref(false)
const createdToken = ref('')
const tokenAcknowledged = ref(false)
const formRef = ref<FormInst | null>(null)
const formModel = reactive({
  name: '',
  user_id: null as number | null,
})

const rules = {
  name: { required: true, message: '请输入 Token 名称', trigger: 'blur' },
}

const statusOptions = [
  { label: '全部', value: null },
  { label: '启用', value: 1 },
  { label: '禁用', value: 0 },
]

const columns = [
  { title: 'ID', key: 'id', width: 70 },
  { title: '名称', key: 'name', width: 180 },
  { title: 'Token 前缀', key: 'token_prefix', width: 140 },
  { title: '绑定用户', key: 'username', width: 120 },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row: any) {
      return h(NSwitch, {
        value: row.status === 1,
        onUpdateValue: (value: boolean) => handleStatusChange(row, value),
      })
    },
  },
  { title: '最后使用', key: 'last_used_at', width: 170, render: (row: any) => row.last_used_at || '-' },
  { title: '创建时间', key: 'created_at', width: 170 },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render(row: any) {
      return h(NButton, {
        size: 'small',
        type: 'error',
        secondary: true,
        onClick: () => handleDelete(row),
      }, { default: () => '删除' })
    },
  },
]

const fetchAdminUsers = async () => {
  try {
    const res = await queryUserList(1, 100)
    const result = await res.json()
    if (result.code === 200) {
      adminUsers.value = (result.data.records || [])
        .filter((u: any) => u.role === 'admin')
        .map((u: any) => ({ label: u.userName, value: u.id }))
      if (adminUsers.value.length > 0 && !formModel.user_id) {
        formModel.user_id = adminUsers.value[0].value
      }
    }
  } catch (e) {
    console.error(e)
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const filters: Record<string, any> = {}
    if (searchName.value) filters.name = searchName.value
    if (filterStatus.value !== null) filters.status = filterStatus.value

    const res = await queryApiTokenList(page.value, pageSize.value, filters)
    const result = await res.json()
    if (result.code === 200) {
      list.value = result.data.records
      total.value = result.data.total_count
    } else {
      message.error(result.msg || '查询失败')
    }
  } catch (e) {
    console.error(e)
    message.error('网络错误')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  fetchData()
}

const handlePageChange = (p: number) => {
  page.value = p
  fetchData()
}

const handleAdd = () => {
  formModel.name = ''
  if (adminUsers.value.length > 0) {
    formModel.user_id = adminUsers.value[0].value
  }
  showCreateModal.value = true
}

const handleCreate = () => {
  formRef.value?.validate(async (errors) => {
    if (errors) return
    try {
      const payload: { name: string, user_id?: number } = { name: formModel.name }
      if (formModel.user_id) payload.user_id = formModel.user_id

      const res = await addApiToken(payload)
      const result = await res.json()
      if (result.code === 200) {
        showCreateModal.value = false
        createdToken.value = result.data.token
        tokenAcknowledged.value = false
        showTokenModal.value = true
        fetchData()
      } else {
        message.error(result.msg || '创建失败')
      }
    } catch (e) {
      console.error(e)
      message.error('网络错误')
    }
  })
}

const handleCopyToken = async () => {
  try {
    await navigator.clipboard.writeText(createdToken.value)
    message.success('已复制到剪贴板')
  } catch {
    message.error('复制失败，请手动复制')
  }
}

const closeTokenModal = () => {
  if (!tokenAcknowledged.value) {
    message.warning('请确认已保存 Token')
    return
  }
  showTokenModal.value = false
  createdToken.value = ''
}

const handleStatusChange = async (row: any, enabled: boolean) => {
  try {
    const res = enabled ? await enableApiToken(row.id) : await disableApiToken(row.id)
    const result = await res.json()
    if (result.code === 200) {
      message.success(enabled ? '已启用' : '已禁用')
      row.status = enabled ? 1 : 0
    } else {
      message.error(result.msg || '操作失败')
    }
  } catch (e) {
    console.error(e)
    message.error('网络错误')
  }
}

const handleDelete = (row: any) => {
  dialog.warning({
    title: '警告',
    content: `确定删除 Token「${row.name}」吗？删除后无法恢复。`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const res = await deleteApiToken(row.id)
        const result = await res.json()
        if (result.code === 200) {
          message.success('删除成功')
          fetchData()
        } else {
          message.error(result.msg || '删除失败')
        }
      } catch (e) {
        console.error(e)
        message.error('网络错误')
      }
    },
  })
}

onMounted(() => {
  fetchAdminUsers()
  fetchData()
})
</script>

<template>
  <div class="api-token-manager">
    <div class="header">
      <div class="title-section">
        <div class="i-material-symbols:key-outline text-24 text-primary mr-2"></div>
        <h2>API Token</h2>
      </div>
      <div class="actions">
        <n-input
          v-model:value="searchName"
          placeholder="搜索名称..."
          clearable
          class="search-input"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <div class="i-carbon-search text-gray-400"></div>
          </template>
        </n-input>
        <n-select
          v-model:value="filterStatus"
          :options="statusOptions"
          placeholder="状态"
          class="status-select"
          @update:value="handleSearch"
        />
        <n-button
          secondary
          @click="handleSearch"
        >
          <template #icon>
            <div class="i-carbon-search"></div>
          </template>
          搜索
        </n-button>
        <n-button
          type="primary"
          @click="handleAdd"
        >
          <template #icon>
            <div class="i-carbon-add"></div>
          </template>
          创建 Token
        </n-button>
      </div>
    </div>

    <div class="content">
      <n-alert
        type="info"
        :bordered="false"
        class="mb-4"
      >
        API Token 为永久有效，可用于脚本、CLI 及第三方系统集成。明文仅在创建时展示一次，请妥善保存。
      </n-alert>
      <n-data-table
        :columns="columns"
        :data="list"
        :loading="loading"
        :pagination="false"
        class="token-table"
      />
      <div
        v-if="total > 0"
        class="pagination-container"
      >
        <n-pagination
          v-model:page="page"
          :page-size="pageSize"
          :item-count="total"
          @update:page="handlePageChange"
        />
      </div>
    </div>

    <n-modal
      v-model:show="showCreateModal"
      preset="dialog"
      title="创建 API Token"
      style="width: 480px"
    >
      <n-form
        ref="formRef"
        :model="formModel"
        :rules="rules"
        label-placement="left"
        label-width="90"
        require-mark-placement="right-hanging"
        class="mt-4"
      >
        <n-form-item
          label="名称"
          path="name"
        >
          <n-input
            v-model:value="formModel.name"
            placeholder="如：生产环境-报表服务"
          />
        </n-form-item>
        <n-form-item label="绑定用户">
          <n-select
            v-model:value="formModel.user_id"
            :options="adminUsers"
            placeholder="选择管理员"
          />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showCreateModal = false">
            取消
          </n-button>
          <n-button
            type="primary"
            @click="handleCreate"
          >
            创建
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal
      v-model:show="showTokenModal"
      preset="dialog"
      title="请保存 Token"
      :mask-closable="false"
      :close-on-esc="false"
      style="width: 560px"
    >
      <n-alert
        type="warning"
        :bordered="false"
        class="mb-4"
      >
        此 Token 仅显示一次，关闭后将无法再次查看。如遗失请删除后重新创建。
      </n-alert>
      <div class="token-display">
        {{ createdToken }}
      </div>
      <n-space
        vertical
        class="mt-4"
      >
        <n-button
          type="primary"
          secondary
          block
          @click="handleCopyToken"
        >
          复制 Token
        </n-button>
        <n-checkbox v-model:checked="tokenAcknowledged">
          我已妥善保存此 Token
        </n-checkbox>
      </n-space>
      <template #action>
        <n-button
          type="primary"
          :disabled="!tokenAcknowledged"
          @click="closeTokenModal"
        >
          关闭
        </n-button>
      </template>
    </n-modal>
  </div>
</template>

<style lang="scss" scoped>
@use "@/styles/typography.scss" as *;

.api-token-manager {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #fff;

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    border-bottom: 1px solid #f3f4f6;

    .title-section {
      display: flex;
      align-items: center;

      h2 {
        @include h3-style;
        margin: 0;
        color: $heading-color;
      }
    }

    .actions {
      display: flex;
      align-items: center;
      gap: 12px;

      .search-input {
        width: 220px;
      }

      .status-select {
        width: 120px;
      }
    }
  }

  .content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding: 16px 24px;

    .token-table {
      flex: 1;
    }

    .pagination-container {
      margin-top: 16px;
      display: flex;
      justify-content: flex-end;
    }
  }

  .token-display {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 13px;
    word-break: break-all;
    padding: 12px;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    line-height: 1.6;
  }
}
</style>
