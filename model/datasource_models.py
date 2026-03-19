"""
数据源管理模型
"""
import datetime
from typing import Optional, List

from sqlalchemy import BigInteger, DateTime, Text, String
from sqlalchemy.orm import Mapped, mapped_column
from model.db_connection_pool import Base


class Datasource(Base):
    """数据源表"""
    __tablename__ = "datasource"
    __table_args__ = {"comment": "数据源表"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="数据源名称")
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="描述")
    url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="jdbcurl")
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="用户名")
    password: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="密码(加密)")
    ds_type: Mapped[str] = mapped_column(String(64), nullable=False,
                                         comment="数据源类型: mysql, postgresql, oracle, sqlserver等")
    ds_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="数据库名称")
    conf_type: Mapped[str] = mapped_column(Text, nullable=False, comment="配置信息(加密)")
    instance: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="实例")
    port: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="密码(加密)")
    host: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="端口")
    del_flag: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="删除标记，0正常；1删除")
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True, comment="创建时间")
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True, comment="更新时间")
    status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="状态: Success, Failed")


class DatasourceTable(Base):
    """数据源表信息"""
    __tablename__ = "datasource_table"
    __table_args__ = {"comment": "数据源表信息"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ds_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="数据源ID")
    checked_flag: Mapped[int] = mapped_column(default=1, comment="是否选中，0否1是")
    table_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="表名")
    table_comment: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="表注释")
    custom_comment: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="自定义注释")
    # 表结构向量：基于“表名 + 注释 + 字段名 + 字段注释”的文本生成的 embedding，存为 JSON 数组字符串
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="表结构 embedding (JSON 数组字符串)")
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True, comment="创建时间")
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True, comment="更新时间")


class DatasourceTableField(Base):
    """数据源字段信息"""
    __tablename__ = "datasource_table_field"
    __table_args__ = {"comment": "数据源字段信息"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ds_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="数据源ID")
    table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="表ID")
    field_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="字段名")
    field_type: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="字段类型")
    field_comment: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="字段注释")
    custom_comment: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="自定义注释")
    data_mapping: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="数据映射")
    weight: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="字段顺序")
    create_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True, comment="创建时间")
    update_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True, comment="更新时间")
