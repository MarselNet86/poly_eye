from django.urls import path
from . import views

app_name = 'analyzer'

urlpatterns = [
    path('', views.index, name='index'),
    path('search-market/', views.search_market, name='search_market'),
    path('fetch-trades/', views.fetch_trades, name='fetch_trades'),
    path('upload-trades/', views.upload_trades, name='upload_trades'),
    path('set-resolved-side/', views.set_resolved_side, name='set_resolved_side'),
    path('generate-analysis/', views.generate_analysis, name='generate_analysis'),
    path('view-chart/', views.view_chart, name='view_chart'),
    path('download-report/', views.download_report, name='download_report'),
]