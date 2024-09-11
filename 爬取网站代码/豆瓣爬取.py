import requests
from pyquery import PyQuery as pq
import re
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

def doulist_crawler(url):
    '''
    爬取豆瓣电影列表页面，并提取列出的电影的详细信息。
    参数:
        url (str): 要爬取的豆瓣电影列表页面的URL。
    返回:
        list: 包含每部电影详细信息的字典组成的列表。
    '''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 如果请求失败，抛出异常
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return []  # 返回空列表表示失败

    if response.status_code == 200:
        doc = pq(response.text)
        doulist_item_doc = doc(".doulist-item")
        doulist = []
        for item in doulist_item_doc.items():
            item_dict = {}
            # 初始化变量
            director = None
            starring = None
            genre = None
            region = None
            year = None
            detail_url = item(".title a").attr("href")
            title = item(".title a").text()
            rating_nums = item(".rating_nums").text()  # 获取评分
            poster_url = item(".post img").attr("src")  # 获取海报链接

            # 尝试提取评分数量
            rating_count_text = item('.rating span:contains("人评价")').text()
            if rating_count_text:
                match = re.search(r'\d+', rating_count_text)
                rating_count = int(match.group(0)) if match else None
            else:
                rating_count = None

            lines = item('div.abstract').text().split('\n')
            for line in lines:
                if '导演' in line:
                    director = line.split('导演:')[-1].strip()
                elif '主演' in line:
                    starring = line.split('主演:')[-1].strip()
                elif '类型' in line:
                    genre = line.split('类型:')[-1].strip()
                elif '制片国家/地区' in line:
                    region = line.split('制片国家/地区:')[-1].strip()
                elif '年份' in line:
                    year = line.split('年份:')[-1].strip()

            item_dict['director'] = director
            item_dict['starring'] = starring
            item_dict['genre'] = genre
            item_dict['region'] = region
            item_dict['year'] = year
            item_dict['detail_url'] = detail_url
            item_dict['title'] = title
            item_dict['rating'] = rating_nums  # 添加评分
            item_dict['rating_count'] = rating_count
            item_dict['poster_url'] = poster_url  # 添加海报链接

            # 只保留所需字段
            if all(v is not None for v in [director, starring, genre, region, year, detail_url, title, rating_nums, rating_count, poster_url]):
                doulist.append(item_dict)

        return doulist  # 返回电影列表
    else:
        print(f"请求失败，状态码：{response.status_code}")
        return []  # 如果请求失败，返回空列表


def save_to_csv(data, filename):
    '''
    将爬取的数据保存到 CSV 文件中。
    参数:
        data (list): 包含电影详细信息的字典列表。
        filename (str): 要保存的 CSV 文件名。
    '''
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"数据已保存到 {filename}")

def fetch_all_movies(urls, max_workers=5):
    '''
    使用多线程爬取所有电影信息
    参数:
        urls (list): 电影列表页面的 URL 列表。
        max_workers (int): 最大线程数。
    返回:
        list: 包含所有电影详细信息的字典列表。
    '''
    all_movies = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(doulist_crawler, url): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                movies = future.result()
                if movies:
                    all_movies.extend(movies)
                else:
                    print(f"未能从 {url} 获取数据，跳过该 URL。")
            except Exception as e:
                print(f"爬取 {url} 时发生错误: {e}")
    return all_movies

if __name__ == "__main__":
    base_url = 'https://www.douban.com/doulist/'
    ids = range(50000, 1000000)  # 调整范围以避免大量请求

    # 生成完整的 URL 列表，将 id 转换为字符串
    urls = [base_url + str(id) + '/' for id in ids]

    # 使用多线程爬取所有数据
    all_movies = fetch_all_movies(urls, max_workers=10)

    # 保存所有数据到 CSV 文件
    save_to_csv(all_movies, 'douban_movies.csv')
