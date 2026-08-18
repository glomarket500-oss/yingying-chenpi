import opencc
import os
import re

BASE = r'C:\Users\a\Desktop\chenpi-website'
converter = opencc.OpenCC('s2hk')

# 需要转换的文件
files = [
    'index.html',
    'about.html',
    'articles.html',
    'article-20260817.html',
    'contact.html',
    'live.html',
    'videos.html',
    '404.html',
    'css/style.css',
]

def convert_file(filename):
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        print(f'  [SKIP] {filename} not found')
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 转换全部中文文本
    content = converter.convert(content)
    
    # 特殊处理：CSS 变量名、HTML 属性值里的英文不要变（opencc 不会变英文，但以防万一）
    # 确保 lang="zh-CN" 变为 lang="zh-HK"
    content = content.replace('lang="zh-CN"', 'lang="zh-HK"')
    content = content.replace("lang='zh-CN'", "lang='zh-HK'")
    
    # 确保 lang="zh-cn" 变为 lang="zh-HK"
    content = content.replace('lang="zh-cn"', 'lang="zh-HK"')
    
    if content == original:
        print(f'  [SKIP] {filename} (no changes)')
        return
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'  [DONE] {filename}')

if __name__ == '__main__':
    print('=== 簡體轉香港繁體 ===')
    for f in files:
        convert_file(f)
    print('\n全部完成！')
    input('按回車鍵退出...')
