from django.urls import path
from . import views
from .feeds import LatestPostsFeed

app_name = 'blog'

urlpatterns = [
    # Widoki posta.
    # path('', views.PostListView.as_view(), name='post_list'),
    path('', views.post_list, name='post_list'),
    # Widok postów na podstawie tagów.
    path('tag<slug:tag_slug>/', views.post_list, name='post_list_by_tag'),
    path('<int:year>/<int:month>/<int:day>/<slug:post>/',
         views.post_detail, name='post_detail'),
    # Wysyłanie maila z linkiem do posta.
    path('<int:post_id>/share/', views.post_share, name='post_share'),
    # Kanał wiadomości dla postów.
    path('feed/', LatestPostsFeed(), name='post_feed'),
    # Widok wyszukiwania.
    path('search/', views.post_search, name='post_search'),
]
