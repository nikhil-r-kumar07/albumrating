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
    path('artist/<int:id>/review/create/', views.create_artist_review, name = 'albums.create_artist_review'),
    path('artist/<int:id>/review/<int:review_id>/edit/', views.edit_artist_review, name = 'albums.edit_artist_review'),
    path('artist/<int:id>/review/<int:review_id>/delete/', views.delete_artist_review, name = 'albums.delete_artist_review'),
    path('review/<int:review_id>/comment/', views.add_comment, name = 'albums.add_comment'),
    path('artist-review/<int:review_id>/comment/', views.add_artist_comment, name = 'albums.add_artist_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name = 'albums.delete_comment'),
    path('comment/<int:comment_id>/report/', views.report_comment, name = 'albums.report_comment'),
    path('review/<int:review_id>/like/', views.like_review, name = 'albums.like_review'),
    path('artist-review/<int:review_id>/like/', views.like_artist_review, name = 'albums.like_artist_review'),
]