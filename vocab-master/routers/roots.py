"""
词根词缀相关 API
"""
from fastapi import APIRouter, HTTPException
from database import get_db, close_db
from models import RootOut, RootWithWordsOut, WordOut

router = APIRouter(prefix="/api/roots", tags=["词根词缀"])


@router.get("", response_model=list[RootOut], summary="获取所有词根词缀列表")
def get_roots():
    """获取所有词根词缀，附带关联单词数量"""
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT wr.*, COUNT(w.id) as word_count
               FROM word_roots wr
               LEFT JOIN words w ON w.root_id = wr.id
               GROUP BY wr.id
               ORDER BY wr.root_text"""
        ).fetchall()
        return [RootOut(
            id=r["id"],
            root_text=r["root_text"],
            meaning=r["meaning"],
            description=r["description"],
            word_count=r["word_count"],
        ) for r in rows]
    finally:
        close_db(conn)


@router.get("/{root_id}/words", response_model=RootWithWordsOut, summary="获取同一词根下的所有派生词")
def get_root_words(root_id: int):
    """获取指定词根下的所有派生词"""
    conn = get_db()
    try:
        root = conn.execute(
            "SELECT * FROM word_roots WHERE id = ?", (root_id,)
        ).fetchone()
        if not root:
            raise HTTPException(status_code=404, detail="词根不存在")

        rows = conn.execute(
            "SELECT * FROM words WHERE root_id = ? ORDER BY sort_order",
            (root_id,),
        ).fetchall()

        root_out = RootOut(
            id=root["id"],
            root_text=root["root_text"],
            meaning=root["meaning"],
            description=root["description"],
            word_count=len(rows),
        )

        words = [WordOut(
            id=r["id"], book_id=r["book_id"], word=r["word"],
            phonetic=r["phonetic"], part_of_speech=r["part_of_speech"],
            definition_cn=r["definition_cn"], example_sentence=r["example_sentence"],
            example_translation=r["example_translation"],
            root_id=r["root_id"], high_freq_defs=r["high_freq_defs"],
            confusion_group=r["confusion_group"],
        ) for r in rows]

        return RootWithWordsOut(root=root_out, words=words)
    finally:
        close_db(conn)
