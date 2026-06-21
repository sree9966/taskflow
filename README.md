# TaskFlow

A backend REST API for managing projects and tasks — built to sharpen my Django REST Framework skills and learn how production-grade backend systems are structured.

The idea is simple: teams need a way to create projects, assign tasks, track status, and make sure people can only touch what they're supposed to. No frontend, just a clean API you can consume from anything.

---

## Why I built this

I wanted to go beyond basic CRUD and actually understand how authentication, object-level permissions, and containerization fit together in a real Django project. Along the way I also wrote automated tests for the first time — which honestly changed how I think about writing code.

---

## Tech Stack

- **Python 3.12**
- **Django 6.0 + Django REST Framework** — API layer
- **PostgreSQL 15** — primary database
- **Docker + Docker Compose** — containerized local development
- **PyJWT + bcrypt** — custom JWT authentication
- **pytest + pytest-django** — automated API testing

---

## Features

- User registration and login with JWT tokens
- Custom JWT authentication class wired into DRF's auth system
- Object-level permissions — users can only edit or delete their own projects and tasks
- Task filtering by status and assignee via query params
- Proper read-only field control on serializers (clients can't spoof `owner` or `created_by`)
- Dockerized with a Postgres healthcheck so the app waits for the DB to be ready before starting
- 7 automated tests covering auth flows, permission enforcement, and project isolation

---

## Getting Started

Make sure Docker Desktop is running, then:

```bash
git clone https://github.com/sree9966/taskflow.git
cd taskflow
```

Create a `.env` file in the project root (see `.env.example` for the required variables):

```
SECRET_KEY=your-secret-key
DB_NAME=taskflow
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=db
DB_PORT=5432
```

Start the containers:

```bash
docker-compose up --build
```

Run migrations (in a second terminal):

```bash
docker-compose exec web python manage.py migrate
```

That's it — the API is running at `http://localhost:8000`.

---

## API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/login` | Login and get JWT token | No |
| GET | `/projects` | List your projects | Yes |
| POST | `/projects` | Create a new project | Yes |
| GET | `/projects/<id>` | Get project details + tasks | Yes |
| PATCH | `/projects/<id>` | Update project (owner only) | Yes |
| DELETE | `/projects/<id>` | Delete project (owner only) | Yes |
| GET | `/projects/<id>/tasks` | List tasks (filter by status/assignee) | Yes |
| POST | `/projects/<id>/tasks` | Create a task in a project | Yes |
| PATCH | `/tasks/<id>` | Update a task | Yes |
| DELETE | `/tasks/<id>` | Delete task (creator or project owner only) | Yes |

For protected endpoints, pass the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

### Filtering tasks

```
GET /projects/<id>/tasks?status=in_progress
GET /projects/<id>/tasks?assignee=<user_id>
```

---

## How Permissions Work

This was the most interesting part to build. Rather than manually checking ownership inside every view, I implemented DRF's `BasePermission` classes:

- `IsProjectOwner` — checks `project.owner == request.user` at the object level
- `CanDeleteTask` — allows deletion only if the user is the task creator or the project owner

These are wired into views via `get_permissions()`, so DRF enforces them automatically before any view logic runs.

---

## Running Tests

```bash
docker-compose exec web pytest -v
```

Current coverage includes:
- Register and login success flows
- Login with wrong password returns 401
- Unauthenticated requests are blocked
- Project creation and listing
- Cross-user project access is denied (403/404)

---

## Project Structure

```
taskflow/
├── app/
│   ├── models.py        # User, Project, Task models with UUID PKs
│   ├── views.py         # APIView-based endpoints
│   ├── serializers.py   # DRF serializers with read-only field control
│   ├── permissions.py   # Custom BasePermission classes
│   ├── auth.py          # Custom JWT authentication class
│   ├── urls.py          # URL routing
│   └── tests.py         # pytest test suite
├── taskflow/
│   └── settings.py      # Django settings
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── requirements.txt
```

---

## Things I'd add with more time

- Refresh token support
- Role-based access (admin vs member per project)
- Pagination on list endpoints
- A proper CI pipeline with GitHub Actions running tests on every push
