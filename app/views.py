
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
import jwt
from datetime import datetime, timedelta
import bcrypt

from app.models import User, Project, Task
from app.serializers import RegisterSerializer, LoginSerializer, ProjectSerializer, TaskSerializer
from app.permissions import IsProjectOwner, CanDeleteTask, CanEditTask
from rest_framework import generics
from django.shortcuts import get_object_or_404




def generate_token(user):
    payload = {
        "user_id": str(user.id),
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"token": generate_token(user)}, status=201)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(email=serializer.validated_data["email"])
        except User.DoesNotExist:
            return Response({"error": "invalid credentials"}, status=401)

        if not bcrypt.checkpw(
            serializer.validated_data["password"].encode(),
            user.password.encode()
        ):
            return Response({"error": "invalid credentials"}, status=401)

        return Response({"token": generate_token(user)})


class ProjectListCreate(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Project.objects.filter(owner=self.request.user)
            .select_related("owner")
            .order_by("-created_at", "-id")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class ProjectDetail(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsProjectOwner()]

    def get_object(self, pk):
        try:
            return Project.objects.get(id=pk)
        except Project.DoesNotExist:
            raise NotFound()

    def get(self, request, pk):
        project = self.get_object(pk)
        self.check_object_permissions(request, project)
        tasks = Task.objects.filter(project=project)
        return Response({
            "project": ProjectSerializer(project).data,
            "tasks": TaskSerializer(tasks, many=True).data
        })

    def patch(self, request, pk):
        project = self.get_object(pk)
        self.check_object_permissions(request, project)
        project.name = request.data.get("name", project.name)
        project.description = request.data.get("description", project.description)
        project.save()
        return Response(ProjectSerializer(project).data)

    def delete(self, request, pk):
        project = self.get_object(pk)
        self.check_object_permissions(request, project)
        project.delete()
        return Response(status=204)

class TaskListCreate(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_project(self):
        return get_object_or_404(
            Project, id=self.kwargs["project_id"], owner=self.request.user
        )

    def get_queryset(self):
        project = self.get_project()
        tasks = Task.objects.filter(project=project).order_by("-created_at", "-id")
        status = self.request.query_params.get("status")
        assignee = self.request.query_params.get("assignee")
        if status:
            tasks = tasks.filter(status=status)
        if assignee:
            tasks = tasks.filter(assignee_id=assignee)
        return tasks

    def perform_create(self, serializer):
        serializer.save(project=self.get_project(), created_by=self.request.user)

class TaskDetail(APIView):

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated(), CanEditTask()]
        if self.request.method == "DELETE":
            return [IsAuthenticated(), CanDeleteTask()]
        return [IsAuthenticated()]

    def get_object(self, pk):
        try:
            return Task.objects.get(id=pk)
        except Task.DoesNotExist:
            raise NotFound()

    def patch(self, request, pk):
        task = self.get_object(pk)
        self.check_object_permissions(request, task)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        task = self.get_object(pk)
        self.check_object_permissions(request, task)
        task.delete()
        return Response(status=204)
