from rest_framework.test import APITestCase
from rest_framework import status
from app.models import User, Project, Task


class AuthTests(APITestCase):

    def test_register_success(self):
        response = self.client.post("/auth/register", {
            "name": "Ramya",
            "email": "ramya@test.com",
            "password": "testpass123"
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.data)

    def test_login_success(self):
        # First register
        self.client.post("/auth/register", {
            "name": "Ramya",
            "email": "ramya@test.com",
            "password": "testpass123"
        }, format="json")

        # Then login
        response = self.client.post("/auth/login", {
            "email": "ramya@test.com",
            "password": "testpass123"
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

    def test_login_wrong_password(self):
        self.client.post("/auth/register", {
            "name": "Ramya",
            "email": "ramya@test.com",
            "password": "testpass123"
        }, format="json")

        response = self.client.post("/auth/login", {
            "email": "ramya@test.com",
            "password": "wrongpassword"
        }, format="json")
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_cannot_access_projects(self):
        response = self.client.get("/projects")
        self.assertIn(response.status_code, [401, 403])


class ProjectTests(APITestCase):

    def setUp(self):
        # Create a user and authenticate before each test
        self.client.post("/auth/register", {
            "name": "Ramya",
            "email": "ramya@test.com",
            "password": "testpass123"
        }, format="json")

        login = self.client.post("/auth/login", {
            "email": "ramya@test.com",
            "password": "testpass123"
        }, format="json")

        self.token = login.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_create_project(self):
        response = self.client.post("/projects", {
            "name": "My Project",
            "description": "Test project"
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "My Project")

    def test_list_projects(self):
        # Create a project first
        self.client.post("/projects", {
            "name": "My Project"
        }, format="json")

        response = self.client.get("/projects")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_other_user_cannot_access_my_project(self):
        # Create project as user 1
        project = self.client.post("/projects", {
            "name": "Private Project"
        }, format="json")
        project_id = project.data["id"]

        # Register and login as user 2
        self.client.post("/auth/register", {
            "name": "Other User",
            "email": "other@test.com",
            "password": "testpass123"
        }, format="json")

        login2 = self.client.post("/auth/login", {
            "email": "other@test.com",
            "password": "testpass123"
        }, format="json")

        # Switch to user 2's token
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login2.data['token']}"
        )

        # Try to delete user 1's project — should be forbidden
        response = self.client.delete(f"/projects/{project_id}")
        self.assertIn(response.status_code, [403, 404])