"""
单词爬虫模块 - 从第三方词典网站抓取助记法和例句
支持：海词词典、词根词缀词典、助记词典
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional


def crawl_dict_cn(word: str) -> dict:
    """
    从海词词典 (dict.cn) 抓取简短释义和例句
    
    Args:
        word: 要查询的单词
        
    Returns:
        {
            "success": bool,
            "example_sentence": str,
            "example_translation": str,
            "definition": str
        }
    """
    try:
        url = f"http://dict.cn/mini.php?q={word}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = "utf-8"
        
        if response.status_code != 200:
            return {"success": False, "error": "请求失败"}
        
        soup = BeautifulSoup(response.text, "html.parser")
        body = soup.find("body")
        
        if not body:
            return {"success": False, "error": "未找到内容"}
        
        # 清理HTML标签，获取纯文本
        text = body.get_text(separator="\n", strip=True)
        
        # 尝试提取例句（通常包含英文句子和中文翻译）
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        example_sentence = ""
        example_translation = ""
        definition = ""
        
        # 简单启发式提取：寻找包含句号或逗号的较长行作为例句
        for i, line in enumerate(lines):
            if len(line) > 20 and ("." in line or "," in line):
                # 可能是英文例句
                example_sentence = line
                # 下一行可能是中文翻译
                if i + 1 < len(lines) and any("\u4e00" <= c <= "\u9fff" for c in lines[i + 1]):
                    example_translation = lines[i + 1]
                break
        
        # 第一行通常是释义
        if lines:
            definition = lines[0]
        
        return {
            "success": True,
            "example_sentence": example_sentence,
            "example_translation": example_translation,
            "definition": definition,
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def crawl_wordsand(word: str) -> dict:
    """
    从词根词缀词典 (wordsand.cn) 抓取词根词缀拆解信息
    
    Args:
        word: 要查询的单词
        
    Returns:
        {
            "success": bool,
            "root_analysis": str
        }
    """
    try:
        url = f"http://www.wordsand.cn/lookup.asp?word={word}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = "gbk"  # 该网站使用GBK编码
        
        if response.status_code != 200:
            return {"success": False, "error": "请求失败"}
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 尝试查找表格中的词根分析内容
        tables = soup.find_all("table")
        root_analysis = ""
        
        for table in tables:
            cells = table.find_all("td")
            for cell in cells:
                text = cell.get_text(strip=True)
                if text and len(text) > 10:
                    # 使用正则提取可能的词根分析
                    if re.search(r"[a-z]+=[a-z]+", text, re.IGNORECASE):
                        root_analysis = text
                        break
        
        return {
            "success": True,
            "root_analysis": root_analysis,
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def crawl_mnemonic_dictionary(word: str) -> dict:
    """
    从助记词典 (mnemonicdictionary.com) 抓取记忆技巧
    
    Args:
        word: 要查询的单词
        
    Returns:
        {
            "success": bool,
            "mnemonics": list[dict]  # [{text, up, down}]
        }
    """
    try:
        url = f"https://mnemonicdictionary.com/?word={word}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = "utf-8"
        
        if response.status_code != 200:
            return {"success": False, "error": "请求失败"}
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 查找所有助记卡片
        cards = soup.find_all("div", class_="card mnemonic-card")
        
        mnemonics = []
        for card in cards:
            # 提取助记文本
            text_elem = card.find("div", class_="mnemonic-text")
            if not text_elem:
                continue
            
            text = text_elem.get_text(strip=True)
            if not text:
                continue
            
            # 提取点赞数和点踩数
            up = 0
            down = 0
            
            up_elem = card.find("span", class_="upvote-count")
            if up_elem:
                try:
                    up = int(up_elem.get_text(strip=True))
                except:
                    pass
            
            down_elem = card.find("span", class_="downvote-count")
            if down_elem:
                try:
                    down = int(down_elem.get_text(strip=True))
                except:
                    pass
            
            mnemonics.append({
                "text": text,
                "up": up,
                "down": down,
            })
        
        # 按点赞数排序，返回最热门的
        mnemonics.sort(key=lambda x: x["up"] - x["down"], reverse=True)
        
        return {
            "success": True,
            "mnemonics": mnemonics[:5],  # 最多返回5条
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def crawl_word_data(word: str) -> dict:
    """
    综合爬取单词的所有数据（助记法、例句等）
    
    Args:
        word: 要查询的单词
        
    Returns:
        {
            "success": bool,
            "mnemonic": str,           # 最佳助记法
            "example_sentence": str,   # 例句
            "example_translation": str,# 例句翻译
            "sources": dict            # 各来源的原始数据
        }
    """
    result = {
        "success": False,
        "mnemonic": "",
        "example_sentence": "",
        "example_translation": "",
        "sources": {},
    }
    
    # 1. 从助记词典获取助记法
    mnemonic_result = crawl_mnemonic_dictionary(word)
    result["sources"]["mnemonic_dictionary"] = mnemonic_result
    
    if mnemonic_result["success"] and mnemonic_result["mnemonics"]:
        # 选择点赞最多的助记法
        best_mnemonic = mnemonic_result["mnemonics"][0]
        result["mnemonic"] = best_mnemonic["text"]
    
    # 2. 从海词词典获取例句
    dict_cn_result = crawl_dict_cn(word)
    result["sources"]["dict_cn"] = dict_cn_result
    
    if dict_cn_result["success"]:
        if dict_cn_result["example_sentence"]:
            result["example_sentence"] = dict_cn_result["example_sentence"]
        if dict_cn_result["example_translation"]:
            result["example_translation"] = dict_cn_result["example_translation"]
    
    # 判断是否成功获取到至少一项数据
    if result["mnemonic"] or result["example_sentence"]:
        result["success"] = True
    
    return result
