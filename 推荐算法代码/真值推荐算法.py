import pymysql
import pandas as pd


# 连接MySQL数据库
def connect_db():
    """
    功能:
    - 连接到MySQL数据库并返回连接对象。

    输出:
    - connection: MySQL数据库连接对象，用于执行SQL查询和更新操作。
    """
    connection = pymysql.connect(
        host='localhost',  # 数据库地址
        user='root',  # 数据库用户名
        password='123456',  # 数据库密码
        database='moviemate',  # 目标数据库名称
        charset='utf8mb4'  # 字符编码
    )
    return connection


# 从数据库中获取电影及评分数据
def get_movie_ratings(connection):
    """
    功能:
    - 从数据库中获取电影和多个来源的评分数据，返回pandas DataFrame。

    输入:
    - connection: MySQL数据库连接对象。

    输出:
    - DataFrame: 包含电影ID、电影名称、评分来源及对应评分的DataFrame数据结构。
    """
    query = """
    SELECT movies.movie_id, movies.title, ratings.source, ratings.rating
    FROM movies
    JOIN ratings ON movies.movie_id = ratings.movie_id;
    """
    return pd.read_sql(query, connection)


# 计算每个数据源的初始可信度
def initialize_trust(sources):
    """
    功能:
    - 初始化每个评分来源的数据源可信度，初始值为1.0。

    输入:
    - sources: 评分数据来源的列表或集合。

    输出:
    - trustworthiness: 包含每个数据源初始可信度的字典，格式为 {source: 1.0}。
    """
    return {source: 1.0 for source in sources}


# 更新可信度直到收敛
def update_trustworthiness(movie_ratings, max_iterations=100, tolerance=0.001):
    """
    功能:
    - 根据评分差异迭代更新每个数据源的可信度，直到达到收敛条件。

    输入:
    - movie_ratings: 包含电影评分数据的DataFrame，其中包括电影ID、评分来源和评分。
    - max_iterations: 最大迭代次数，默认值为100。
    - tolerance: 收敛的容差值，当两次迭代可信度变化小于该值时停止，默认值为0.001。

    输出:
    - trustworthiness: 更新后的可信度字典，包含每个数据源的最终可信度。
    """
    unique_sources = movie_ratings['source'].unique()
    trustworthiness = initialize_trust(unique_sources)
    movie_ratings['final_rating'] = 0
    movie_ratings['weighted_rating'] = 0

    for _ in range(max_iterations):
        previous_trust = trustworthiness.copy()

        # 计算加权评分
        for movie_id in movie_ratings['movie_id'].unique():
            movie_df = movie_ratings[movie_ratings['movie_id'] == movie_id]
            total_weight = sum(trustworthiness[source] for source in movie_df['source'])
            if total_weight == 0:
                continue

            weighted_sum = sum(
                trustworthiness[row['source']] * row['rating'] for _, row in movie_df.iterrows()
            )
            final_rating = weighted_sum / total_weight
            movie_ratings.loc[movie_ratings['movie_id'] == movie_id, 'final_rating'] = final_rating

            # 更新每个评分的加权差值
            for _, row in movie_df.iterrows():
                weighted_diff = abs(final_rating - row['rating'])
                movie_ratings.loc[(movie_ratings['movie_id'] == movie_id) & (
                            movie_ratings['source'] == row['source']), 'weighted_rating'] = weighted_diff

        # 根据加权差值更新可信度
        for source in unique_sources:
            source_diffs = movie_ratings[movie_ratings['source'] == source]['weighted_rating']
            trustworthiness[source] = 1.0 / (1.0 + source_diffs.mean())

        # 检查收敛条件
        trust_diff = max(abs(trustworthiness[source] - previous_trust[source]) for source in unique_sources)
        if trust_diff < tolerance:
            break

    return trustworthiness


# 更新电影的最终评分
def update_final_ratings(movie_ratings, trustworthiness):
    """
    功能:
    - 对于每一部电影，选择可信度最高的评分作为最终评分，并更新到DataFrame中。

    输入:
    - movie_ratings: 包含电影评分数据的DataFrame。
    - trustworthiness: 包含每个数据源可信度的字典。

    输出:
    - 无直接输出，更新后的最终评分将存储在 movie_ratings 的 'final_rating' 列中。
    """
    for movie_id in movie_ratings['movie_id'].unique():
        movie_df = movie_ratings[movie_ratings['movie_id'] == movie_id]
        best_source = movie_df.loc[movie_df['source'].isin(trustworthiness.keys())]['source'].iloc[0]
        best_rating = movie_df[movie_df['source'] == best_source]['rating'].values[0]
        movie_ratings.loc[movie_ratings['movie_id'] == movie_id, 'final_rating'] = best_rating


# 保存最终评分到数据库
def save_final_ratings(connection, movie_ratings):
    """
    功能:
    - 将每部电影的最终评分更新保存到数据库中。

    输入:
    - connection: MySQL数据库连接对象。
    - movie_ratings: 包含电影评分数据的DataFrame。

    输出:
    - 无直接输出，更新后的数据被写回数据库。
    """
    cursor = connection.cursor()
    for movie_id in movie_ratings['movie_id'].unique():
        final_rating = movie_ratings[movie_ratings['movie_id'] == movie_id]['final_rating'].values[0]
        cursor.execute(
            "UPDATE movies SET final_rating=%s WHERE movie_id=%s",
            (final_rating, movie_id)
        )
    connection.commit()


# 主函数
def main():
    """
    功能:
    - 主函数，负责执行所有操作：连接数据库，获取电影及评分数据，计算可信度，更新最终评分并保存到数据库。

    输入:
    - 无直接输入

    输出:
    - 无直接输出
    """
    connection = connect_db()

    # 获取电影及其评分数据
    movie_ratings = get_movie_ratings(connection)

    # 进行可信度更新，直到收敛
    trustworthiness = update_trustworthiness(movie_ratings)

    # 更新每部电影的最终评分
    update_final_ratings(movie_ratings, trustworthiness)

    # 保存最终评分到数据库
    save_final_ratings(connection, movie_ratings)

    connection.close()
    print("评分更新完成！")


if __name__ == '__main__':
    main()
