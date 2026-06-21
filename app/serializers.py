from rest_framework import serializers
from app.models import User, Project, Task
import bcrypt
class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["name", "email", "password"]

    def create(self, validated_data):

        password = validated_data.pop("password")

        hashed_password = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

        user = User.objects.create(
            password=hashed_password,
            **validated_data
        )

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "description", "owner", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]
       

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
         model = Task
         fields = ["id", "title", "description", "status", "priority",
                  "project", "assignee", "created_by", "due_date",
                  "created_at", "updated_at"]
         read_only_fields = ["id", "project", "created_by", "created_at", "updated_at"]
        


