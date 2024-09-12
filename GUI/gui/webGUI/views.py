from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render

from django.shortcuts import HttpResponse  # 导入HttpResponse模块
from .models import UserInfo
import json, pymysql

import requests
import base64
import hashlib
import time
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage
from . import chatbot_utils as util
def helloworld(request):  # request是必须带的实例。类似class下方法必须带self一样
    return HttpResponse("Hello World!!")  # 通过HttpResponse模块直接返回字符串到前端页面

#用户界面
def author_view(request):
    return render(request, 'author.html')

#登录界面
def toLogin_view(request):
    return render(request, 'login.html') #返回渲染好的login界面

#将用户输入的用户名与密码与数据库中数据进行比对
def Login_view(request):

    u = request.POST.get('user','')
    p = request.POST.get('password','')
    if u and p :
        info = {
            "user_name": u,
            "user-password": p
        }
        with open(r'D:\PythonProject\moviemate\movie-reommendation-system\GUI\gui\webGUI\static\assets\userData\author.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        if data:
            # 更新author.json的target
            data['target'] = info
        with open(r'D:\PythonProject\moviemate\movie-reommendation-system\GUI\gui\webGUI\static\assets\userData\author.json','w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        c = UserInfo.objects.filter(user_name=u, user_password=p).count()
        if c:
            return HttpResponseRedirect('http://127.0.0.1:8000/dev/index/')
        else:
            return HttpResponse('Login failed！')
    else:
        return HttpResponse('Your user name or password should not be empty！')

#注册界面
def toRegister_view(request):
    return render(request, 'register.html') #返回渲染好的界面

#将用户注册信息存入数据库
def register_view(request):
    u = request.POST.get('user', '')
    p = request.POST.get('password', '')
    if u and p:
        if UserInfo.objects.filter(user_name=u).exists():
            return HttpResponse('This username is already taken. Please try another one.')
        else:
            stu = UserInfo(user_name=u, user_password=p)
            stu.save()
            # Pass a message to the template
            message = 'Register successfully! Redirecting to login page in 2s...'
            return render(request, 'register_success.html', {'message': message})
    else:
        return HttpResponse('Please try again！')

#搜索界面
def post_view(request):
    # 搜索的电影
    question = request.GET.get('search', '')
    print(f'post-question: {question}')
    response = render(request, 'post.html')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

#主页
def index_view(request):
    question = request.POST.get('search', '')
    print(f'index-question: {question}')
    host = 'localhost'
    user = 'root'
    password = '123456'
    port = 3306
    database = 'MovieMate'
    charset = 'utf8'
    if question:
        try:
            connection = pymysql.connect(host=host, user=user, password=password, port=port, charset=charset, database=database)
            print({f'connection:{connection}'})
            if connection:
                with connection.cursor() as cursor:
                    #搜索到的电影信息
                    results = search_moviemate_data_by_title(cursor, question)
                    # 搜索电影的类别,多个类别取第一个
                    category = results['Category'].split('/')[0]
                    print(f'category{category}')
                    #同类别评分最高的十部电影
                    best_movies = best_10_movies_by_genre(cursor, category)
                    img_urls = []
                    detail_urls = []
                    for url in best_movies:
                        img_urls.append(url['poster_url'])
                        detail_urls.append((url['detail_url']))
                    print(f'type:{best_movies}')
                    if results:
                        #更新author.json
                        with open(r'D:\PythonProject\moviemate\movie-reommendation-system\GUI\gui\webGUI\static\assets\userData\author.json','r', encoding='utf-8') as file:
                            data = json.load(file)
                        if data:
                            #更新author.json的imgurls
                            if results['url'] not in data['imgurls']:
                                data['imgurls'].insert(0, results['url']) #从列表开头插入元素
                                data['detail_urls'].insert(0, results['detail_url'])
                            if len(data['imgurls']) > 20 and len(data['detail_urls']) > 20:  # 只保留最近的二十条搜索记录
                                del data['imgurls'][20:]
                                del data['detail_urls'][20:]
                        else:
                            return HttpResponse('data is empty')
                        with open(r'D:\PythonProject\moviemate\movie-reommendation-system\GUI\gui\webGUI\static\assets\userData\author.json','w', encoding='utf-8') as file:
                            json.dump(data, file, ensure_ascii=False, indent=4)
                        #更新post.json
                        with open(r'D:\PythonProject\moviemate\movie-reommendation-system\GUI\gui\webGUI\static\assets\userData\post.json','r', encoding='utf-8') as file:
                            data = json.load(file)
                        if data:
                            data['target'] = results
                            data['imgurls'] = img_urls
                            data['detail_urls'] = detail_urls
                        else:
                            return HttpResponse('data is empty')
                        with open(r'D:\PythonProject\moviemate\movie-reommendation-system\GUI\gui\webGUI\static\assets\userData\post.json','w', encoding='utf-8') as file:
                            json.dump(data, file, ensure_ascii=False, indent=4)
                        # 处理浏览器缓存
                        response = render(request, 'post.html')
                        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                        response['Pragma'] = 'no-cache'
                        response['Expires'] = '0'
                        return response
                    else:
                        return HttpResponse('No matched movies')
            else:
                return HttpResponse('Database connection failed')
        except Exception as e:
            print(e)
            return HttpResponse(f"An error occurred: {e}")
        finally:
            if connection:
                connection.close()  # 确保在最后关闭数据库连接
    else:
        return render(request, 'index.html')

#根据标题从数据库中搜索电影信息
def search_moviemate_data_by_title(cursor, title):
    try:
        sql = 'SELECT * FROM moviemate_movies WHERE title LIKE %s'
        cursor.execute(sql, ('%' + title + '%',))
        result = cursor.fetchone()
        results = {
            'Name': result[6],
            'img': result[9],
            'MM Rating': result[10],
            'Category': result[2],
            'Star': result[1],
            'Date': result[4],
            'url': result[9],
            'detail_url':result[5]
        }
        return results
    except Exception as e:
        print('查询moviemate电影数据库时发生异常：', e)
        raise

#同类别评分最高的十部电影
def best_10_movies_by_genre(cursor, genre):
    try:
        # 编写SQL查询语句，按评分降序排列，同时筛选特定类别,因为重复太多了，限制的数量可以适当增加，现在选的是300
        sql = f'SELECT title, mm_rating, poster_url, detail_url FROM moviemate_movies WHERE genre LIKE %s ORDER BY mm_rating DESC LIMIT 500'
        # 执行SQL查询，传入类别参数
        cursor.execute(sql, ('%' + genre + '%',))
        # 获取查询结果
        results = cursor.fetchall()
        best_movies = []
        for row in results:
            movie_name, mm_rating, poster_url, detail_url = row
            best_movies.append({
                'title': movie_name,
                'mm_rating': mm_rating,
                'poster_url': poster_url,
                'detail_url': detail_url
            })
        best_10_movies = []
        #防止重复
        for movie in best_movies:
            if movie not in best_10_movies:
                best_10_movies.append(movie)
        return best_10_movies
    except Exception as e:
        # 打印异常信息
        print(f'查找类别为 {genre} 的评分最高的10部电影时发生错误: {e}')
        return None


def chat_view(request):
    util.answer = ""
    if request.method == 'POST':
        Input = request.POST['user_input']
        query = util.checklen(util.getText("user", Input))
        # print("MovieMate:", end="")
        util.main(
            appid="1fd7ab4e",  # 填写控制台中获取的 APPID 信息
            api_secret="NmQ1ZTU5NDFkY2Q5NWNhZTM5ZGM4NmE1",  # 填写控制台中获取的 APISecret 信息
            api_key="679684f5a7086dd84ff413486042687b",  # 填写控制台中获取的 APIKey 信息
            # appid、api_secret、api_key三个服务认证信息请前往开放平台控制台查看（https://console.xfyun.cn/services/bm35）
            gpt_url="wss://spark-api.xf-yun.com/v4.0/chat",
            # Spark_url = "ws://spark-api.xf-yun.com/v3.1/chat"  # v3.0环境的地址
            # Spark_url = "ws://spark-api.xf-yun.com/v2.1/chat"  # v2.0环境的地址
            # Spark_url = "ws://spark-api.xf-yun.com/v1.1/chat"  # v1.5环境的地址
            domain="4.0Ultra",
            # domain = "generalv3"    # v3.0版本
            # domain = "generalv2"    # v2.0版本
            # domain = "general"    # v2.0版本
            query=query
        )
        bot_response = next(
            (item['content'] for item in reversed(util.getText("assistant", util.answer)) if item['role'] == 'assistant'), None)
        print("bot",bot_response)
        return JsonResponse({'response': bot_response})



    return render(request, 'chat.html')