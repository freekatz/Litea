#!/usr/bin/env python3
"""
初始化数据库脚本
删除旧的数据库文件并创建新的数据库表
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.db.models import Base
from app.config import get_settings


async def init_database():
    """初始化数据库"""
    settings = get_settings()
    
    print("=" * 60)
    print(" 初始化数据库")
    print("=" * 60)
    print(f"数据库 URL: {settings.database.url}")
    
    # 如果是 SQLite，检查并删除旧文件
    if "sqlite" in settings.database.url:
        db_file = settings.database.url.replace("sqlite+aiosqlite:///", "")
        if db_file.startswith("./"):
            db_file = db_file[2:]
        
        if os.path.exists(db_file):
            print(f"\n删除旧的数据库文件: {db_file}")
            os.remove(db_file)
            
            # 删除 SQLite 临时文件
            for suffix in ["-shm", "-wal"]:
                temp_file = db_file + suffix
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"删除临时文件: {temp_file}")
    
    # 创建数据库引擎
    engine = create_async_engine(
        settings.database.url,
        echo=True,  # 显示 SQL 语句
    )
    
    print("\n创建数据库表...")
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("\n✓ 数据库初始化完成！")
    print("\n创建的表:")
    for table_name in sorted(Base.metadata.tables.keys()):
        print(f"  - {table_name}")
    
    # 显示 tasks 表的关键字段
    from sqlalchemy import inspect as sync_inspect
    async with engine.connect() as conn:
        def get_columns(connection):
            inspector = sync_inspect(connection)
            return inspector.get_columns('tasks')
        
        columns = await conn.run_sync(get_columns)
        print("\ntasks 表字段:")
        for col in columns:
            null_info = "NULL" if col['nullable'] else "NOT NULL"
            default_info = f" DEFAULT {col['default']}" if col.get('default') else ""
            print(f"  - {col['name']}: {col['type']} {null_info}{default_info}")
    
    print("\n功能特性:")
    print("  ✓ 任务管理（创建、启动、停止）")
    print("  ✓ 文献收集与存储")
    print("  ✓ 定时任务调度")
    print("  ✓ 任务归档功能（软删除）")
    
    await engine.dispose()
    print("\n" + "=" * 60)


def main():
    """主函数"""
    try:
        asyncio.run(init_database())
        return 0
    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
