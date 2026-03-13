#!/usr/bin/env python3
"""
查询中证红利指数成分股月度表现
使用准确的成分股列表，计算上月收盘到月末收盘的涨跌幅
"""

import json
import subprocess
import sys
import os
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    print("正在安装 pandas...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pandas", "openpyxl", "-q"], check=True)
    import pandas as pd

def run_python_code(code):
    """运行Python代码并返回结果"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120
    )
    return result.stdout, result.stderr

def load_component_stocks(excel_path):
    """从Excel文件加载中证红利成分股"""
    try:
        df = pd.read_excel(excel_path)
        code_col = [c for c in df.columns if 'Constituent Code' in c][0]
        name_col = [c for c in df.columns if 'Constituent Name' in c][0]
        
        stocks = []
        for _, row in df.iterrows():
            code = str(row[code_col]).zfill(6)
            name = row[name_col]
            stocks.append((code, name))
        return stocks
    except Exception as e:
        print(f"加载成分股失败: {e}", file=sys.stderr)
        return []

def calculate_month_change(code, year, month):
    """计算单只股票某月份的涨跌幅
    月涨跌幅 = (月末收盘价 - 上月最后一个交易日收盘价) / 上月最后一个交易日收盘价 * 100%
    """
    # 确定市场前缀
    if code.startswith("6") or code.startswith("9"):
        market = "sh"
    else:
        market = "sz"
    
    # 计算上月末日期
    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1
    
    code_py = f"""
import requests
import json

symbol = "{market}{code}"
url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
params = {{
    "symbol": symbol,
    "scale": "240",
    "ma": "no",
    "datalen": "1000"  
}}

try:
    r = requests.get(url, params=params, timeout=15)
    data = r.text
    klines = json.loads(data)
    
    prev_close = None  # 上月最后一个交易日收盘价
    month_end_close = None  # 当月最后一个交易日收盘价
    
    for k in klines:
        day = k.get("day", "")
        
        # 找上月最后一个交易日
        if day.startswith("{prev_year}-{prev_month:02d}"):
            prev_close = float(k.get("close", 0))
        
        # 找当月最后一个交易日
        if day.startswith("{year}-{month:02d}"):
            month_end_close = float(k.get("close", 0))
    
    if prev_close and month_end_close and prev_close > 0:
        change = (month_end_close - prev_close) / prev_close * 100
        print(f"{{prev_close}}|{{month_end_close}}|{{change:.2f}}")
    else:
        print("NO_DATA")
except Exception as e:
    print(f"Error: {{e}}")
"""
    stdout, stderr = run_python_code(code_py)
    
    try:
        result = stdout.strip()
        if result == "NO_DATA" or not result or result.startswith("Error:"):
            return None, None, None
        parts = result.split("|")
        if len(parts) == 3:
            return float(parts[0]), float(parts[1]), float(parts[2])
    except:
        pass
    return None, None, None

def main():
    if len(sys.argv) < 2:
        print("用法: python3 script.py <年份-月份>")
        print("示例: python3 script.py 2026-02")
        sys.exit(1)
    
    year_month = sys.argv[1]
    try:
        year, month = map(int, year_month.split("-"))
    except:
        print("格式错误，请使用 YYYY-MM 格式", file=sys.stderr)
        sys.exit(1)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(script_dir, "000922cons.xls")
    
    print(f"正在查询 {year}年{month:02d}月 中证红利成分股表现...")
    
    stocks = load_component_stocks(excel_path)
    if not stocks:
        print("无法获取成分股列表", file=sys.stderr)
        sys.exit(1)
    
    print(f"获取到 {len(stocks)} 只成分股\n")
    
    results = []
    for i, (code, name) in enumerate(stocks):
        prev_close, end_price, change = calculate_month_change(code, year, month)
        if change is not None:
            results.append({
                "code": code,
                "name": name,
                "prev_close": prev_close,
                "end_price": end_price,
                "change": change
            })
        
        if (i + 1) % 20 == 0:
            print(f"已处理 {i+1}/{len(stocks)} 只股票...")
    
    if not results:
        print("无法获取任何股票数据", file=sys.stderr)
        sys.exit(1)
    
    results.sort(key=lambda x: x["change"])
    
    avg_change = sum(r["change"] for r in results) / len(results)
    
    print(f"\n## {year}年{month:02d}月 中证红利成分股表现\n")
    print(f"**计算方式**: 上月末收盘价 → 月末收盘价\n")
    print("| 排名 | 代码 | 名称 | 月涨跌幅 |")
    print("|------|------|------|----------|")
    
    for i, r in enumerate(results[:10], 1):
        change_str = f"{r['change']:+.2f}%"
        print(f"| {i} | {r['code']} | {r['name']} | {change_str} |")
    
    print(f"\n**共计 {len(results)} 只成分股，平均涨跌幅: {avg_change:+.2f}%**")

if __name__ == "__main__":
    main()
