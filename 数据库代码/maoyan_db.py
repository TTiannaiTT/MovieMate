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

# 创建maoyan_movies数据表
def create_maoyan_table(cursor):
    try:
        sql = '''
        CREATE TABLE IF NOT EXISTS maoyan_movies (
            title VARCHAR(255) NOT NULL,
            grade VARCHAR(255) NOT NULL,
            genre VARCHAR(255) NOT NULL,
            cast VARCHAR(255) NOT NULL,
            release_date VARCHAR(255) NOT NULL,
            image_url VARCHAR(255) NOT NULL
        )
        '''
        cursor.execute(sql)
        print("数据表 maoyan_movies 创建或已存在。")
    except Exception as e:
        print('创建数据表时发生异常：', e)
        raise

# def add_all_maoyan_data(cursor, data):
#     try:
#         sql = 'INSERT IGNORE INTO maoyan_movies(title, grade, genre, cast, release_date, image_url) VALUES(%s, %s, %s, %s, %s, %s)'
#         cursor.executemany(sql, data)
#         cursor.connection.commit()
#         print(f"成功添加 {cursor.rowcount} 条数据。")
#     except Exception as e:
#         print('添加数据时发生异常：', e)
#         raise

def add_all_maoyan_data(cursor, data):
    try:
        sql = 'INSERT IGNORE INTO maoyan_movies(title, grade, genre, cast, release_date, image_url) VALUES(%s, %s, %s, %s, %s, %s)'
        for row in data:
            cursor.execute(sql, row)
        cursor.connection.commit()
        print(f"成功添加 {len(data)} 条数据。")
    except Exception as e:
        print('添加数据时发生异常：', e)
        raise

def delete_all_maoyan_data(cursor):
    try:
        sql='TRUNCATE TABLE maoyan_movies'
        cursor.execute(sql)
        print('成功删除所有数据')
    except Exception as e:
        print(f'删除数据时出错{e}')

# 通过电影名称查找单条数据
def search_maoyan_data_by_title(cursor, title):
    try:
        sql = 'SELECT * FROM maoyan_movies WHERE title = %s'
        cursor.execute(sql, (title,))
        result = cursor.fetchone()
        if result:
            print("查询结果：", result)
        else:
            print("未找到匹配的数据。")
        return result
    except Exception as e:
        print('查询数据库电影评分数据时发生异常：', e)
        raise

# 读取csv文件
def read_csv(file_path):
    try:
        df = pd.read_csv(file_path, dtype=str, encoding='utf-8')
        # 用一个空字符串替换所有的 nan 值
        df.fillna('', inplace=True)
        return [tuple(x) for x in df.values.tolist()]
    except Exception as e:
        print('读取CSV文件时发生异常：', e)
        raise

def main():
    host = 'localhost'
    user = 'root'
    password = '123456'
    port = 3306
    database = 'moviemate'
    charset = 'utf8mb4'

    try:
        connection = pymysql.connect(host=host, user=user, password=password, port=port, charset=charset)
        with connection.cursor() as cursor:
            create_database(cursor, database)
            cursor.execute(f"USE {database}")

            create_maoyan_table(cursor)

            file_path = r'../爬取网站代码/movies_maoyan_merge.csv'
            data = read_csv(file_path)
            print('数据长度',len(data))
            print(data[:10])

            delete_all_maoyan_data(cursor)
            add_all_maoyan_data(cursor, data)
            print("数据添加完成。")

            print("准备查询数据...")
            search_movie_title = input('请输入要查询的电影的名称：')
            if search_movie_title.strip():
                result = search_maoyan_data_by_title(cursor, search_movie_title)
            else:
                print("未输入有效的电影名称。")

    except Exception as e:
        print('在执行主函数main时发生异常：', e)
        raise
    finally:
        print("程序执行完毕")

if __name__ == '__main__':
    main()