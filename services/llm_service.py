import json
import logging
import re
import traceback

from agent.common.enhanced_common_agent import EnhancedCommonAgent
from agent.deepagent.deep_research_agent import DeepAgent
from agent.excel.excel_agent import ExcelAgent
from agent.text2sql.text2_sql_agent import Text2SqlAgent
from common.exception import MyException
from constants.code_enum import IntentEnum, SysCodeEnum
from services.auth_service import resolve_token

logger = logging.getLogger(__name__)

common_agent = EnhancedCommonAgent()
sql_agent = Text2SqlAgent()
excel_agent = ExcelAgent()
deep_agent = DeepAgent()


class LLMRequest:
    """聊天请求路由服务：按 qa_type 分发到本地 Agent。"""

    async def exec_query(self, res, req_obj=None, token=None):
        try:
            if req_obj is None:
                req_body_content = res.request.body
                body_str = req_body_content.decode("utf-8")
                req_obj = json.loads(body_str)

            logging.info(f"query param: {json.dumps(req_obj, ensure_ascii=False)}")

            chat_id = req_obj.get("chat_id")
            qa_type = req_obj.get("qa_type")
            uuid_str = req_obj.get("uuid")
            file_list = req_obj.get("file_list")
            datasource_id = req_obj.get("datasource_id")
            query = req_obj.get("query")
            cleaned_query = re.sub(r"\s+", "", query) if query else ""

            if token is None:
                token = res.request.headers.get("Authorization")
                if not token:
                    raise MyException(SysCodeEnum.c_401)
                if token.startswith("Bearer "):
                    token = token.split(" ")[1]

            selected_skills = req_obj.get("selected_skills")

            if qa_type == IntentEnum.COMMON_QA.value[0]:
                await common_agent.run_agent(
                    query,
                    res,
                    chat_id,
                    uuid_str,
                    token,
                    file_list,
                    selected_skills=selected_skills,
                )
            elif qa_type == IntentEnum.DATABASE_QA.value[0]:
                await sql_agent.run_agent(
                    query, res, chat_id, uuid_str, token, datasource_id
                )
            elif qa_type == IntentEnum.FILEDATA_QA.value[0]:
                await excel_agent.run_excel_agent(
                    cleaned_query, res, chat_id, uuid_str, token, file_list
                )
            elif qa_type == IntentEnum.REPORT_QA.value[0]:
                await deep_agent.run_agent(
                    cleaned_query,
                    res,
                    chat_id,
                    uuid_str,
                    token,
                    file_list,
                    datasource_id,
                )
            else:
                raise MyException(SysCodeEnum.PARAM_ERROR, f"不支持的问答类型: {qa_type}")

        except MyException:
            raise
        except Exception as e:
            logging.error(f"Error during exec_query: {e}")
            traceback.print_exception(e)
            raise MyException(SysCodeEnum.c_9999) from e


async def stop_chat(request, task_id, qa_type) -> dict:
    """停止正在进行的 Agent 对话流。"""
    token = request.headers.get("Authorization")
    if not token:
        raise MyException(SysCodeEnum.c_401)
    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    user_dict = resolve_token(token) or {}
    cancel_task_id = user_dict["id"]

    if qa_type == IntentEnum.COMMON_QA.value[0]:
        success = await common_agent.cancel_task(cancel_task_id)
    elif qa_type == IntentEnum.DATABASE_QA.value[0]:
        success = await sql_agent.cancel_task(cancel_task_id)
    elif qa_type == IntentEnum.FILEDATA_QA.value[0]:
        success = await excel_agent.cancel_task(cancel_task_id)
    elif qa_type == IntentEnum.REPORT_QA.value[0]:
        success = await deep_agent.cancel_task(cancel_task_id)
    else:
        raise MyException(SysCodeEnum.PARAM_ERROR, f"不支持的问答类型: {qa_type}")

    return {
        "success": success,
        "message": "任务已停止" if success else "未找到任务",
    }
