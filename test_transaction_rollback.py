"""
测试事务回滚机制
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db.database import async_get_db
from app.crud.crud_users import crud_users
from app.crud.crud_roles import crud_roles
from app.crud.crud_user_roles import assign_role_to_user, list_user_roles
from app.schemas.user import UserCreateInternal
from app.core.security import get_password_hash


async def test_transaction_rollback():
    """测试事务回滚机制"""
    print("开始测试事务回滚机制...")
    
    async for db in async_get_db():
        try:
            # 测试场景1: 用户创建过程中角色分配失败
            print("\n测试场景1: 用户创建过程中角色分配失败")
            
            # 创建测试用户数据
            test_user_data = UserCreateInternal(
                name="Test User",
                username="testtxuser",  # 使用符合正则表达式的用户名 (只包含小写字母和数字)
                email="test_transaction@example.com",
                hashed_password=get_password_hash("testpassword123")
            )
            
            try:
                # 使用事务上下文管理器
                async with db.begin():
                    # 创建用户
                    created_user = await crud_users.create(db=db, object=test_user_data)
                    print(f"用户创建成功: {created_user.username}")
                    
                    # 尝试分配一个不存在的角色 (这应该会失败)
                    await assign_role_to_user(db, created_user.id, 99999)  # 不存在的角色ID
                    print("角色分配成功")  # 这行不应该执行到
                    
            except Exception as e:
                print(f"✅ 正确: 捕获到异常并回滚事务: {e}")
                
                # 验证用户是否被回滚（不存在）
                user_exists = await crud_users.exists(db=db, username="testtxuser")
                if user_exists:
                    print("❌ 错误: 事务回滚失败，用户仍然存在")
                else:
                    print("✅ 正确: 事务回滚成功，用户不存在")
            
            # 测试场景2: 正常的事务提交
            print("\n测试场景2: 正常的事务提交")
            
            try:
                # 创建不同的测试用户数据
                test_user_data2 = UserCreateInternal(
                    name="Test User 2",
                    username="testtxuser2",  # 不同的用户名
                    email="test_transaction2@example.com",  # 不同的邮箱
                    hashed_password=get_password_hash("testpassword123")
                )
                
                # 获取一个存在的角色ID
                roles = await crud_roles.get_multi(db=db, limit=1)
                if not roles or len(roles) == 0:
                    print("❌ 错误: 找不到测试用的角色")
                    return
                
                existing_role = roles[0]
                
                # 使用事务上下文管理器
                async with db.begin():
                    # 创建用户
                    created_user = await crud_users.create(db=db, object=test_user_data2)
                    print(f"用户创建成功: {created_user.username}")
                    
                    # 分配存在的角色
                    await assign_role_to_user(db, created_user.id, existing_role.id)
                    print(f"角色分配成功: role_id={existing_role.id}")
                
                # 验证用户和角色分配是否都存在
                user_exists = await crud_users.exists(db=db, username="testtxuser2")
                user_roles = await list_user_roles(db, created_user.id)
                
                if user_exists and len(user_roles) > 0:
                    print("✅ 正确: 正常事务提交成功，用户和角色分配都存在")
                    
                    # 清理测试数据
                    await crud_users.delete(db=db, id=created_user.id)
                    async with db.begin():
                        pass  # 提交删除操作
                    print("测试数据清理完成")
                else:
                    print("❌ 错误: 正常事务提交失败")
                    
            except Exception as e:
                print(f"❌ 错误: 正常事务失败: {e}")
            
            print("\n事务回滚测试完成")
            
        except Exception as e:
            print(f"测试过程中发生错误: {str(e)}")
        finally:
            await db.close()
        break


if __name__ == "__main__":
    asyncio.run(test_transaction_rollback())