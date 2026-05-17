"""
生成演示数据 - 展示完整的艾宾浩斯复习计划
包括：不同阶段的单词、多种复习日期分布
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocab_master.db")

def generate_demo_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    print("🔄 正在清空旧数据...")
    
    try:
        # 清空现有数据
        conn.execute("DELETE FROM word_progress")
        conn.execute("DELETE FROM study_records")
        conn.execute("DELETE FROM checkins")
        conn.commit()
        print("✓ 已清空旧数据")
        
        # 获取当前词书的所有单词
        words = conn.execute("""
            SELECT w.id, w.word, wb.id as book_id 
            FROM words w 
            JOIN word_books wb ON w.book_id = wb.id 
            WHERE wb.id = 'cet4'
            ORDER BY w.sort_order
            LIMIT 50
        """).fetchall()
        
        if not words:
            print("❌ 未找到 CET-4 词书的单词，请先导入词书")
            return
        
        print(f"✓ 找到 {len(words)} 个单词")
        
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")
        
        # 新的艾宾浩斯间隔（长期记忆法）
        intervals = [1, 2, 4, 7, 15, 30]  # 天数
        
        print("\n📊 正在生成学习进度数据...")
        
        for i, word in enumerate(words):
            word_id = word["id"]
            
            # 模拟不同的学习阶段
            if i < 10:
                # 前10个单词：已完成第1轮，处于第2轮复习的不同阶段
                stage = 2
                review_step = (i % 6) + 1  # 1-6次复习
                days_ago = intervals[review_step - 1]
                last_reviewed = today - timedelta(days=days_ago)
                next_review = last_reviewed + timedelta(days=intervals[min(review_step, len(intervals)-1)])
                
                status = "learning"
                ease_factor = 2.5
                repetitions = review_step
                interval = intervals[min(review_step - 1, len(intervals)-1)]
                stage_2_pass_count = review_step  # 假设都通过了
                history = "1" * review_step  # 全部记得
                
            elif i < 20:
                # 10-20号单词：刚学完第1轮，等待第1次复习
                stage = 2
                review_step = 0
                last_reviewed = today - timedelta(hours=2)
                next_review = today + timedelta(days=1)  # 明天复习
                
                status = "learning"
                ease_factor = 2.5
                repetitions = 0
                interval = 0
                stage_2_pass_count = 0
                history = "1"
                
            elif i < 30:
                # 20-30号单词：进入第3轮（输出验证）
                stage = 3
                review_step = 6  # 已完成6次间隔复习
                last_reviewed = today - timedelta(days=30)
                next_review = today + timedelta(days=2)  # 后天验证
                
                status = "familiar"
                ease_factor = 2.8
                repetitions = 6
                interval = 30
                stage_2_pass_count = 6
                stage_3_attempts = 0
                stage_3_passed = 0
                history = "1" * 6
                
            elif i < 40:
                # 30-40号单词：已掌握
                stage = 3
                review_step = 6
                last_reviewed = today - timedelta(days=45)
                next_review = today + timedelta(days=60)  # 2个月后
                
                status = "mastered"
                ease_factor = 3.0
                repetitions = 8
                interval = 60
                stage_2_pass_count = 6
                stage_3_attempts = 1
                stage_3_passed = 1
                history = "1" * 8
                
            else:
                # 40-50号单词：还未学习
                stage = 1
                review_step = 0
                last_reviewed = None
                next_review = None
                
                status = "new"
                ease_factor = 2.5
                repetitions = 0
                interval = 0
                stage_2_pass_count = 0
                history = ""
            
            # 插入 word_progress
            learn_date = (last_reviewed - timedelta(days=1)).strftime("%Y-%m-%d") if last_reviewed else None
            last_reviewed_str = last_reviewed.isoformat() if last_reviewed else None
            next_review_str = next_review.strftime("%Y-%m-%d") if next_review else None
            
            conn.execute("""
                INSERT INTO word_progress 
                (word_id, status, ease_factor, interval, repetitions, 
                 next_review_date, last_reviewed_at, learn_date, 
                 stage, review_step, stage_2_pass_count, 
                 stage_3_attempts, stage_3_passed, history)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                word_id, status, ease_factor, interval, repetitions,
                next_review_str, last_reviewed_str, learn_date,
                stage, review_step, stage_2_pass_count,
                stage_3_attempts if stage == 3 else 0,
                stage_3_passed if stage == 3 else 0,
                history
            ))
        
        print("✓ 已生成单词进度数据")
        
        # 生成打卡记录（过去30天）
        print("\n📅 正在生成打卡记录...")
        for d in range(30):
            date = today - timedelta(days=d)
            date_str = date.strftime("%Y-%m-%d")
            
            # 随机生成学习/复习数量
            if d == 0:
                words_learned = 10
                words_reviewed = 5
            elif d < 7:
                words_learned = 15
                words_reviewed = 8
            else:
                words_learned = 12
                words_reviewed = 10
            
            conn.execute("""
                INSERT OR REPLACE INTO checkins 
                (checkin_date, words_learned, words_reviewed, checked)
                VALUES (?, ?, ?, 1)
            """, (date_str, words_learned, words_reviewed))
        
        print("✓ 已生成30天打卡记录")
        
        # 生成学习记录
        print("\n📝 正在生成学习记录...")
        for word in words[:30]:  # 前30个单词有学习记录
            word_id = word["id"]
            # 模拟多次学习/复习记录
            for r in range(3):
                record_date = today - timedelta(days=r*2)
                conn.execute("""
                    INSERT INTO study_records (word_id, action, rating, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    word_id,
                    "study" if r == 0 else "review",
                    5,  # 高质量
                    record_date.isoformat()
                ))
        
        print("✓ 已生成学习记录")
        
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ 演示数据生成完成！")
        print("="*60)
        print("\n数据概览：")
        print(f"  • 单词总数：{len(words)}")
        print(f"  • 未学习（第1轮）：10个")
        print(f"  • 间隔复习中（第2轮）：20个")
        print(f"  • 输出验证中（第3轮）：10个")
        print(f"  • 已掌握：10个")
        print(f"\n复习计划分布（使用新间隔 1,2,4,7,15,30天）：")
        
        # 统计未来30天的复习计划
        future_dates = conn.execute("""
            SELECT next_review_date, COUNT(*) as cnt
            FROM word_progress
            WHERE next_review_date IS NOT NULL
              AND next_review_date <= date('now', '+30 days')
            GROUP BY next_review_date
            ORDER BY next_review_date
        """).fetchall()
        
        for row in future_dates:
            print(f"  {row['next_review_date']}: {row['cnt']} 个单词待复习")
        
        print("\n💡 现在打开日历，可以看到丰富的复习计划分布！")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    print("⚠️  警告：此操作将清空所有现有学习数据并生成演示数据！")
    confirm = input("确定要继续吗？输入 YES 确认: ")
    if confirm == "YES":
        generate_demo_data()
    else:
        print("操作已取消")
