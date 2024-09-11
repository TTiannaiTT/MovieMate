import httpx
from functools import lru_cache
import csv


class MovieDatabase:
    def __init__(self, tmdb_api_key):
        self.tmdb_api_key = tmdb_api_key

    @lru_cache(maxsize=1024)
    def get_movie_details(self, movie_id: int):
        try:
            response = httpx.get(f'https://api.themoviedb.org/3/movie/{movie_id}', headers={
                'Authorization': f'Bearer {self.tmdb_api_key}'
            }, params={
                'language': 'en-US'
            })

            # 打印响应状态码和响应内容
            # print(f"Response Status Code: {response.status_code}")
            # print(f"Response Content: {response.text}")

            # 检查是否成功获取数据
            if response.status_code == 200:
                movie = response.json()
                if 'poster_path' in movie:
                    movie['poster_url'] = self.get_poster_url(movie['poster_path'])
                else:
                    movie['poster_url'] = 'N/A'
                return movie
            else:
                # API 请求失败时返回错误信息
                return {'error': 'Failed to retrieve movie details'}
        except httpx.RequestError as e:
            # 捕获和打印请求错误
            return {'error': f'Request failed: {e}'}

    def get_poster_url(self, poster_path):
        base_url = 'https://image.tmdb.org/t/p/w500'
        return f'{base_url}{poster_path}'

    def save_movie_to_csv(self, movie_list, filename):
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # 写入标题行
            writer.writerow([
                'Title', 'Overview', 'Poster URL', 'Backdrop Path', 'Genres',
                'Origin Country', 'Original Title', 'Release Date',
                'Vote Average', 'Vote Count'
            ])
            for movie_data in movie_list:
                # 写入数据行
                writer.writerow([
                    movie_data.get('title', 'N/A'),
                    movie_data.get('overview', 'N/A'),
                    movie_data.get('poster_path', 'N/A'),
                    movie_data.get('backdrop_path', 'N/A'),
                    ', '.join(genre['name'] for genre in movie_data.get('genres', [])),
                    ', '.join(movie_data.get('origin_country', [])),
                    movie_data.get('original_title', 'N/A'),
                    movie_data.get('release_date', 'N/A'),
                    movie_data.get('vote_average', 'N/A'),
                    movie_data.get('vote_count', 'N/A')
                ])

# 使用你自己的 API 密钥
api_key = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0OGY3OTdmZDYzZWViZWRmYTRhNGEzOWZlNzkxOGRhNyIsIm5iZiI6MTcyNTU0MjUzNS4yMjExNjMsInN1YiI6IjY2ZDlhZWE2YjIwZDI0Y2NhMWZjYzMxZiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.owqprBWlFFK5HMg-S29z2BQZnthF4Vcirubd4JV7haA'  # 替换为实际的 API 密钥
mdb = MovieDatabase(api_key)
all_movies = []

for movie_id in range(1, 100000):  # 从 ID 1 到 100000
    print(f"Fetching movie details for ID: {movie_id}")
    movie_details = mdb.get_movie_details(movie_id)
    if movie_details:
        all_movies.append(movie_details)

# 保存到 CSV 文件
csv_filename = 'movie_details.csv'
mdb.save_movie_to_csv(all_movies, csv_filename)

print(f"All movie details saved to {csv_filename}")
