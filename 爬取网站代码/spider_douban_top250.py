'''
2024/08/30
实现功能：
爬取了豆瓣网top250的电影名及评分
并保存在了本地数据库中
'''
import requests
from bs4 import BeautifulSoup
import pymysql
import csv

def douban_top250():
    try:
        headers = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/XX.0.0.0 Safari/537.36"
        }

        title_list=[]
        grade_list=[]
        for i in range(0,250,25):
            response = requests.get(f"https://movie.douban.com/top250?start={i}&filter=", headers = headers) #headers作为参数传入，把爬虫请求伪装成浏览器请求
            content = response.text #html
            soup = BeautifulSoup(content, "html.parser") #解析html

            all_titles = soup.findAll('span', attrs={'class': 'title'}) #查找信息
            all_grades = soup.findAll('span', attrs={'class': 'rating_num'})

            for title in all_titles:
                title = title.get_text().split('/')[0].strip()
                """
                获得的文本信息是‘电影中文名/电影原名’,以‘/’分开,
                用split按照‘/’划分为列表，并返回列表第一个值，
                strip去除文本内容前后空格
                """
                if title:
                    title_list.append(title)

            for grade in all_grades:
                grade = grade.get_text().strip()
                grade_list.append(grade)

        movie_list = [(title, grade) for title, grade in zip(title_list, grade_list)]

        with open('douban_top250.csv', 'w', newline='', encoding='utf8') as f:
            writer = csv.writer(f)
            writer.writerow(['标题','评分'])
            writer.writerows(movie_list)

    except Exception as e:
        print('在爬取豆瓣top250数据时发生异常：',e)
        raise  # 重新抛出异常

if __name__ == '__main__':
    douban_top250()
