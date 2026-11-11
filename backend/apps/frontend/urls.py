from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    
    # User Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Module 1: Business Card Builder, Edit, Delete & Manager
    path('cards/', views.card_list, name='card_list'),
    path('card/create/', views.card_builder, name='card_builder'),
    path('card/edit/<str:card_id>/', views.card_builder, name='card_edit'),
    path('card/delete/<str:card_id>/', views.card_delete, name='card_delete'),
    path('card/preview/<str:card_id>/', views.card_preview, name='card_preview'),
    path('card/<slug:slug>/qr.png', views.card_qr_image, name='card_qr_image'),
    path('card/<slug:slug>/', views.card_standalone, name='card_standalone'),

    # Module 2: Website Builder & Preview
    path('website/create/', views.website_builder, name='website_builder'),
    path('website/preview/<str:site_id>/', views.website_preview, name='website_preview'),
    path('site/<slug:slug>/', views.website_standalone, name='website_standalone'),
]

