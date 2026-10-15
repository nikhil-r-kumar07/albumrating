from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name = 'concerts.index'),
    path('new/', views.create, name = 'concerts.create'),
    path('<int:id>/', views.show, name = 'concerts.show'),
    path('<int:id>/edit/', views.edit, name = 'concerts.edit'),
    path('<int:id>/delete/', views.delete, name = 'concerts.delete'),
    path('u/<str:username>/', views.user_concerts, name = 'concerts.user'),
]
