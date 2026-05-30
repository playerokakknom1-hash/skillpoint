from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tournaments/', views.tournaments_list, name='tournaments_list'),
    path('tournament/<int:tournament_id>/', views.tournament_detail, name='tournament_detail'),
    path('create-tournament/', views.create_tournament, name='create_tournament'),
    path('create-team/', views.create_team, name='create_team'),
    path('my-team/', views.my_team, name='my_team'),
    path('join-tournament/<int:tournament_id>/', views.join_tournament, name='join_tournament'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('friends/', views.friends_list, name='friends_list'),
    path('send-friend/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('accept-friend/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('add-to-team/<int:user_id>/', views.add_friend_to_team, name='add_friend_to_team'),
    path('remove-friend/<int:user_id>/', views.remove_friend, name='remove_friend'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/toggle-staff/<int:user_id>/', views.toggle_staff, name='toggle_staff'),
    path('leave-team/', views.leave_team, name='leave_team'),
    path('disband-team/', views.disband_team, name='disband_team'),
    path('api/support/', views.support_api, name='support_api'),
]