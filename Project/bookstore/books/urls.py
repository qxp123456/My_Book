from django.conf.urls import url
from books import views

urlpatterns = [
	url(r'^index/$',views.index, name='index'),
	url(r'^index/(?P<book_id>\d+)/$',views.detail, name='detail'), #详情页
	url(r'^list/(?P<type_id>\d+)/(?P<page>\d+)/$', views.list, name='list')
]