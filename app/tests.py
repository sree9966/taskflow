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
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

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
    def test_projects_are_paginated(self):
        user = User.objects.get(email="ramya@test.com")
        for i in range(25):
            Project.objects.create(name=f"P{i}", owner=user)

        page1 = self.client.get("/projects")
        self.assertEqual(page1.data["count"], 25)
        self.assertEqual(len(page1.data["results"]), 20)

        page2 = self.client.get("/projects?page=2")
        self.assertEqual(len(page2.data["results"]), 5)

        ids1 = {p["id"] for p in page1.data["results"]}
        ids2 = {p["id"] for p in page2.data["results"]}
        self.assertFalse(ids1 & ids2)  # no overlap between pages

    def test_page_size_is_capped(self):
        user = User.objects.get(email="ramya@test.com")
        for i in range(105):
            Project.objects.create(name=f"P{i}", owner=user)
        response = self.client.get("/projects?page_size=1000")
        self.assertEqual(len(response.data["results"]), 100)

    def test_user_only_sees_own_projects(self):
        self.client.post("/projects", {"name": "Mine"}, format="json")
        other = User.objects.create(name="Other", email="other@test.com", password="x")
        Project.objects.create(name="Not mine", owner=other)

        response = self.client.get("/projects")
        names = [p["name"] for p in response.data["results"]]
        self.assertEqual(names, ["Mine"])

    def test_create_project_without_name_returns_400(self):
        response = self.client.post("/projects", {"description": "x"}, format="json")
        self.assertEqual(response.status_code, 400)
class TaskTests(APITestCase):

    def setUp(self):
        self.client.post("/auth/register", {
            "name": "Ramya", "email": "ramya@test.com", "password": "testpass123"
        }, format="json")
        login = self.client.post("/auth/login", {
            "email": "ramya@test.com", "password": "testpass123"
        }, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['token']}")

        self.user = User.objects.get(email="ramya@test.com")
        self.project = Project.objects.create(name="P", owner=self.user)
        self.url = f"/projects/{self.project.id}/tasks"

    def test_tasks_are_paginated(self):
        for i in range(25):
            Task.objects.create(title=f"T{i}", project=self.project, created_by=self.user)

        page1 = self.client.get(self.url)
        self.assertEqual(page1.data["count"], 25)
        self.assertEqual(len(page1.data["results"]), 20)

        page2 = self.client.get(self.url + "?page=2")
        self.assertEqual(len(page2.data["results"]), 5)

    def test_create_task(self):
        response = self.client.post(self.url, {"title": "First task"}, format="json")
        self.assertEqual(response.status_code, 201)

    def test_create_task_without_title_returns_400(self):
        response = self.client.post(self.url, {"description": "x"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_other_user_cannot_see_or_add_tasks(self):
        self.client.post("/auth/register", {
            "name": "Other", "email": "other@test.com", "password": "testpass123"
        }, format="json")
        login2 = self.client.post("/auth/login", {
            "email": "other@test.com", "password": "testpass123"
        }, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login2.data['token']}")

        self.assertEqual(self.client.get(self.url).status_code, 404)
        res = self.client.post(self.url, {"title": "hack"}, format="json")
        self.assertEqual(res.status_code, 404)
        