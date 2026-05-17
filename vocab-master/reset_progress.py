"""
重置所有单词的学习进度，应用新的艾宾浩斯间隔
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocab_master.db")

def reset_progress():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 确认操作
    print("⚠️  警告：此操作将清空所有单词的学习进度！")
    print("这将删除：")
    print("  - 所有单词的学习状态")
    print("  - 所有复习记录")
    print("  - 所有打卡记录")
    print("  - 所有学习历史")
    print()
    
    confirm = input("确定要继续吗？输入 YES 确认: ")
    if confirm != "YES":
        print("操作已取消")
        return
    
    try:
        # 清空 word_progress 表
        conn.execute("DELETE FROM word_progress")
        print("✓ 已清空单词进度")
        
        # 清空 study_records 表
        conn.execute("DELETE FROM study_records")
        print("✓ 已清空学习记录")
        
        # 清空 checkins 表
        conn.execute("DELETE FROM checkins")
        print("✓ 已清空打卡记录")
        
        conn.commit()
        print("\n✅ 重置完成！现在可以重新学习单词，将使用新的长期记忆法间隔。")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 错误：{e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_progress()
