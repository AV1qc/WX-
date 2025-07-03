# -*- coding: utf-8 -*-
import csv
import requests
from bs4 import BeautifulSoup
import re
import time
import json
import html # 用于解码HTML实体

def get_content_from_url(url):
    """
    访问给定的 URL，解析 HTML 并提取'文：'和'图：'之间的内容。

    :param url: 要抓取的网页链接
    :return: 提取到的文本内容，如果找不到或发生错误则返回相应的消息
    """
    try:
        # 发送 HTTP GET 请求，并设置超时时间
        # 添加 User-Agent 来模拟浏览器访问，避免被一些网站阻止
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=20)
        # 检查请求是否成功
        response.raise_for_status()

        # 设置正确的编码
        response.encoding = response.apparent_encoding

        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # 获取页面的所有文本内容，用空格作为分隔符以处理标签间的文本
        page_text = soup.get_text(separator=' ')

        # 使用正则表达式查找 '文：' 和 '图：' 之间的内容
        # re.DOTALL 标志让 '.' 可以匹配包括换行符在内的任何字符
        # (.*?) 是一个非贪婪匹配，它会匹配尽可能少的字符直到遇到 '图：'
        # \s* 用来匹配 '文：' 或 '图：' 周围可能存在的任意空白字符
        match = re.search(r'文\s*：(.*?)\s*图\s*：', page_text, re.DOTALL)

        if match:
            # group(1) 获取第一个捕获组的内容，即我们想要提取的文本
            # .strip() 用于移除内容开始和结尾的空白字符
            content = match.group(1).strip()
            # 将文本中连续的多个空白（包括空格、换行、制表符）替换为单个空格
            content = re.sub(r'\s+', ' ', content)
            return content if content else "内容为空"
        else:
            return "未找到'文：'和'图：'标记之间的内容"

    except requests.exceptions.RequestException as e:
        # 处理网络相关的错误 (如 DNS 错误, 连接超时等)
        print(f"抓取 URL '{url}' 时发生网络错误: {e}")
        return f"网络错误: {e}"
    except Exception as e:
        # 处理其他所有可能的错误
        print(f"处理 URL '{url}' 时发生未知错误: {e}")
        return f"未知错误: {e}"

def extract_read_nums_from_html(html_file_path):
    """
    从本地 HTML 文件中提取文章标题和对应的阅读数。
    该函数适用于从微信公众号“发表记录”页面导出的HTML文件。

    :param html_file_path: 发表记录页面的 HTML 文件路径
    :return: 包含文章标题和阅读数的字典 {title: read_num}
    """
    read_num_data = {}
    try:
        # 尝试以 UTF-8 编码打开文件
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        # 查找包含 publish_page 数据的 script 标签
        # 使用 'string' 代替 'text' 来避免 DeprecationWarning
        script_tag = soup.find('script', string=re.compile(r'publish_page\s*=\s*({.*});', re.DOTALL))

        if script_tag:
            script_text = script_tag.string
            # 使用正则表达式提取 publish_page 的 JSON 字符串
            match = re.search(r'publish_page\s*=\s*({.*?});', script_text, re.DOTALL)
            if match:
                json_str_raw = match.group(1)
                
                # 定义一个内部函数来处理 'publish_info' 字段的值
                def replace_publish_info_value(match_obj):
                    # match_obj.group(1) 是键的部分，例如 '"publish_info":'
                    # match_obj.group(2) 是值的部分，例如 '{&quot;type&quot;:9,...}'

                    raw_inner_json_str_value = match_obj.group(2)
                    
                    # 1. HTML 反转义内部 JSON 字符串，使其成为合法的 JSON 字符串
                    # 例如: '{&quot;type&quot;:9,...}' 变为 '{"type":9,...}'
                    valid_json_string = html.unescape(raw_inner_json_str_value)

                    # 2. 将这个合法的 JSON 字符串再次进行 JSON 转义
                    # 这样它就可以安全地作为字符串值嵌入到外层 JSON 中
                    # 例如: '{"type":9,...}' 变为 '{\\"type\\":9,...}'
                    # json.dumps 会为字符串添加额外的双引号，所以我们用 [1:-1] 去除
                    properly_escaped_inner_json_str = json.dumps(valid_json_string)[1:-1]
                    
                    # 返回重构的字符串，包括原始的键部分和正确转义后的值
                    return f'{match_obj.group(1)}{properly_escaped_inner_json_str}"'

                # 使用正则表达式和替换函数来修复 malformed 的 'publish_info' 字段
                # 这个正则表达式会匹配 'publish_info":"' 后面的内容，直到匹配到其字符串值的结束引号
                # (?:(?!"),.)*? 匹配任何字符，除非它是一个未转义的双引号（不包括转义后的双引号），这是为了避免提前终止字符串
                # 这种模式是为了处理 `"` 字符在 JSON 字符串值中没有被 `\` 转义的情况
                # 这里假设 `publish_info` 的值以 `"{` 开头，以 `}"` 结尾
                # 由于 `json_str_raw` 中 `&quot;` 存在，先不全局 `html.unescape`
                # 替换发生在 `json_str_raw` 上
                fixed_json_str = re.sub(r'("publish_info":")(.+?)"', replace_publish_info_value, json_str_raw)

                # 现在解析经过修复的 JSON 字符串
                publish_page_data = json.loads(fixed_json_str)

                # 遍历 publish_list，获取每条发表记录
                for publish_item in publish_page_data.get('publish_list', []):
                    # publish_info 字段本身是一个 JSON 字符串（现在已经正确转义）
                    publish_info_str = publish_item.get('publish_info')
                    if publish_info_str:
                        # 解析 publish_info 内部的 JSON 字符串
                        publish_info_decoded = json.loads(publish_info_str)
                        
                        # 遍历 appmsg_info 列表，获取每篇文章的信息
                        for appmsg_info in publish_info_decoded.get('appmsg_info', []):
                            title = appmsg_info.get('title')
                            read_num = appmsg_info.get('read_num')
                            if title and read_num is not None:
                                read_num_data[title] = read_num
        else:
            print("未在 HTML 中找到 'publish_page' 数据。请检查 '发表记录.txt' 文件是否正确。")
    except FileNotFoundError:
        print(f"错误：找不到发表记录文件 '{html_file_path}'。请检查文件名和路径是否正确。")
    except json.JSONDecodeError as e:
        print(f"解析 JSON 数据时发生错误: {e}")
        # 打印导致错误的 JSON 字符串片段，以便调试
        if 'fixed_json_str' in locals():
            print(f"错误发生在大致的 JSON 字符串片段 (尝试修复后): {fixed_json_str[max(0, e.pos-100):e.pos+100]}")
        else:
            print("无法确定 JSON 错误发生的位置。")
    except Exception as e:
        print(f"处理发表记录文件时发生未知错误: {e}")
    return read_num_data

def process_csv(input_file, output_file, url_column_index, publish_history_html_file, title_column_index):
    """
    处理 CSV 文件，从指定 URL 提取内容，并从发表记录 HTML 中提取阅读数，然后写入新文件。

    :param input_file: 输入的 CSV 文件路径
    :param output_file: 输出的 CSV 文件路径
    :param url_column_index: 包含 URL 的列的索引 (从 0 开始)
    :param publish_history_html_file: 发表记录页面的 HTML 文件路径
    :param title_column_index: CSV 中包含文章标题的列的索引 (从 0 开始)，用于匹配阅读数
    """
    print(f"开始处理文件: {input_file}")
    print(f"URL 所在列的索引: {url_column_index}")
    print(f"文章标题所在列的索引 (用于匹配阅读数): {title_column_index}")
    print(f"将从以下文件提取阅读数: {publish_history_html_file}")
    print(f"处理结果将保存到: {output_file}")

    # 提取阅读数数据
    title_to_read_num_map = extract_read_nums_from_html(publish_history_html_file)
    if not title_to_read_num_map:
        print("警告: 未能从发表记录文件中提取到阅读数数据，或数据为空。最终输出中阅读数可能显示 'N/A' 或 '未找到阅读数'。")

    try:
        with open(input_file, 'r', encoding='gbk') as infile, \
             open(output_file, 'w', newline='', encoding='utf-8-sig') as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # 读取并写入表头，并添加新的列名
            header = next(reader)
            new_header = header + ['通讯员', '阅读数']
            writer.writerow(new_header)

            # 逐行处理数据
            for i, row in enumerate(reader):
                current_row = list(row) # 创建行的副本，以便修改

                # --- 提取网页内容 (原有功能) ---
                extracted_content = "URL列为空或无效"
                if len(current_row) > url_column_index:
                    url = current_row[url_column_index].strip()
                    if url.startswith('http://') or url.startswith('https://'):
                        print(f"正在处理第 {i+2} 行, URL: {url}")
                        extracted_content = get_content_from_url(url)
                        time.sleep(1) # 暂停1秒，避免对服务器造成太大压力
                    else:
                        print(f"第 {i+2} 行的 '{url}' 不是一个有效的 URL，已跳过内容提取。")
                else:
                    print(f"第 {i+2} 行的列数不足，无法获取 URL，已跳过内容提取。")

                # --- 获取阅读数 ---
                read_num = "N/A" # 默认值
                if len(current_row) > title_column_index:
                    article_title = current_row[title_column_index].strip()
                    # 从预先提取的字典中查找阅读数，如果找不到则显示“未找到阅读数”
                    read_num = title_to_read_num_map.get(article_title, "未找到阅读数")
                else:
                    print(f"第 {i+2} 行的列数不足，无法获取文章标题，已跳过阅读数匹配。")

                # 将原始内容、提取的内容和阅读数一起写入新文件
                writer.writerow(current_row + [extracted_content, read_num])
        
        print(f"\n处理完成！结果已保存到 {output_file}")

    except FileNotFoundError:
        print(f"错误：找不到输入文件 '{input_file}'。请检查文件名和路径是否正确。")
    except Exception as e:
        print(f"处理文件时发生错误: {e}")

# --- 主程序 ---
if __name__ == '__main__':
    # --- 请在这里配置您的文件和列信息 ---

    # 1. 输入文件名 (您上传的 CSV 文件)
    # 请确保此文件与脚本在同一个文件夹下，或者提供完整路径
    INPUT_CSV_FILE = '1.csv' # <-- 请将此替换为您的实际 CSV 文件名 (例如 'your_data.csv')

    # 2. 输出文件名 (处理后的结果将保存在这里)
    OUTPUT_CSV_FILE = '输出结果_含阅读数.csv'

    # 3. URL 所在列的索引 (重要！)
    # 列的编号从 0 开始。例如，如果 URL 在第一列，索引就是 0；如果在第二列，就是 1，以此类推。
    # 您需要打开 CSV 文件确认一下链接具体在哪一列。
    URL_COLUMN_INDEX = 3  # <-- 假设链接在第5列 (索引为4)，请根据您的文件进行修改

    # 4. 发表记录页面的 HTML 文件路径 (重要！)
    # 这是您上传的 '发表记录.txt' 文件
    PUBLISH_HISTORY_HTML_FILE = '发表记录.txt' # <-- 请将此替换为您的实际 HTML 文件名

    # 5. CSV 中包含文章标题的列的索引 (重要！)
    # 用于从 '发表记录.txt' 中匹配阅读数。确保此列的标题与 HTML 中的标题一致。
    TITLE_COLUMN_INDEX = 2 # <-- 假设 CSV 中文章标题在第1列 (索引为0)，请根据您的文件进行修改

    # --- 配置结束 ---

    process_csv(INPUT_CSV_FILE, OUTPUT_CSV_FILE, URL_COLUMN_INDEX, PUBLISH_HISTORY_HTML_FILE, TITLE_COLUMN_INDEX)