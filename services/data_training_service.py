import logging
import math
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, desc, or_, and_

from common.exception import MyException
from constants.code_enum import SysCodeEnum
from model.db_connection_pool import get_db_pool
from model.db_models import SqlTrain, TAiModel
from model.datasource_models import Datasource
from model.schemas import DataTrainingItem, PaginatedResponse
from services.embedding_service import generate_embedding

logger = logging.getLogger(__name__)
pool = get_db_pool()


async def page_data_training(page: int, size: int, question: Optional[str] = None, oid: int = 1) -> Dict[str, Any]:
    with pool.get_session() as session:
        # Build query
        query = (
            session.query(
                SqlTrain,
                Datasource.name.label("datasource_name")
            )
            .outerjoin(Datasource, SqlTrain.ds_id == Datasource.id)
        )

        if question:
            query = query.filter(SqlTrain.question.ilike(f"%{question}%"))

        # Count total
        total_count = query.count()
        total_pages = math.ceil(total_count / size) if size > 0 else 0

        # Pagination
        offset = (page - 1) * size
        results = query.order_by(desc(SqlTrain.create_time)).offset(offset).limit(size).all()

        # Serialize
        items = []
        for row in results:
            training, ds_name = row
            items.append(
                DataTrainingItem(
                    id=str(training.id),
                    question=training.question,
                    description=training.description,
                    ds_id=str(training.ds_id),
                    datasource_name=ds_name,
                    enabled_flag=training.enabled_flag,
                    create_time=str(training.create_time) if training.create_time else None,
                )
            )

        return {"records": items, "total_count": total_count, "current_page": page, "total_pages": total_pages}


async def create_training(data: Dict[str, Any]) -> bool:
    question = data.get("question")
    description = data.get("description")
    datasource = data.get("datasource")
    advanced_application = data.get("advanced_application")

    if not question:
        raise MyException(SysCodeEnum.PARAM_ERROR, "Question cannot be empty")

    # Generate embedding - 优先使用用户配置的模型，没有则使用离线模型
    embedding = await generate_embedding(question)

    with pool.get_session() as session:
        # Check duplicates
        query = session.query(SqlTrain).filter(SqlTrain.question == question)

        if datasource and advanced_application:
            query = query.filter(SqlTrain.ds_id == datasource)
        elif datasource:
            query = query.filter(SqlTrain.ds_id == datasource)

        if query.count() > 0:
            raise MyException(SysCodeEnum.PARAM_ERROR, "Training data already exists")

        new_training = SqlTrain(
            ds_id=datasource,
            question=question,
            description=description,
            embedding=embedding,
            enabled_flag=data.get("enabled_flag", 1),
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        session.add(new_training)
        session.commit()
        return True


async def update_training(data: Dict[str, Any]) -> bool:
    question = data.get("question")

    with pool.get_session() as session:
        training_id = data.get("id")
        training = session.query(SqlTrain).filter(SqlTrain.id == training_id).first()
        if not training:
            raise MyException(SysCodeEnum.PARAM_ERROR, "Training data not found")

        # Check if question changed to update embedding
        embedding = None
        if question and question != training.question:
            pass

    # Refactored update logic:
    training_id = data.get("id")
    current_question = None

    with pool.get_session() as session:
        training = session.query(SqlTrain).filter(SqlTrain.id == training_id).first()
        if not training:
            raise MyException(SysCodeEnum.PARAM_ERROR, "Training data not found")
        current_question = training.question

    embedding = None
    if question and question != current_question:
        # 优先使用用户配置的模型，没有则使用离线模型
        embedding = await generate_embedding(question)

    with pool.get_session() as session:
        training = session.query(SqlTrain).filter(SqlTrain.id == training_id).first()
        if training:
            if question:
                training.question = question
            if embedding:
                training.embedding = embedding

            training.description = data.get("description", training.description)
            training.ds_id = data.get("ds_id", training.ds_id)
            training.enabled_flag = data.get("enabled_flag", 1)
            training.update_time = datetime.now()

            session.commit()
            return True
        return False


async def delete_training(ids: List[int]) -> bool:
    with pool.get_session() as session:
        session.query(SqlTrain).filter(SqlTrain.id.in_(ids)).delete(synchronize_session=False)
        session.commit()
        return True


async def enable_training(training_id: int, enabled: bool) -> bool:
    with pool.get_session() as session:
        training = session.query(SqlTrain).filter(SqlTrain.id == training_id).first()
        if not training:
            raise MyException(SysCodeEnum.PARAM_ERROR, "Training data not found")

        training.enabled_flag = 1 if enabled else 0
        session.commit()
        return True
