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
from app.permissions import IsProjectOwner, CanDeleteTask


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


class ProjectListCreate(APIView):

    def get(self, request):
        projects = Project.objects.filter(owner=request.user)
        return Response(ProjectSerializer(projects, many=True).data)

    def post(self, request):
        project = Project.objects.create(
            name=request.data.get("name"),
            description=request.data.get("description", ""),
            owner=request.user
        )
        return Response(ProjectSerializer(project).data, status=201)


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


class TaskListCreate(APIView):

    def get(self, request, project_id):
        tasks = Task.objects.filter(project_id=project_id)

        status = request.GET.get("status")
        assignee = request.GET.get("assignee")

        if status:
            tasks = tasks.filter(status=status)
        if assignee:
            tasks = tasks.filter(assignee_id=assignee)

        return Response(TaskSerializer(tasks, many=True).data)

    def post(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise NotFound()

        task = Task.objects.create(
            title=request.data["title"],
            description=request.data.get("description"),
            project=project,
            created_by=request.user
        )
        return Response(TaskSerializer(task).data, status=201)


class TaskDetail(APIView):

    def get_permissions(self):
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
        for field in ["title", "description", "status", "priority", "due_date"]:
            if field in request.data:
                setattr(task, field, request.data[field])
        if "assignee" in request.data:
            try:
                task.assignee = User.objects.get(id=request.data["assignee"])
            except User.DoesNotExist:
                return Response({"error": "assignee not found"}, status=400)
        task.save()
        return Response(TaskSerializer(task).data)

    def delete(self, request, pk):
        task = self.get_object(pk)
        self.check_object_permissions(request, task)
        task.delete()
        return Response(status=204)