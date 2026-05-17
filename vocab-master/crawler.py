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
    【优化】增加了更稳健的 HTML 解析逻辑和错误日志
    """
    try:
        url = f"http://dict.cn/mini.php?q={word}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = "utf-8"
        
        if response.status_code != 200 or len(response.text) < 50:
            return {"success": False, "error": "请求失败或内容为空"}
        
        soup = BeautifulSoup(response.text, "lxml")
        body = soup.find("body")
        
        if not body:
            return {"success": False, "error": "未找到内容"}
        
        # 尝试提取所有段落或行，比纯文本分割更准确
        lines = [line.get_text(strip=True) for line in body.find_all(['p', 'div', 'li']) if line.get_text(strip=True)]
        if not lines:
            lines = body.get_text(separator="\n", strip=True).split("\n")
            lines = [l.strip() for l in lines if l.strip()]
        
        example_sentence = ""
        example_translation = ""
        
        # 【优化】更精准的启发式提取
        for i, line in enumerate(lines):
            # 寻找包含目标单词且长度适中的英文行
            if len(line) > 15 and word.lower() in line.lower() and any(c.isalpha() for c in line):
                # 简单过滤掉纯释义行（通常很短）
                if len(line) > 20:
                    example_sentence = line
                    # 检查下一行是否为中文翻译
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        if next_line and all("\u4e00" <= c <= "\u9fff" or c in '，。！？' for c in next_line):
                            example_translation = next_line
                    break
        
        return {
            "success": True,
            "example_sentence": example_sentence,
            "example_translation": example_translation,
            "definition": lines[0] if lines else "",
        }
        
    except Exception as e:
        print(f"[Crawler Error] dict.cn failed for '{word}': {e}")
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
    【优化】增加了数据有效性校验和多源 fallback 逻辑
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
        best_mnemonic = mnemonic_result["mnemonics"][0]
        result["mnemonic"] = best_mnemonic["text"]
    
    # 2. 从海词词典获取例句
    dict_cn_result = crawl_dict_cn(word)
    result["sources"]["dict_cn"] = dict_cn_result
    
    if dict_cn_result["success"]:
        ex_sent = dict_cn_result.get("example_sentence", "")
        # 【优化】校验：例句必须包含单词本身，且长度大于10个字符
        if ex_sent and len(ex_sent) > 10 and word.lower() in ex_sent.lower():
            result["example_sentence"] = ex_sent
            result["example_translation"] = dict_cn_result.get("example_translation", "")
    
    # 【优化】Fallback：如果没抓到助记法，尝试用词根拆解代替
    if not result["mnemonic"]:
        wordsand_result = crawl_wordsand(word)
        result["sources"]["wordsand"] = wordsand_result
        if wordsand_result["success"] and wordsand_result["root_analysis"]:
            result["mnemonic"] = f"[词根拆解] {wordsand_result['root_analysis']}"
    
    # 判断是否成功获取到至少一项有效数据
    if result["mnemonic"] or result["example_sentence"]:
        result["success"] = True
    
    return result
