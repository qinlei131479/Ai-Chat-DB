// import { mockEventStreamText } from '@/data'
// import { currentHost } from '@/utils/location'
// import request from '@/utils/request'

/**
 * SSE 流式聊天接口
 */
export async function streamChatAnswer(text, qa_type, uuid, chat_id, file_list, datasource_id, selected_skills?) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/api/chat/answer`)

  const controller = new AbortController()
  const timeoutId = setTimeout(() => {
    controller.abort()
  }, 36 * 60 * 1000)

  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      query: text,
      qa_type,
      uuid,
      chat_id,
      file_list,
      datasource_id,
      ...(selected_skills?.length ? { selected_skills } : {}),
    }),
    signal: controller.signal,
  })

  return fetch(req).finally(() => {
    clearTimeout(timeoutId)
  })
}

export async function login(username, password) {
  const url = new URL(`${location.origin}/api/user/login`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username,
      password,
    }),
  })
  return fetch(req)
}

export async function query_user_qa_record(page, limit, search_text, chat_id) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/api/user/query_user_record`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      page,
      size: limit,
      search_text,
      chat_id,
    }),
  })
  return fetch(req)
}

export async function query_user_record_list(page, limit, search_text) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/api/user/query_user_record_list`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      page,
      size: limit,
      search_text,
    }),
  })
  return fetch(req)
}

export async function delete_user_record(ids) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/api/user/delete_user_record`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      record_ids: ids,
    }),
  })
  return fetch(req)
}

export async function get_record_sql(record_id) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/api/user/get_record_sql`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      record_id,
    }),
  })
  return fetch(req)
}

export async function send_feedback(record_id: number, rating: 'like' | 'dislike') {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/api/user/feedback`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      record_id,
      rating,
    }),
  })
  return fetch(req)
}

export async function word_to_md(file_key) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/api/ta/word_to_md`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      file_key,
    }),
  })
  return fetch(req)
}

export async function query_demand_records(page, limit) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/api/ta/query_demand_records`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      page,
      limit,
    }),
  })
  return fetch(req)
}

export async function insert_demand_manager(project_data) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/api/ta/insert_demand_manager`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      project_data,
    }),
  })
  return fetch(req)
}

export async function delete_demand_records(id) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/api/ta/delete_demand_records`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      id,
    }),
  })
  return fetch(req)
}

export async function abstract_doc_func(doc_id) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/api/ta/abstract_doc_func`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      doc_id,
    }),
  })
  return fetch(req)
}

export async function stop_chat(task_id, qa_type) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/api/chat/stop`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      task_id,
      qa_type,
    }),
  })
  return fetch(req)
}

export async function resumeChat(thread_id: string, user_input: string) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/api/chat/resume`)

  const controller = new AbortController()
  const timeoutId = setTimeout(() => {
    controller.abort()
  }, 36 * 60 * 1000)

  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      thread_id,
      user_input,
    }),
    signal: controller.signal,
  })
  return fetch(req).finally(() => {
    clearTimeout(timeoutId)
  })
}
