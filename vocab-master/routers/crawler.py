"""
单词爬虫 API 接口
提供从第三方词典网站抓取助记法和例句的功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db, close_db
from crawler import crawl_word_data

router = APIRouter(prefix="/api/crawler", tags=["单词爬虫"])


class CrawlRequest(BaseModel):
    word: str
    save_to_db: bool = True  # 是否保存到数据库


class CrawlResponse(BaseModel):
    success: bool
    word: str
    mnemonic: str = ""
    example_sentence: str = ""
    example_translation: str = ""
    message: str = ""


@router.post("/crawl", response_model=CrawlResponse, summary="爬取单词数据")
def crawl_word(request: CrawlRequest):
    """
    从第三方词典网站爬取单词的助记法和例句
    
    - 如果数据库中已有数据，可选择直接返回或重新爬取
    - 支持保存到数据库供后续使用
    """
    word = request.word.strip().lower()
    
    if not word:
        raise HTTPException(status_code=400, detail="单词不能为空")
    
    conn = get_db()
    try:
        # 检查数据库中是否已有该单词的数据
        existing = conn.execute(
            "SELECT id, mnemonic, example_sentence, example_translation FROM words WHERE LOWER(word) = ?",
            (word,),
        ).fetchone()
        
        # 如果已有数据且不强制重新爬取，直接返回
        if existing and not request.save_to_db:
            return CrawlResponse(
                success=True,
                word=word,
                mnemonic=existing["mnemonic"] or "",
                example_sentence=existing["example_sentence"] or "",
                example_translation=existing["example_translation"] or "",
                message="从数据库返回已有数据",
            )
        
        # 执行爬取
        crawl_result = crawl_word_data(word)
        
        if not crawl_result["success"]:
            return CrawlResponse(
                success=False,
                word=word,
                message="爬取失败，未找到相关数据",
            )
        
        # 如果指定保存到数据库且单词已存在，更新数据
        if request.save_to_db and existing:
            updates = []
            params = []
            
            if crawl_result["mnemonic"]:
                updates.append("mnemonic = ?")
                params.append(crawl_result["mnemonic"])
            
            if crawl_result["example_sentence"]:
                updates.append("example_sentence = ?")
                params.append(crawl_result["example_sentence"])
            
            if crawl_result["example_translation"]:
                updates.append("example_translation = ?")
                params.append(crawl_result["example_translation"])
            
            if updates:
                params.append(existing["id"])
                conn.execute(
                    f"UPDATE words SET {', '.join(updates)} WHERE id = ?",
                    params,
                )
                conn.commit()
        
        return CrawlResponse(
            success=True,
            word=word,
            mnemonic=crawl_result["mnemonic"],
            example_sentence=crawl_result["example_sentence"],
            example_translation=crawl_result["example_translation"],
            message="爬取成功" + ("并已保存到数据库" if request.save_to_db else ""),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}")
    finally:
        close_db(conn)


@router.get("/batch-crawl", summary="批量爬取单词数据")
def batch_crawl_words(limit: int = 10):
    """
    批量爬取当前词书中缺少助记法或例句的单词
    
    Args:
        limit: 每次处理的单词数量（默认10个）
        
    Returns:
        处理结果统计
    """
    conn = get_db()
    try:
        from routers.study import _get_setting
        
        book_id = _get_setting(conn, "current_book_id", "cet4")
        
        # 查找缺少助记法或例句的单词
        rows = conn.execute(
            """SELECT id, word FROM words 
               WHERE book_id = ? 
                 AND (mnemonic = '' OR mnemonic IS NULL 
                      OR example_sentence = '' OR example_sentence IS NULL)
               LIMIT ?""",
            (book_id, limit),
        ).fetchall()
        
        if not rows:
            return {
                "message": "所有单词数据完整",
                "processed": 0,
                "success": 0,
                "failed": 0,
            }
        
        processed = 0
        success = 0
        failed = 0
        results = []
        
        for row in rows:
            word_id = row["id"]
            word = row["word"]
            
            try:
                crawl_result = crawl_word_data(word)
                
                if crawl_result["success"]:
                    updates = []
                    params = []
                    
                    if crawl_result["mnemonic"]:
                        updates.append("mnemonic = ?")
                        params.append(crawl_result["mnemonic"])
                    
                    if crawl_result["example_sentence"]:
                        updates.append("example_sentence = ?")
                        params.append(crawl_result["example_sentence"])
                    
                    if crawl_result["example_translation"]:
                        updates.append("example_translation = ?")
                        params.append(crawl_result["example_translation"])
                    
                    if updates:
                        params.append(word_id)
                        conn.execute(
                            f"UPDATE words SET {', '.join(updates)} WHERE id = ?",
                            params,
                        )
                        success += 1
                    
                    results.append({
                        "word": word,
                        "status": "success",
                        "has_mnemonic": bool(crawl_result["mnemonic"]),
                        "has_example": bool(crawl_result["example_sentence"]),
                    })
                else:
                    failed += 1
                    results.append({
                        "word": word,
                        "status": "failed",
                    })
                
                processed += 1
                
            except Exception as e:
                failed += 1
                results.append({
                    "word": word,
                    "status": "error",
                    "error": str(e),
                })
        
        conn.commit()
        
        return {
            "message": f"批量爬取完成",
            "processed": processed,
            "success": success,
            "failed": failed,
            "results": results,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量爬取失败: {str(e)}")
    finally:
        close_db(conn)
