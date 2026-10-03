from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name = 'albums.index'),
    path('<int:id>/', views.show, name = 'albums.show'),
    path('<int:id>/review/create/', views.create_review, name = 'albums.create_review'),
    path('<int:id>/review/<int:review_id>/edit/', views.edit_review, name = 'albums.edit_review'),
    path('<int:id>/review/<int:review_id>/delete/', views.delete_review, name = 'albums.delete_review'),
    path('mb/<uuid:mbid>/', views.open_album, name = 'albums.open'),
    path('artist/<int:id>/', views.artist, name = 'albums.artist'),
]