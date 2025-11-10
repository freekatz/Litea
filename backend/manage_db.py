#!/usr/bin/env python3
"""
数据库管理工具
提供初始化、检查、备份等功能
"""

import asyncio
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.models import Base
from app.config import get_settings


async def check_database():
    """检查数据库状态"""
    settings = get_settings()
    
    print("=" * 60)
    print(" 数据库状态检查")
    print("=" * 60)
    print(f"数据库 URL: {settings.database.url}\n")
    
    # 检查文件是否存在
    if "sqlite" in settings.database.url:
        db_file = settings.database.url.replace("sqlite+aiosqlite:///", "").replace("./", "")
        if os.path.exists(db_file):
            size = os.path.getsize(db_file)
            print(f"✓ 数据库文件存在: {db_file}")
            print(f"  大小: {size:,} bytes ({size/1024:.2f} KB)")
        else:
            print(f"✗ 数据库文件不存在: {db_file}")
            return False
    
    # 检查表结构
    try:
        engine = create_async_engine(settings.database.url, echo=False)
        
        async with engine.connect() as conn:
            # 获取所有表名
            def get_table_names(connection):
                inspector = inspect(connection)
                return inspector.get_table_names()
            
            def get_table_columns(connection, table_name):
                inspector = inspect(connection)
                return inspector.get_columns(table_name)
            
            existing_tables = await conn.run_sync(get_table_names)
            expected_tables = set(Base.metadata.tables.keys())
            
            print(f"\n数据库表状态:")
            print(f"  预期表数: {len(expected_tables)}")
            print(f"  实际表数: {len(existing_tables)}")
            
            missing_tables = expected_tables - set(existing_tables)
            extra_tables = set(existing_tables) - expected_tables
            
            if missing_tables:
                print(f"\n✗ 缺失的表: {', '.join(missing_tables)}")
            if extra_tables:
                print(f"\n⚠ 额外的表: {', '.join(extra_tables)}")
            
            if not missing_tables and not extra_tables:
                print("\n✓ 所有表结构正确")
                print("\n表列表:")
                for table in sorted(existing_tables):
                    print(f"  - {table}")
                
                # 检查 tasks 表的关键字段
                if 'tasks' in existing_tables:
                    columns = await conn.run_sync(lambda c: get_table_columns(c, 'tasks'))
                    column_names = [col['name'] for col in columns]
                    
                    print("\ntasks 表字段检查:")
                    required_fields = ['id', 'name', 'prompt', 'status', 'is_archived', 'created_at']
                    for field in required_fields:
                        status = "✓" if field in column_names else "✗"
                        print(f"  {status} {field}")
                    
                    if 'is_archived' in column_names:
                        print("\n  ✓ is_archived 字段已存在（归档功能支持）")
                    else:
                        print("\n  ⚠ is_archived 字段不存在，需要运行迁移脚本")
                
                await engine.dispose()
                return True
            else:
                await engine.dispose()
                return False
                
    except Exception as e:
        print(f"\n✗ 数据库检查失败: {e}")
        return False
    
    print("\n" + "=" * 60)


async def init_database(force=False):
    """初始化数据库"""
    settings = get_settings()
    
    print("=" * 60)
    print(" 初始化数据库")
    print("=" * 60)
    print(f"数据库 URL: {settings.database.url}")
    
    # 如果是 SQLite，处理文件
    if "sqlite" in settings.database.url:
        db_file = settings.database.url.replace("sqlite+aiosqlite:///", "").replace("./", "")
        
        if os.path.exists(db_file):
            if force:
                # 备份现有数据库
                backup_name = f"{db_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                print(f"\n备份现有数据库到: {backup_name}")
                shutil.copy2(db_file, backup_name)
                
                print(f"删除旧的数据库文件: {db_file}")
                os.remove(db_file)
                
                # 删除 SQLite 临时文件
                for suffix in ["-shm", "-wal"]:
                    temp_file = db_file + suffix
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
            else:
                print(f"\n⚠ 数据库文件已存在: {db_file}")
                print("  使用 --force 参数强制重建")
                return False
    
    # 创建数据库引擎
    engine = create_async_engine(settings.database.url, echo=False)
    
    print("\n创建数据库表...")
    
    try:
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
        
        await engine.dispose()
        print("\n" + "=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        await engine.dispose()
        return False


async def backup_database():
    """备份数据库"""
    settings = get_settings()
    
    if "sqlite" not in settings.database.url:
        print("✗ 只支持 SQLite 数据库备份")
        return False
    
    db_file = settings.database.url.replace("sqlite+aiosqlite:///", "").replace("./", "")
    
    if not os.path.exists(db_file):
        print(f"✗ 数据库文件不存在: {db_file}")
        return False
    
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    backup_name = backup_dir / f"litea_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    print(f"备份数据库...")
    print(f"  源文件: {db_file}")
    print(f"  备份文件: {backup_name}")
    
    shutil.copy2(db_file, backup_name)
    
    print(f"\n✓ 备份完成")
    print(f"  大小: {os.path.getsize(backup_name):,} bytes")
    
    return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库管理工具")
    parser.add_argument(
        "action",
        choices=["check", "init", "backup"],
        help="操作: check(检查) | init(初始化) | backup(备份)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重建数据库（会备份旧数据）"
    )
    
    args = parser.parse_args()
    
    try:
        if args.action == "check":
            result = asyncio.run(check_database())
        elif args.action == "init":
            result = asyncio.run(init_database(force=args.force))
        elif args.action == "backup":
            result = asyncio.run(backup_database())
        
        return 0 if result else 1
        
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        return 1
    except Exception as e:
        print(f"\n✗ 操作失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
