from django.urls import path
from app.views import *

urlpatterns = [
    path("auth/register", RegisterView.as_view()),
    path("auth/login", LoginView.as_view()),

    path("projects", ProjectListCreate.as_view()),
    path("projects/<uuid:pk>", ProjectDetail.as_view()),

    path("projects/<uuid:project_id>/tasks", TaskListCreate.as_view()),
    path("tasks/<uuid:pk>", TaskDetail.as_view()),
]