from flask import Flask, render_template, request, jsonify
import random
import requests
import os
import json
from datetime import datetime

app = Flask(__name__)
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')

def get_today_quote():
    """从 quotes.json 读取今日语录"""
    try:
        # 读取 JSON 文件（确保和 app.py 同级目录）
        with open('quotes.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 支持三种常见 JSON 格式，自动识别
        quotes_list = []
        
        # 格式1：直接是数组 [{"book": "...", "content": "..."}]
        if isinstance(data, list):
            quotes_list = data
        
        # 格式2：{"quotes": [...]} 包裹
        elif isinstance(data, dict) and 'quotes' in data:
            quotes_list = data['quotes']
        
        # 格式3：{"书名": ["语录1", "语录2"], ...}
        elif isinstance(data, dict):
            for book, contents in data.items():
                if isinstance(contents, list):
                    for content in contents:
                        quotes_list.append({"book": f"《{book}》", "content": content})
                else:
                    quotes_list.append({"book": f"《{book}》", "content": str(contents)})
        
        if not quotes_list:
            return {"book": "系统", "content": "语录库为空，请检查 quotes.json"}
        
        # 用日期做种子，确保同一天内容一致
        today = datetime.now().strftime("%Y%m%d")
        random.seed(int(today))
        selected = random.choice(quotes_list)
        random.seed()
        
        # 统一返回格式
        book_name = selected.get("book", selected.get("source", "经典书籍"))
        content = selected.get("content", selected.get("quote", selected.get("text", "今日无语录")))
        
        return {
            "book": book_name,
            "content": content
        }
        
    except FileNotFoundError:
        return {"book": "错误", "content": "找不到 quotes.json，请确认文件已复制到 my_bot 文件夹"}
    except json.JSONDecodeError:
        return {"book": "错误", "content": "quotes.json 格式错误，请检查 JSON 语法是否正确"}
    except Exception as e:
        return {"book": "错误", "content": f"读取失败：{str(e)}"}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/today')
def today_quote():
    """获取今日语录并生成解读"""
    quote = get_today_quote()
    
    # 如果有错误，直接返回错误信息
    if quote["book"] == "错误":
        return jsonify({
            "date": datetime.now().strftime("%Y年%m月%d日"),
            "book": quote["book"],
            "quote": quote["content"],
            "interpretation": "请检查配置文件"
        })
    
    # 用 DeepSeek 生成解读（失败时不影响主功能）
    interpretation = "愿你今天充满能量。"
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"这句话来自{quote['book']}：{quote['content']}。请用温暖简短的一句话（20字以内）鼓励一下听者，像朋友早上打招呼一样。"
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 60
        }
        
        r = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers, json=data, timeout=10
        )
        
        result = r.json()
        if 'choices' in result and len(result['choices']) > 0:
            interpretation = result['choices'][0]['message']['content']
        
    except:
        interpretation = "今日份思考，愿你拥有美好的一天。"

    return jsonify({
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "book": quote['book'],
        "quote": quote['content'],
        "interpretation": interpretation
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)