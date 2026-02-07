from django.urls import path
from . import views

app_name = 'market'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload', views.upload_csv, name='upload_csv'),
    path('files/', views.files_list, name='files_list'),
    path('files/<slug:slug>/', views.file_detail, name='file_detail'),
    path('files/<slug:slug>/delete/', views.file_delete, name='file_delete'),
]