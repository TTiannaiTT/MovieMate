import pandas as pd

# 从 Excel 文件中获取电影及评分数据
def get_movie_ratings_from_excel(file_path):
    """
    功能:
    - 从Excel文件中获取电影和评分数据，返回pandas DataFrame。

    输入:
    - file_path: str类型，Excel文件的路径。

    输出:
    - DataFrame: 包含电影名称、来源及评分的DataFrame数据结构。
    """
    # 读取 Excel 文件
    df = pd.read_excel(file_path)

    # 确保评分列为数值类型
    df['IMDb评分'] = pd.to_numeric(df['IMDb评分'], errors='coerce')
    df['猫眼评分'] = pd.to_numeric(df['猫眼评分'], errors='coerce')
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')

    # 将 IMDb评分、猫眼评分 和 豆瓣评分 作为评分来源
    ratings_list = []

    # IMDb 评分
    for index, row in df.iterrows():
        if not pd.isnull(row['IMDb评分']):
            ratings_list.append({'movie_id': index, 'title': row['title'], 'source': 'IMDb', 'rating': row['IMDb评分']})

    # 猫眼 评分
    for index, row in df.iterrows():
        if not pd.isnull(row['猫眼评分']):
            ratings_list.append({'movie_id': index, 'title': row['title'], 'source': '猫眼', 'rating': row['猫眼评分']})

    # 豆瓣 评分
    for index, row in df.iterrows():
        if not pd.isnull(row['rating']):
            ratings_list.append({'movie_id': index, 'title': row['title'], 'source': '豆瓣', 'rating': row['rating']})

    # 转换成 DataFrame
    ratings_df = pd.DataFrame(ratings_list)
    return ratings_df


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
    # 获取所有唯一的评分来源
    unique_sources = movie_ratings['source'].unique()

    # 初始化每个数据源的可信度
    trustworthiness = initialize_trust(unique_sources)

    # 为存储最终评分和加权差值添加新列，并指定数据类型为浮点数
    movie_ratings['final_rating'] = 0.0
    movie_ratings['weighted_rating'] = 0.0

    # 进行最大迭代次数
    for _ in range(max_iterations):
        # 记录当前的可信度
        previous_trust = trustworthiness.copy()

        # 计算每部电影的加权评分
        for movie_id in movie_ratings['movie_id'].unique():
            # 筛选出当前电影的所有评分记录
            movie_df = movie_ratings[movie_ratings['movie_id'] == movie_id]

            # 计算当前电影的总权重（所有来源的可信度总和）
            total_weight = sum(trustworthiness[source] for source in movie_df['source'])
            if total_weight == 0:
                continue  # 如果总权重为0，则跳过计算

            # 计算加权评分的加权和
            weighted_sum = sum(
                trustworthiness[row['source']] * row['rating'] for _, row in movie_df.iterrows()
            )

            # 计算最终评分
            final_rating = weighted_sum / total_weight
            movie_ratings.loc[movie_ratings['movie_id'] == movie_id, 'final_rating'] = final_rating

            # 更新每个评分的加权差值
            for _, row in movie_df.iterrows():
                weighted_diff = abs(final_rating - row['rating'])
                movie_ratings.loc[(movie_ratings['movie_id'] == movie_id) & (
                        movie_ratings['source'] == row['source']), 'weighted_rating'] = weighted_diff

        # 根据加权差值更新每个数据源的可信度
        for source in unique_sources:
            source_diffs = movie_ratings[movie_ratings['source'] == source]['weighted_rating']
            # 使用差值的均值计算可信度，较小的差值表示更高的可信度
            trustworthiness[source] = 1.0 / (1.0 + source_diffs.mean())

        # 检查是否达到收敛条件
        trust_diff = max(abs(trustworthiness[source] - previous_trust[source]) for source in unique_sources)
        if trust_diff < tolerance:
            break  # 如果可信度变化小于容差值，则停止迭代

    return trustworthiness

# 更新电影的最终评分
def update_final_ratings(movie_ratings, trustworthiness):
    """
    功能:
    - 对于每一部电影，计算加权评分，考虑所有评分来源，并更新到DataFrame中。

    输入:
    - movie_ratings: 包含电影评分数据的DataFrame。
    - trustworthiness: 包含每个数据源可信度的字典。

    输出:
    - 无直接输出，更新后的最终评分将存储在 movie_ratings 的 'final_rating' 列中。
    """
    # 对于每部电影，计算其最终评分
    for movie_id in movie_ratings['movie_id'].unique():
        # 筛选出当前电影的所有评分记录
        movie_df = movie_ratings[movie_ratings['movie_id'] == movie_id]

        # 计算当前电影的总权重（所有来源的可信度总和）
        total_weight = sum(trustworthiness[source] for source in movie_df['source'])
        if total_weight == 0:
            continue  # 如果总权重为0，则跳过计算

        # 计算加权评分的加权和
        weighted_sum = sum(
            trustworthiness[row['source']] * row['rating'] for _, row in movie_df.iterrows()
        )

        # 计算最终评分
        final_rating = weighted_sum / total_weight
        # 将最终评分存储到 DataFrame 中
        movie_ratings.loc[movie_ratings['movie_id'] == movie_id, 'final_rating'] = final_rating


# 保存最终评分到Excel
def save_final_ratings_to_excel(movie_ratings, output_file):
    """
    功能:
    - 将每部电影的最终评分保存到 Excel 文件中。

    输入:
    - movie_ratings: 包含电影评分数据的DataFrame。
    - output_file: str类型，保存的Excel文件路径。

    输出:
    - 无直接输出，更新后的数据被写入Excel文件中。
    """
    # 将 movie_ratings 中的最终评分列保存为 Excel 文件
    movie_ratings[['movie_id', 'title', 'final_rating']].to_excel(output_file, index=False)


# 主函数
def main():
    """
    功能:
    - 主函数，负责执行所有操作：从Excel文件中获取电影及评分数据，计算可信度，更新最终评分并保存到Excel。

    输入:
    - 无直接输入

    输出:
    - 无直接输出
    """
    file_path = '豆瓣电影_合并评分.xlsx'

    # 获取电影及其评分数据
    movie_ratings = get_movie_ratings_from_excel(file_path)

    # 进行可信度更新，直到收敛
    trustworthiness = update_trustworthiness(movie_ratings)

    # 更新每部电影的最终评分
    update_final_ratings(movie_ratings, trustworthiness)

    # 保存最终评分到 Excel 文件
    save_final_ratings_to_excel(movie_ratings, '豆瓣电影_最终评分.xlsx')

    print("评分更新完成！")


if __name__ == '__main__':
    main()
