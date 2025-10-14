"""
Unit of Work decorator for automatic database transaction management.

This module provides decorators that automatically manage database transactions
for FastAPI route functions, ensuring that all database operations within a
function either succeed completely or fail completely (atomicity).
"""

import functools
import inspect
import logging
from typing import Any, Callable, ParamSpec, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from ..exceptions.config_exceptions import MissingDatabaseSessionError

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


def unit_of_work(
    db_param_name: str = "db",
    commit_on_success: bool = True
):
    """
    工作单元装饰器，为路由函数自动管理数据库事务。
    
    Args:
        db_param_name: 数据库会话参数的名称，默认为 "db"
        commit_on_success: 是否在成功时自动提交，默认为 True
    
    功能：
    - 自动开始事务
    - 成功时自动提交
    - 任何异常时自动回滚
    - 支持嵌套事务（savepoint）
    
    使用示例:
        @unit_of_work()
        async def create_user(user_data: UserCreate, db: AsyncSession):
            # 所有数据库操作都在同一个事务中
            user = await crud_users.create(db=db, object=user_data, commit=False)
            # 如果后续任何操作失败（包括文件操作、外部API调用等），
            # 数据库事务都会自动回滚
            return user
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # 获取数据库会话
            db_session = None
            
            # 从 kwargs 中查找数据库会话
            if db_param_name in kwargs:
                db_session = kwargs[db_param_name]
            else:
                # 从 args 中查找（需要通过函数签名推断位置）
                try:
                    sig = inspect.signature(func)
                    param_names = list(sig.parameters.keys())
                    
                    if db_param_name in param_names:
                        param_index = param_names.index(db_param_name)
                        if param_index < len(args):
                            db_session = args[param_index]
                except Exception as e:
                    logger.warning(f"Failed to inspect function signature: {e}")
            
            if not isinstance(db_session, AsyncSession):
                msg = (
                    f"AsyncSession not found or invalid type for parameter '{db_param_name}'. "
                    "Ensure your route includes the dependency, e.g., "
                    f"`{db_param_name}: AsyncSession = Depends(async_get_db)`, or configure db_param_name correctly."
                )
                logger.error(msg)
                # 未找到或类型无效时，抛出明确的配置错误
                raise MissingDatabaseSessionError(msg)
            
            # 检查是否已经在事务中
            if db_session.in_transaction():
                # 如果已经在事务中，使用 savepoint
                async with db_session.begin_nested() as savepoint:
                    try:
                        result = await func(*args, **kwargs)
                        if commit_on_success:
                            # savepoint 会在 context manager 退出时自动提交
                            pass
                        return result
                    except Exception as e:
                        # 任何异常都回滚 savepoint
                        await savepoint.rollback()
                        logger.info(f"Savepoint rolled back due to exception: {str(e)}")
                        raise
            else:
                # 开始新事务
                async with db_session.begin():
                    try:
                        result = await func(*args, **kwargs)
                        # 事务会在 context manager 退出时自动提交
                        return result
                    except Exception as e:
                        # 任何异常都回滚事务
                        logger.info(f"Transaction rolled back due to exception: {str(e)}")
                        raise
        
        return wrapper
    return decorator


def transactional(db_param_name: str = "db"):
    """
    简化版本的事务装饰器，任何异常都回滚。
    
    这是最常用的装饰器，适用于大多数写操作场景。
    
    Args:
        db_param_name: 数据库会话参数的名称，默认为 "db"
    
    使用示例:
        @transactional()
        async def create_user(user_data: UserCreate, db: AsyncSession):
            user = await crud_users.create(db=db, object=user_data, commit=False)
            # 任何后续操作失败都会回滚数据库事务
            return user
    """
    return unit_of_work(
        db_param_name=db_param_name,
        commit_on_success=True
    )


def read_only_transaction(db_param_name: str = "db"):
    """
    只读事务装饰器，不会提交任何更改。
    
    适用于复杂的查询操作，确保数据一致性但不提交更改。
    
    Args:
        db_param_name: 数据库会话参数的名称，默认为 "db"
    
    使用示例:
        @read_only_transaction()
        async def get_user_stats(db: AsyncSession):
            # 只读操作，不会提交更改
            return await crud_users.get_stats(db=db)
    """
    return unit_of_work(
        db_param_name=db_param_name,
        commit_on_success=False
    )