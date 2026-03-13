#!/usr/bin/env python3
"""
股票组合回测
计算一段时间内等权组合的总收益率
"""

import subprocess
import sys
import os
import json

try:
    import pandas as pd
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "pandas", "openpyxl", "-q"], check=True)
    import pandas as pd

def run_python_code(code):
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120
    )
    return result.stdout, result.stderr

def get_stock_name(code):
    """获取股票名称"""
    if code.startswith("6") or code.startswith("9"):
        market = "sh"
    else:
        market = "sz"
    
    code_py = f"""
import requests
import re

url = "https://hq.sinajs.cn/list={market}{code}"
headers = {{"Referer": "https://finance.sina.com.cn"}}

try:
    r = requests.get(url, headers=headers, timeout=10)
    content = r.text
    match = re.search(r'="([^"]+)"', content)
    if match:
        parts = match.group(1).split(',')
        if len(parts) > 0:
            print(parts[0])
    else:
        print("{code}")
except:
    print("{code}")
"""
    stdout, _ = run_python_code(code_py)
    return stdout.strip() if stdout.strip() else code

def get_prices_in_range(code, start_date, end_date):
    """获取指定日期范围内的所有交易日数据"""
    if code.startswith("6") or code.startswith("9"):
        market = "sh"
    else:
        market = "sz"
    
    code_py = f"""
import requests
import json

symbol = "{market}{code}"
url = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
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
    
    result = []
    for k in klines:
        day = k.get("day", "")
        if "{start_date}" <= day <= "{end_date}":
            result.append(day + "|" + k.get("open", "") + "|" + k.get("close", ""))
    
    print("|||".join(result))
except Exception as e:
    print("Error")
"""
    stdout, _ = run_python_code(code_py)
    result = stdout.strip()
    
    if result and result != "Error":
        prices = []
        for item in result.split("|||"):
            parts = item.split("|")
            if len(parts) >= 3:
                try:
                    prices.append({
                        "date": parts[0],
                        "open": float(parts[1]),
                        "close": float(parts[2])
                    })
                except:
                    pass
        return prices
    return []

def main():
    if len(sys.argv) < 4:
        print("用法: python3 script.py <股票代码列表> <开始日期> <结束日期>")
        print("示例: python3 script.py 600737,601963 2026-03-02 2026-03-13")
        sys.exit(1)
    
    stocks_input = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    
    codes = [c.strip() for c in stocks_input.split(",")]
    
    print(f"回测期间: {start_date} → {end_date}")
    print(f"股票数量: {len(codes)} 只（等权配置）\n")
    
    results = []
    for code in codes:
        # 获取股票名称
        name = get_stock_name(code)
        
        # 获取价格数据
        prices = get_prices_in_range(code, start_date, end_date)
        
        if prices and len(prices) >= 2:
            start_info = prices[0]
            start_price = start_info["close"]
            start_date_actual = start_info["date"]
            
            end_info = prices[-1]
            end_price = end_info["close"]
            end_date_actual = end_info["date"]
            
            change = (end_price - start_price) / start_price * 100
            results.append({
                "code": code,
                "name": name,
                "start_date": start_date_actual,
                "end_date": end_date_actual,
                "start_price": start_price,
                "end_price": end_price,
                "change": change
            })
            print(f"{code} {name}: {start_date_actual} 收盘 {start_price:.2f} → {end_date_actual} 收盘 {end_price:.2f}  {change:+.2f}%")
        else:
            print(f"{code}: 无法获取价格数据")
    
    if not results:
        print("\n无法获取任何股票数据")
        sys.exit(1)
    
    avg_change = sum(r["change"] for r in results) / len(results)
    
    print(f"\n{'='*60}")
    print(f"回测结果")
    print(f"{'='*60}")
    print(f"回测期间: {start_date} → {end_date}")
    print(f"股票数量: {len(results)} 只")
    print(f"等权配置: 每只股票 {(100/len(results)):.1f}%")
    print(f"\n| 代码 | 名称 | 涨跌幅 |")
    print(f"|------|------|--------|")
    for r in results:
        print(f"| {r['code']} | {r['name']} | {r['change']:+.2f}% |")
    print(f"\n**组合总收益率: {avg_change:+.2f}%**")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
