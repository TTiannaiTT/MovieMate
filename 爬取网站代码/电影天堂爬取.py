import requests
from lxml import etree
import time
from bs4 import BeautifulSoup
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DOMAIN = 'http://www.dytt8.net'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}


def get_detail_urls(url):
    response = requests.get(url, headers=HEADERS)
    text = response.content.decode('gbk')
    html_element = etree.HTML(text)
    detail_urls = html_element.xpath('//table[@class="tbspan"]//a/@href')
    detail_urls_new = detail_urls
    for index, detail_url in enumerate(detail_urls_new):
        if detail_url == '/html/gndy/jddy/index.html':
            detail_urls.remove(detail_url)
    # print(detail_urls)
    # print(BASE_DOMAIN + detail_url)
    detail_urls = map(lambda x: BASE_DOMAIN + x, detail_urls)
    return detail_urls
#用于获取电影详情页的url


def parse_detail_urls(detail_url):
    response = requests.get(detail_url, headers=HEADERS)
    text = response.content.decode('gbk')
    if not text:
        print(f'No content returned from {detail_url}')
        return
    html_element = etree.HTML(text)
    if html_element is None:
        print(f'Failed to parse HTML from {detail_url}')
        return

    title = html_element.xpath('//div[@class="title_all"]//font[@color="#07519a"]/text()')[0]
    # print(title)
    zoom_element = html_element.xpath('//div[@id="Zoom"]')[0]

    imgs = zoom_element.xpath('.//img/@src')
    # print(imgs)
    cover = imgs[0]
    # print(cover)
    movie = {
        'title': title,
        'cover': cover,
    }
    year, country, type, rating, duration, director, actors, cover, screen_shot = '', '', '', '', '', '', '', '', ''

    def parse_info(info, rule):
        return info.replace(rule, '').strip()

    infos = zoom_element.xpath('.//text()')
    for index, info in enumerate(infos):
        if info.startswith('◎年　　代'):
            info = parse_info(info, '◎年　　代')
            movie['year'] = info
        elif info.startswith('◎产　　地'):
            info = parse_info(info, '◎产　　地')
            movie['country'] = info
        elif info.startswith('◎类　　别'):
            info = parse_info(info, '◎类　　别')
            movie['category'] = info
        elif info.startswith('◎IMDb评分'):
            info = parse_info(info, '◎IMDb评分')
            movie['imdb_rating'] = info
        elif info.startswith('◎豆瓣评分'):
            info = parse_info(info, '◎豆瓣评分')
            movie['douban_rating'] = info
        elif info.startswith('◎片　　长'):
            info = parse_info(info, '◎片　　长')
            movie['duration'] = info
        # elif info.startswith('◎导　　演'):
        #     info = parse_info(info, '◎导　　演')
        #     movie['director'] = info
        # elif info.startswith('◎主　　演'):
        #     info = parse_info(info, '◎主　　演')
        #     actors = [info]
        #     for x in range(index + 1, len(infos)):
        #         actor = infos[x].strip()
        #         if actor.startswith('◎'):
        #             break
        #         actors.append(actor)
        #     movie['actors'] = actors
        # elif info.startswith('◎简　　介'):
        #     info = parse_info(info, '◎简　　介')
        #     for x in range(index + 1, len(infos)):
        #         profile = infos[x].strip()
        #         if profile.startswith('【下载地址】'):
        #             break
        #         movie['profile'] = profile
    if len(imgs) > 1:
        screen_shot = imgs[1]
        movie['screen_shot'] = screen_shot
    zoom_str = etree.tostring(zoom_element, encoding='utf-8').decode('utf-8')
    soup = BeautifulSoup(zoom_str, 'html.parser')
    magnet_link = soup.find('a', href=True)['href']

    movie['download_link'] = magnet_link
    return movie
#用于解析电影详情页的信息


def fetch_movies_for_page(page_number):
    url = f'http://www.dytt8.net/html/gndy/dyzz/list_23_{page_number}.html'
    detail_urls = get_detail_urls(url)
    movies = []
    for detail_url in detail_urls:
        movie = parse_detail_urls(detail_url)
        if movie:
            movies.append(movie)
    return movies
# 用于处理每一页的电影数据

def spider():
    all_movies = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_page = {executor.submit(fetch_movies_for_page, x): x for x in range(1, 142)}
        for future in as_completed(future_to_page):
            page_number = future_to_page[future]
            try:
                movies = future.result()
                all_movies.extend(movies)
            except Exception as exc:
                print(f'Page {page_number} generated an exception: {exc}')
            time.sleep(1)  # 避免过于频繁地请求服务器
    save_movies_to_excel(all_movies, 'movies.xlsx')


def save_movies_to_excel(movies, filename):
    """
    将电影数据保存到 Excel 文件中

    参数:
    movies (list of dict): 包含电影信息的字典列表
    filename (str): 要保存的 Excel 文件名
    """
    # 将电影数据列表转换为 pandas DataFrame
    df = pd.DataFrame(movies)

    # 将 DataFrame 保存为 Excel 文件
    df.to_excel(filename, index=False, engine='openpyxl')
if __name__ == '__main__':
    spider()





# 用于爬取电影天堂的电影信息并保存到 Excel 文件中


