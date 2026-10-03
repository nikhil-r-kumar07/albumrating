from django.urls import path
from . import views

urlpatterns = [
    path('edit/', views.edit, name = 'profiles.edit'),
    path('reviews/', views.reviews, name = 'profiles.reviews'),
    path('lists/', views.lists, name = 'profiles.lists'),
    path('lists/<int:id>/', views.list_detail, name = 'profiles.list'),
    path('lists/<int:id>/update/', views.list_update, name = 'profiles.list_update'),
    path('lists/<int:id>/delete/', views.list_delete, name = 'profiles.list_delete'),
    path('lists/add/', views.list_add, name = 'profiles.list_add'),
    path('lists/<int:id>/item/<int:item_id>/', views.list_item, name = 'profiles.list_item'),
    path('queue/', views.queue, name = 'profiles.queue'),
    path('queue/add/', views.queue_add, name = 'profiles.queue_add'),
    path('queue/item/<int:item_id>/', views.queue_item, name = 'profiles.queue_item'),
]
