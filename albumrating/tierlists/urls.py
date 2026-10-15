from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name = 'tierlists.index'),
    path('add/', views.add, name = 'tierlists.add'),
    path('<int:id>/', views.show, name = 'tierlists.show'),
    path('<int:id>/arrange/', views.arrange, name = 'tierlists.arrange'),
    path('<int:id>/add-reviewed/', views.add_reviewed, name = 'tierlists.add_reviewed'),
    path('<int:id>/item/<int:item_id>/remove/', views.remove_item, name = 'tierlists.remove_item'),
    path('<int:id>/update/', views.update, name = 'tierlists.update'),
    path('<int:id>/tier/add/', views.add_tier, name = 'tierlists.add_tier'),
    path('<int:id>/tier/<int:tier_id>/delete/', views.delete_tier, name = 'tierlists.delete_tier'),
    path('<int:id>/delete/', views.delete, name = 'tierlists.delete'),
]
