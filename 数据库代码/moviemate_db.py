import json
import pymysql
import pandas as pd

# 创建数据库
def create_database(cursor, database):
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        print(f"数据库 {database} 创建或已存在。")
    except Exception as e:
        print('创建数据库时发生异常：', e)
        raise

# 创建moviemate_movies数据表
def create_moviemate_table(cursor):
    try:
        sql = '''
        CREATE TABLE IF NOT EXISTS moviemate_movies (
            director VARCHAR(255) NOT NULL,
            starring VARCHAR(255) NOT NULL,
            genre VARCHAR(255) NOT NULL,
            region VARCHAR(255) NOT NULL,
            year VARCHAR(255) NOT NULL,
            detail_url VARCHAR(255) NOT NULL,
            title VARCHAR(255) NOT NULL,
            rating VARCHAR(255) NOT NULL,
            rating_count VARCHAR(255) NOT NULL,
            poster_url VARCHAR(255) NOT NULL,
            mm_rating VARCHAR(255) NOT NULL,
            IMDB_rating VARCHAR(255) NOT NULL,
            maoyan_rating VARCHAR(255) NOT NULL
        )
        '''
        cursor.execute(sql)
        print("数据表 moviemate_movies 创建或已存在。")
    except Exception as e:
        print('创建数据表时发生异常：', e)
        raise

def add_all_moviemate_data(cursor, data):
    try:
        sql = 'INSERT IGNORE INTO moviemate_movies(director, starring, genre, region, year, detail_url, title, rating, rating_count, poster_url, mm_rating, IMDB_rating, maoyan_rating) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.executemany(sql, data)
        cursor.connection.commit()
        print(f"成功添加 {cursor.rowcount} 条数据。")
    except Exception as e:
        print('添加所有数据时发生异常：', e)
        raise

def delete_all_moviemate_data(cursor):
    try:
        sql = 'TRUNCATE TABLE douban_movies'
        cursor.execute(sql)
        print("所有数据已删除。")
    except Exception as e:
        print('删除所有数据时发生异常：', e)
        raise

# 通过电影名称查找单条数据
def search_single_moviemate_data_by_title(cursor, title):
    try:
        sql = 'SELECT * FROM moviemate_movies WHERE title LIKE %s'
        cursor.execute(sql, (title,))
        result = cursor.fetchone()
        if result:
            print("查询结果：", result)
        else:
            print("未找到匹配的数据。")
        return result
    except Exception as e:
        print('查询moviemate电影数据库时发生异常：', e)
        raise

def read_xlsx(file_path):
    try:
        # 读取 Excel 文件
        df = pd.read_excel(file_path, dtype=str)
        # 替换 NaN 值为 ''
        df.fillna('', inplace=True)
        # 将 DataFrame 转换为列表
        return df.values.tolist()
    except Exception as e:
        print('读取Excel文件时发生异常：', e)
        raise

def read_csv(file_path):
    try:
        # 读取 CSV 文件
        df = pd.read_csv(file_path, dtype=str)
        # 替换 NaN 值为 ''
        df.fillna('', inplace=True)
        # 将 DataFrame 转换为列表
        return df.values.tolist()
    except Exception as e:
        print('读取CSV文件时发生异常：', e)
        raise

def best_15_movies(cursor):
    try:
        # 编写SQL查询语句，按评分降序排列，并限制结果为前15条
        sql = 'SELECT title, mm_rating, poster_url , detail_url FROM moviemate_movies ORDER BY mm_rating DESC LIMIT 15'
        # 执行SQL查询
        cursor.execute(sql)
        # 获取查询结果
        results = cursor.fetchall()
        # 处理结果
        best_movies = []
        for row in results:
            movie_name, mm_rating, poster_url, detail_url = row
            best_movies.append({
                'title': movie_name,
                'rating': mm_rating,
                'poster_url': poster_url,
                'detail_url':detail_url
            })
        best_15_movies_poster_url = []
        best_15_movies_detail_url = []
        for movie in best_movies:
            if movie['poster_url'] not in best_15_movies_poster_url:
                best_15_movies_poster_url.append(movie['poster_url'])
                best_15_movies_detail_url.append(movie['detail_url'])

        # 读取现有的JSON文件
        with open(r'D:\PythonProject\moviemate\movie-reommendation-system\GUI\gui\webGUI\static\assets\userData\home.json','r', encoding='utf-8') as file:
            data = json.load(file)
        if data:
            # 更新imgurls字段
            data['imgurls'] = best_15_movies_poster_url
            data['detail_urls'] = best_15_movies_detail_url
        # 将更新后的数据写回到JSON文件
        with open(r'D:\PythonProject\moviemate\movie-reommendation-system\GUI\gui\webGUI\static\assets\userData\home.json','w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        # 返回结果
        return best_15_movies_poster_url
    except Exception as e:
        # 打印异常信息
        print(f'查找15名评分最高的电影时发生错误: {e}')

def best_10_movies_by_genre(cursor, genre):
    try:
        # 编写SQL查询语句，按评分降序排列，并限制结果为前15条，同时筛选特定类别
        sql = f'SELECT title, mm_rating, poster_url FROM moviemate_movies WHERE genre LIKE %s ORDER BY rating DESC LIMIT 100'
        # 执行SQL查询，传入类别参数
        cursor.execute(sql, (genre,))
        # 获取查询结果
        results = cursor.fetchall()
        # 处理结果

        best_movies = []
        for row in results:
            movie_name, rating, poster_url = row
            best_movies.append({
                'title': movie_name,
                'rating': rating,
                'poster_url': poster_url
            })
        best_100_movies_poster_url = []
        for movie in best_movies:
            poster_url = movie['poster_url']
            if poster_url not in best_100_movies_poster_url:
                best_100_movies_poster_url.append(poster_url)
        best_10_movies_poster_url = []
        for i in range(10):
            best_10_movies_poster_url.append(best_100_movies_poster_url[i])

        # 读取现有的JSON文件
        with open(
                r'D:\PythonProject\moviemate\movie-reommendation-system\GUI\gui\webGUI\static\assets\userData\post.json',
                'r', encoding='utf-8') as file:
            data = json.load(file)
        if data:
            # 更新imgurls字段
            data['imgurls'] = best_10_movies_poster_url
        # 将更新后的数据写回到JSON文件
        with open(
                r'D:\PythonProject\moviemate\movie-reommendation-system\GUI\gui\webGUI\static\assets\userData\post.json',
                'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        # 返回结果
        return best_10_movies_poster_url
    except Exception as e:
        # 打印异常信息
        print(f'查找类别为 {genre} 的评分最高的15部电影时发生错误: {e}')
        return None



def main():
    host = 'localhost'
    user = 'root'
    password = '123456'
    port = 3306
    database = 'MovieMate'
    charset = 'utf8'

    try:
        connection = pymysql.connect(host=host, user=user, password=password, port=port, database=database, charset=charset)
        with connection.cursor() as cursor:
            best_movies = best_15_movies(cursor)
            print(f'best_movies:{len(best_movies)}')

            # create_database(cursor, database)
            # cursor.execute(f"USE {database}")
            #
            # create_moviemate_table(cursor)
            #
            # file_path = r'../爬取网站代码/moviemate电影.xlsx'
            # data = read_xlsx(file_path)
            #
            # print('数据长度', len(data))
            #
            # delete_all_moviemate_data(cursor)
            # add_all_moviemate_data(cursor, data)
            # print("数据添加完成。")

            # print("准备查询数据...")
            # search_movie_title = input('请输入要查询的电影的名称：')
            # if search_movie_title.strip():
            #     result = search_single_moviemate_data_by_title(cursor, search_movie_title)
            # else:
            #     print("未输入有效的电影名称。")

    except Exception as e:
        print('在执行主函数main时发生异常：', e)
        raise
    finally:
        print("程序执行完毕")

if __name__ == '__main__':
    main()

