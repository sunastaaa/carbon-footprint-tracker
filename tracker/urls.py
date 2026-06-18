from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-log/', views.add_carbon_log, name='add_log'),
    path('goal/', views.set_goal, name='set_goal'),
    path('history/', views.history, name='history'),
    path('delete-log/<int:log_id>/', views.delete_log, name='delete_log'),
]