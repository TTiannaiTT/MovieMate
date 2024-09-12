from django.urls import path
from . import views

urlpatterns = [
    path('', views.toLogin_view, name = 'tologin'),
    path('login/', views.Login_view, name = 'login'),

    path("index/", views.index_view, name = 'index'),
    path("post/", views.post_view, name='post'),
    path("author/", views.author_view, name='author'),
    path("chat/", views.chat_view, name='chat'),

    path('toregister/', views.toRegister_view, name='toregister'),
    path('register/', views.register_view, name='register')
]