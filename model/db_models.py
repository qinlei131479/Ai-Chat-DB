import datetime
from typing import List, Optional, Union

from sqlalchemy import (
    BigInteger,
    Boolean,
    Integer,
    String,
    TIMESTAMP,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import VECTOR

from model.db_connection_pool import Base

"""
读取数据生成ORM数据库实体Bean
sqlacodegen postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/chat_db --outfile=models.py
"""


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    userName: Mapped[Optional[str]] = mapped_column(String(200), comment="用户名称")
    password: Mapped[Optional[str]] = mapped_column(String(300), comment="密码")
    mobile: Mapped[Optional[str]] = mapped_column(String(100), comment="手机号")
    role: Mapped[Optional[str]] = mapped_column(String(20), default="user", comment="角色: admin/user")
    createTime: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, comment="创建时间")
    updateTime: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, comment="修改时间")


class UserQaRecord(Base):
    __tablename__ = "user_qa_record"
    __table_args__ = {"comment": "问答记录表"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, comment="用户id")
    uuid: Mapped[Optional[str]] = mapped_column(String(200), comment="自定义id")
    conversation_id: Mapped[Optional[str]] = mapped_column(String(100), comment="对话id")
    message_id: Mapped[Optional[str]] = mapped_column(String(100), comment="消息id")
    task_id: Mapped[Optional[str]] = mapped_column(String(100), comment="任务id")
    chat_id: Mapped[Optional[str]] = mapped_column(String(100), comment="对话id")
    question: Mapped[Optional[str]] = mapped_column(Text, comment="用户问题")
    to2_answer: Mapped[Optional[str]] = mapped_column(Text, comment="大模型答案")
    to4_answer: Mapped[Optional[str]] = mapped_column(Text, comment="业务数据")
    qa_type: Mapped[Optional[str]] = mapped_column(String(100), comment="问答类型")
    datasource_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="数据源ID")
    file_key: Mapped[Optional[str]] = mapped_column(String(100), comment="文件minio/key")
    sql_statement: Mapped[Optional[str]] = mapped_column(Text, comment="SQL语句（数据问答时保存）")
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment="创建时间"
    )


class Supplier(Base):
    __tablename__ = "supplier"
    __table_args__ = {"comment": "AI供应商表"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="供应商名称")
    description: Mapped[str] = mapped_column(String(255), nullable=False, comment="供应商描述")
    logo: Mapped[str] = mapped_column(String(255), nullable=False, comment="供应商Logo")
    api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="API Key")
    api_domain: Mapped[str] = mapped_column(String(255), nullable=False, comment="API Domain")
    api_apply_domain: Mapped[str] = mapped_column(String(255), nullable=False, comment="API key 申请Domain")

    status: Mapped[str] = mapped_column(String(10), default='0', nullable=False, comment="状态: 0:正常，1停用")
    del_flag: Mapped[str] = mapped_column(String(10), default='0', nullable=False, comment="删除标识，0：存在，1：删除")
    create_by: Mapped[str] = mapped_column(String(32), nullable=False, comment="创建人")
    update_by: Mapped[str] = mapped_column(String(32), nullable=False, comment="更新人")
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment="创建时间"
    )
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment="更新时间"
    )


class SupplierModel(Base):
    __tablename__ = "supplier_model"
    __table_args__ = {"comment": "供应商模型表"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    supplier_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="供应商表(supplier)的Id", )
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="模型名称")
    base_model: Mapped[str] = mapped_column(String(255), nullable=False, comment="模型名称（别名）")
    model_type: Mapped[str] = mapped_column(String(2), default='1', nullable=False,
                                            comment="模型类型: 1:聊天, 2:推理, 3:向量，4：排序，5：图片，6：视觉")
    description: Mapped[str] = mapped_column(String(255), nullable=False, comment="模型描述")
    context_length: Mapped[str] = mapped_column(String(50), nullable=False, comment="模型上下文长度")
    default_flag: Mapped[str] = mapped_column(String(2), default='0', nullable=False, comment="默认模型，0：否，1：是")
    ext_config: Mapped[Optional[str]] = mapped_column(Text, comment="模型扩展配置")
    del_flag: Mapped[str] = mapped_column(String(10), default='0', nullable=False, comment="删除标识，0：存在，1：删除")
    create_by: Mapped[str] = mapped_column(String(32), nullable=False, comment="创建人")
    update_by: Mapped[str] = mapped_column(String(32), nullable=False, comment="更新人")
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment="创建时间"
    )
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment="更新时间"
    )


class Terminology(Base):
    __tablename__ = "terminology"
    __table_args__ = {"comment": "术语配置表"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # oid: Mapped[Optional[int]] = mapped_column(BigInteger, default=1, comment="组织ID")
    parent_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="父ID")
    word: Mapped[Optional[str]] = mapped_column(String(255), comment="术语名称")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="描述")
    specific_ds: Mapped[Optional[int]] = mapped_column(Integer, default=0, comment="是否指定数据源")
    datasource_ids: Mapped[Optional[str]] = mapped_column(Text, comment="数据源ID列表(JSON)")
    enabled_flag: Mapped[Optional[int]] = mapped_column(Integer, default=1, comment="是否启用")
    # VECTOR 类型：用于在数据库中进行向量相似度搜索（使用 <=> 操作符）
    # 不指定维度，支持动态维度（768/1024等），pgvector 会自动处理
    # Python 类型：List[float] 或 numpy.ndarray，SQLAlchemy 会自动转换
    embedding: Mapped[Optional[Union[List[float], str]]] = mapped_column(
        VECTOR, nullable=True, comment="术语向量数据（pgvector VECTOR 类型，支持动态维度）"
    )
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment="创建时间"
    )
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment="更新时间"
    )


class SqlTrain(Base):
    __tablename__ = "sql_train"
    __table_args__ = {"comment": "SQL数据训练表"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ds_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="数据源ID")
    question: Mapped[Optional[str]] = mapped_column(String(255), comment="问题描述")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="示例SQL")
    # VECTOR 类型：用于在数据库中进行向量相似度搜索（使用 <=> 操作符）
    # 不指定维度，支持动态维度（768/1024等），pgvector 会自动处理
    # Python 类型：List[float] 或 numpy.ndarray，SQLAlchemy 会自动转换
    embedding: Mapped[Optional[Union[List[float], str]]] = mapped_column(
        VECTOR, nullable=True, comment="向量数据（pgvector VECTOR 类型，支持动态维度）"
    )
    enabled_flag: Mapped[Optional[int]] = mapped_column(Integer, default=1, comment="是否启用")
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment="创建时间"
    )
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment="更新时间"
    )
