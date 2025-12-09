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


async def migrate_document_constraint():
    """
    迁移 documents 表的唯一约束
    从 (external_id, source_name) 改为 (task_id, external_id, source_name)
    这样不同任务可以有相同的文献，互不影响
    """
    settings = get_settings()
    
    print("=" * 60)
    print(" 迁移 documents 表唯一约束")
    print("=" * 60)
    
    if "sqlite" not in settings.database.url:
        print("✗ 只支持 SQLite 数据库迁移")
        return False
    
    db_file = settings.database.url.replace("sqlite+aiosqlite:///", "").replace("./", "")
    
    if not os.path.exists(db_file):
        print(f"✗ 数据库文件不存在: {db_file}")
        return False
    
    # 先备份
    print("\n1. 备份数据库...")
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    backup_name = backup_dir / f"litea_before_migrate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(db_file, backup_name)
    print(f"   备份到: {backup_name}")
    
    engine = create_async_engine(settings.database.url, echo=False)
    
    try:
        async with engine.begin() as conn:
            from sqlalchemy import text
            
            # 检查当前约束
            print("\n2. 检查当前表结构...")
            result = await conn.execute(text("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='documents'
            """))
            row = result.fetchone()
            
            if row:
                current_sql = row[0]
                print(f"   当前表定义:\n   {current_sql[:200]}...")
                
                if 'uq_task_document_source' in current_sql:
                    print("\n✓ 约束已经是正确的 (task_id, external_id, source_name)")
                    print("  无需迁移")
                    await engine.dispose()
                    return True
            
            print("\n3. 开始迁移...")
            
            # SQLite 不支持直接修改约束，需要重建表
            # 步骤：创建新表 -> 复制数据 -> 删除旧表 -> 重命名新表
            
            # 创建新表
            print("   创建新表 documents_new...")
            await conn.execute(text("""
                CREATE TABLE documents_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    run_id INTEGER,
                    source_name VARCHAR(100) NOT NULL,
                    external_id VARCHAR(255) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    authors JSON DEFAULT '[]',
                    abstract TEXT,
                    url VARCHAR(500),
                    published_at DATETIME,
                    keywords JSON DEFAULT '[]',
                    user_keywords JSON DEFAULT '[]',
                    extra_metadata JSON DEFAULT '{}',
                    is_filtered_in BOOLEAN DEFAULT 0,
                    rank_score FLOAT,
                    zotero_key VARCHAR(20),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
                    FOREIGN KEY (run_id) REFERENCES task_runs(id) ON DELETE SET NULL,
                    UNIQUE (task_id, external_id, source_name)
                )
            """))
            
            # 复制数据
            print("   复制数据到新表...")
            await conn.execute(text("""
                INSERT INTO documents_new 
                SELECT * FROM documents
            """))
            
            # 检查数据数量
            result = await conn.execute(text("SELECT COUNT(*) FROM documents"))
            old_count = result.scalar()
            result = await conn.execute(text("SELECT COUNT(*) FROM documents_new"))
            new_count = result.scalar()
            print(f"   原表记录数: {old_count}, 新表记录数: {new_count}")
            
            if old_count != new_count:
                print("   ✗ 数据复制失败，记录数不匹配！")
                print("   回滚...")
                await conn.execute(text("DROP TABLE documents_new"))
                await engine.dispose()
                return False
            
            # 删除旧表
            print("   删除旧表...")
            await conn.execute(text("DROP TABLE documents"))
            
            # 重命名新表
            print("   重命名新表...")
            await conn.execute(text("ALTER TABLE documents_new RENAME TO documents"))
            
            # 重建索引
            print("   重建索引...")
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_documents_task_id ON documents(task_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_documents_external_id ON documents(external_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_documents_source_name ON documents(source_name)
            """))
            
            # 重建 document_summaries 外键关系
            print("   检查 document_summaries 表...")
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM document_summaries
            """))
            summary_count = result.scalar()
            print(f"   document_summaries 记录数: {summary_count}")
            
            print("\n✓ 迁移完成！")
            
        await engine.dispose()
        
        # 验证
        print("\n4. 验证迁移结果...")
        engine = create_async_engine(settings.database.url, echo=False)
        async with engine.connect() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='documents'
            """))
            row = result.fetchone()
            if row and 'UNIQUE (task_id, external_id, source_name)' in row[0]:
                print("   ✓ 新约束已生效")
            else:
                print("   ⚠ 请手动检查约束")
            
            # 检查数据
            result = await conn.execute(text("SELECT COUNT(*) FROM documents"))
            count = result.scalar()
            print(f"   ✓ documents 表记录数: {count}")
            
        await engine.dispose()
        
        print("\n" + "=" * 60)
        print(" 迁移成功！现在不同任务可以独立保存相同的文献了。")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n数据库已备份到: {backup_name}")
        print("如需恢复，请将备份文件复制回原位置")
        await engine.dispose()
        return False


async def check_task_isolation():
    """检查任务间文献隔离是否正常"""
    settings = get_settings()
    
    print("=" * 60)
    print(" 检查任务间文献隔离")
    print("=" * 60)
    
    engine = create_async_engine(settings.database.url, echo=False)
    
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            
            # 按任务统计
            print("\n1. 按任务统计文献数量:")
            result = await conn.execute(text("""
                SELECT 
                    t.id, t.name,
                    COUNT(d.id) as total,
                    SUM(CASE WHEN d.is_filtered_in = 1 THEN 1 ELSE 0 END) as filtered_in
                FROM tasks t
                LEFT JOIN documents d ON t.id = d.task_id
                GROUP BY t.id, t.name
                ORDER BY t.id
            """))
            rows = result.fetchall()
            
            print(f"   {'ID':<5} {'任务名称':<30} {'总数':<10} {'筛选通过':<10}")
            print("   " + "-" * 55)
            for row in rows:
                name = row[1][:28] if row[1] else 'N/A'
                print(f"   {row[0]:<5} {name:<30} {row[2]:<10} {row[3] or 0:<10}")
            
            # 检查重复
            print("\n2. 检查同一任务内是否有重复文献:")
            result = await conn.execute(text("""
                SELECT task_id, external_id, source_name, COUNT(*) as cnt
                FROM documents
                GROUP BY task_id, external_id, source_name
                HAVING COUNT(*) > 1
            """))
            rows = result.fetchall()
            
            if rows:
                print(f"   ✗ 发现 {len(rows)} 组重复文献！")
                for row in rows[:5]:
                    print(f"      task_id={row[0]}, external_id={row[1][:30]}, count={row[3]}")
            else:
                print("   ✓ 没有重复文献")
            
            # 检查约束
            print("\n3. 检查唯一约束:")
            result = await conn.execute(text("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='documents'
            """))
            row = result.fetchone()
            
            if row:
                if 'UNIQUE (task_id, external_id, source_name)' in row[0] or 'uq_task_document_source' in row[0]:
                    print("   ✓ 约束正确: (task_id, external_id, source_name)")
                elif 'UNIQUE (external_id, source_name)' in row[0] or 'uq_document_source' in row[0]:
                    print("   ✗ 约束是旧的: (external_id, source_name)")
                    print("   请运行: python manage_db.py migrate-constraint")
                else:
                    print("   ⚠ 无法确定约束类型，请手动检查")
            
        await engine.dispose()
        print("\n" + "=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        await engine.dispose()
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库管理工具")
    parser.add_argument(
        "action",
        choices=["check", "init", "backup", "migrate-constraint", "check-isolation"],
        help="操作: check(检查) | init(初始化) | backup(备份) | migrate-constraint(迁移约束) | check-isolation(检查隔离)"
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
        elif args.action == "migrate-constraint":
            result = asyncio.run(migrate_document_constraint())
        elif args.action == "check-isolation":
            result = asyncio.run(check_task_isolation())
        
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
