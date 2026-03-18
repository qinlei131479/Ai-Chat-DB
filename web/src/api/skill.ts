/**
 * 技能相关 API 封装
 */
import { useUserStore } from '@/store/business/userStore'

/**
 * 获取技能列表
 */
export async function fetch_skill_list() {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/agi/system/skill/list`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'get',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  return fetch(req)
}
