import { useUserStore } from '@/store/business/userStore'

const BASE_URL = `${location.origin}/sanic/user/api_token`

const getHeaders = () => {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  }
}

export async function queryApiTokenList(
  page: number,
  size: number,
  filters?: { name?: string, user_id?: number, status?: number },
) {
  const url = new URL(`${BASE_URL}/list`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: getHeaders(),
    body: JSON.stringify({ page, size, ...filters }),
  })
  return fetch(req)
}

export async function addApiToken(data: { name: string, user_id?: number }) {
  const url = new URL(`${BASE_URL}/add`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: getHeaders(),
    body: JSON.stringify(data),
  })
  return fetch(req)
}

export async function enableApiToken(id: number) {
  const url = new URL(`${BASE_URL}/enable`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: getHeaders(),
    body: JSON.stringify({ id }),
  })
  return fetch(req)
}

export async function disableApiToken(id: number) {
  const url = new URL(`${BASE_URL}/disable`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: getHeaders(),
    body: JSON.stringify({ id }),
  })
  return fetch(req)
}

export async function deleteApiToken(id: number) {
  const url = new URL(`${BASE_URL}/delete`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: getHeaders(),
    body: JSON.stringify({ id }),
  })
  return fetch(req)
}
