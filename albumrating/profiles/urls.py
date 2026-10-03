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
    path('favorites/toggle/', views.favorite_toggle, name = 'profiles.favorite_toggle'),
    path('favorites/<int:item_id>/', views.favorite_item, name = 'profiles.favorite_item'),
    path('diary/', views.diary, name = 'profiles.diary'),
    path('diary/log/', views.log_listen, name = 'profiles.log_listen'),
    path('diary/<int:entry_id>/delete/', views.diary_delete, name = 'profiles.diary_delete'),
    path('people/', views.people, name = 'profiles.people'),
    path('feed/', views.feed, name = 'profiles.feed'),
    path('notifications/', views.notifications, name = 'profiles.notifications'),
    path('u/<str:username>/', views.public, name = 'profiles.public'),
    path('u/<str:username>/follow/', views.follow_toggle, name = 'profiles.follow'),
]
