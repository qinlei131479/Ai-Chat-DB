const LayoutDefault = () => import('@/components/Layout/default.vue')

const childrenRoutes: Array<RouteRecordRaw> = [
  {
    path: 'skill-center',
    name: 'SkillCenter',
    component: () => import('@/views/skills/skill-center.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: 'chat',
    meta: { requiresAuth: true },
    name: 'ChatRoot',
    redirect: {
      name: 'ChatIndex',
    },
    children: [
      {
        path: '',
        name: 'ChatIndex',
        component: () => import('@/views/chat/index.vue'),
      },
    ],
  },
  {
    path: 'datasource',
    name: 'DatasourceManager',
    component: () => import('@/views/system/datasource/index.vue'),
    meta: { requiresAuth: true }, // 标记需要认证
  },
  {
    path: 'datasource/table/:dsId/:dsName',
    name: 'DatasourceTableList',
    component: () => import('@/views/system/datasource/datasource-table-list.vue'),
    meta: { requiresAuth: true }, // 标记需要认证
  },
  {
    path: 'user-manager',
    name: 'UserManager',
    component: () => import('@/views/system/user/index.vue'),
    meta: { requiresAuth: true },
  },

  {
    path: 'llm-config',
    name: 'LLMConfig',
    component: () => import('@/views/system/supplier-model/index.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: 'terminology-config',
    name: 'TerminologyConfig',
    component: () => import('@/views/system/terminology/index.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: 'set/training',
    name: 'SqlExampleLibrary',
    component: () => import('@/views/system/sql-train/index.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: 'system-settings',
    name: 'SystemSettings',
    component: () => import('@/views/system/system-settings.vue'),
    meta: { requiresAuth: true },
  },
]

export default childrenRoutes
