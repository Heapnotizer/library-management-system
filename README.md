#Learning Management System

A modern Learning Management System built with **FastAPI**, **SQLModel**, and **PostgreSQL**. Features comprehensive user authentication, role-based access control, and a complete book borrowing/transaction system.

## 🎯 Features

### Authentication & Authorization
- **JWT-based authentication** with secure token management
- **Role-based access control (RBAC)** with two roles: ADMIN and REGULAR
- **Bcrypt password hashing** for secure credential storage
- **Admin bootstrap CLI** for initial admin user creation
- **Token expiration** (30 minutes default)

### User Management
- User registration and login
- Profile management (users can update their own profile)
- Password change functionality
- Admin can manage all users, change roles, and deactivate accounts
- Users can only modify their own profile (admins can modify restricted fields like `is_active` and `role`)

### Authors Management
- **Admin-only operations**: Create, update, delete authors
- **Public read access**: All authenticated users can view authors
- Author information includes: name, bio, email, nationality
- Relationship validation prevents deleting authors with books

### Books Management
- **Admin-only operations**: Create, update, delete books
- **Public read access**: All authenticated users can view books
- **Dynamic copy management**: Books grouped by ISBN
  - `total_copies` = count of all books with same ISBN
  - `available_copies` = total copies minus borrowed copies
- **Availability checking**: Prevents borrowing when no copies available
- Book details include: title, ISBN, published year, description, author
- Filter books by title, ISBN, author, or availability
- Search functionality across titles and ISBNs

### Transactions & Borrowing
- **Users can borrow** books (creates transaction)
- **Users can view their own** borrowing history
- **Users can return books** they borrowed
- **Admins can manage all** transactions
- Borrowing history includes: borrow date, return date, return status
- **Privacy protection**: Book borrowing history is admin-only
- Automatic availability validation when borrowing

## 🏗️ System Architecture

### Tech Stack
- **Framework**: FastAPI (async Python web framework)
- **ORM**: SQLModel (combines SQLAlchemy + Pydantic)
- **Database**: PostgreSQL 16
- **Authentication**: JWT (HS256) + bcrypt
- **Containerization**: Docker & Docker Compose
- **Server**: Gunicorn + Uvicorn

### Core Entities

#### Users
- `id`: Primary key
- `username`: Unique identifier
- `email`: Unique email address
- `hashed_password`: Bcrypt hashed
- `role`: ADMIN or REGULAR
- `is_active`: Account status
- `full_name`: User's full name
- `created_at`, `updated_at`: Timestamps

#### Authors
- `id`: Primary key
- `name`: Author name
- `bio`: Author biography
- `email`: Contact email
- `nationality`: Country of origin
- `books`: Relationship to books
- `created_at`, `updated_at`: Timestamps

#### Books
- `id`: Primary key
- `title`: Book title
- `isbn`: Unique identifier (required, groups copies)
- `published_year`: Publication year
- `author_id`: Foreign key to Author
- `description`: Book description
- `created_at`, `updated_at`: Timestamps
- **Calculated fields**:
  - `total_copies`: Count of books with same ISBN
  - `available_copies`: Total minus borrowed copies

#### Transactions
- `id`: Primary key
- `user_id`: Foreign key to User
- `book_id`: Foreign key to Book
- `borrow_date`: When borrowed
- `return_date`: When returned (nullable)
- `is_returned`: Boolean status
- `created_at`, `updated_at`: Timestamps

### Design Patterns
- **Repository Pattern**: Separation of data access logic
- **Dependency Injection**: FastAPI dependencies for auth, DB session
- **Role-Based Access Control**: Middleware for permission checks
- **On-Demand Calculation**: Copy counts calculated from transactions
- **Partial Updates**: Support for partial entity updates with `exclude_unset=True`

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 16 (included in Docker Compose)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   cd creativescript-lms
   ```

2. **Configure environment variables**
   ```bash
   # Create .env.compose (already exists)
   # Update ADMIN credentials if needed
   ```

3. **Start the system**
   ```bash
   docker-compose up --build
   ```

4. **Access the API**
   ```
   http://localhost:8000
   ```

5. **API Documentation**
   ```
   http://localhost:8000/docs (Swagger UI)
   http://localhost:8000/redoc (ReDoc)
   ```

### Local Development

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database**
   - Ensure PostgreSQL is running
   - Update database URL in environment

4. **Create admin user**
   ```bash
   python src/cli.py
   ```

5. **Run the application**
   ```bash
   uvicorn src.main:app --reload
   ```

## 📚 API Endpoints

### Authentication
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/users/register` | Register new user | Public |
| POST | `/api/v1/users/login` | Login and get token | Public |
| GET | `/api/v1/users/{user_id}` | Get user profile | Protected |
| PATCH | `/api/v1/users/{user_id}` | Update user profile | Protected (owner/admin) |
| POST | `/api/v1/users/{user_id}/change-password` | Change password | Protected |

### Users Management (Admin)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/users` | List all users | Admin only |
| PATCH | `/api/v1/users/{user_id}/role` | Change user role | Admin only |
| DELETE | `/api/v1/users/{user_id}` | Delete user | Admin only |

### Authors
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/authors` | Create author | Admin only |
| GET | `/api/v1/authors` | List authors (paginated) | Protected |
| GET | `/api/v1/authors/{author_id}` | Get author details | Protected |
| PATCH | `/api/v1/authors/{author_id}` | Update author | Admin only |
| DELETE | `/api/v1/authors/{author_id}` | Delete author | Admin only |

### Books
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/books` | Create book | Admin only |
| GET | `/api/v1/books` | List books (paginated, searchable) | Protected |
| GET | `/api/v1/books/{book_id}` | Get book details | Protected |
| PATCH | `/api/v1/books/{book_id}` | Update book | Admin only |
| DELETE | `/api/v1/books/{book_id}` | Delete book | Admin only |
| GET | `/api/v1/books/{book_id}/availability` | Check availability | Protected |

**Query Parameters for Books:**
- `skip`: Pagination offset (default: 0)
- `limit`: Page size (default: 10, max: 100)
- `search`: Search by title or ISBN
- `author_id`: Filter by author
- `available_only`: Show only available books

### Transactions (Borrowing)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/transactions` | Borrow a book | Protected (all users) |
| GET | `/api/v1/transactions` | List all transactions | Admin only |
| GET | `/api/v1/transactions/{transaction_id}` | Get transaction | Protected (owner/admin) |
| GET | `/api/v1/transactions/user/{user_id}` | Get user's transactions | Protected (owner/admin) |
| GET | `/api/v1/transactions/book/{book_id}` | Get book's history | Admin only (privacy) |
| PATCH | `/api/v1/transactions/{transaction_id}` | Update transaction | Admin only |
| POST | `/api/v1/transactions/{transaction_id}/return` | Return book | Protected (owner/admin) |
| DELETE | `/api/v1/transactions/{transaction_id}` | Delete transaction | Admin only |

## 🔐 Permission Model

### ADMIN Role
- ✅ Create, read, update, delete authors
- ✅ Create, read, update, delete books
- ✅ Create, read, update, delete transactions
- ✅ View all users and manage their accounts
- ✅ View complete borrowing history (all books and users)

### REGULAR Role
- ✅ View authors and books (read-only)
- ✅ Borrow books (creates transaction)
- ✅ View their own borrowing history
- ✅ Return their own borrowed books
- ❌ Cannot create/modify/delete authors or books
- ❌ Cannot view other users' transactions
- ❌ Cannot view book borrowing history (privacy)

## 📝 Example Workflows

### Admin Setup
```bash
# 1. Start system
docker-compose up

# 2. Admin user automatically created from env vars
# Credentials from .env.compose

# 3. Login as admin
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

### Adding Books to Library
```bash
# 1. Login as admin, get token
TOKEN="your_jwt_token"

# 2. Create author
curl -X POST http://localhost:8000/api/v1/authors \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Robert Martin",
    "email": "robert@example.com",
    "nationality": "USA"
  }'

# 3. Create book (3 copies with same ISBN)
curl -X POST http://localhost:8000/api/v1/books \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Clean Code",
    "isbn": "978-0132350884",
    "published_year": 2008,
    "author_id": 1,
    "description": "A handbook of agile software craftsmanship"
  }'

# Repeat the above 2 more times to add 3 copies
```

### User Borrowing a Book
```bash
# 1. User registers and logs in
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@example.com", "password": "pass123"}'

# 2. User views available books
curl -X GET "http://localhost:8000/api/v1/books?available_only=true" \
  -H "Authorization: Bearer $USER_TOKEN"

# 3. User borrows a book
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "book_id": 1,
    "borrow_date": "2025-11-11T10:00:00Z"
  }'

# 4. User views their borrowing history
curl -X GET http://localhost:8000/api/v1/transactions/user/2 \
  -H "Authorization: Bearer $USER_TOKEN"

# 5. User returns the book
curl -X POST http://localhost:8000/api/v1/transactions/1/return \
  -H "Authorization: Bearer $USER_TOKEN"
```

## 🗄️ Database Schema

### Key Relationships
```
User ──┐
       ├──> Transaction ──> Book ──> Author
```

- User → has many Transactions
- Transaction → references Book and User
- Book → references Author
- Author → has many Books (one-to-many)

### Indexes for Performance
- `idx_book_author_id`: Fast author filtering
- `idx_book_title_author`: Optimized title + author queries
- Transaction indexes: `user_id`, `book_id`, `is_returned`, `borrow_date`

## 🔧 Configuration

### Environment Variables (`.env.compose`)
```bash
# Database
POSTGRES_USER=pg-user
POSTGRES_PASSWORD=pgpassword
POSTGRES_DB=pgdb
DATABASE_URL=postgresql://pg-user:pgpassword@db_service:5432/pgdb

# Admin Bootstrap
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123
ADMIN_FULLNAME=Administrator

# JWT
SECRET_KEY=your-super-secret-key-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 📊 Copy Management System

### How It Works
1. **Each book row = 1 physical copy**
2. **ISBN groups copies together**
3. **Counts calculated on-demand**:
   - `total_copies` = COUNT(books WHERE isbn = X)
   - `available_copies` = total - borrowed
   - Borrowed = COUNT(transactions WHERE book_id IN (X) AND is_returned = false)

### Benefits
- ✅ Clean database (no redundant copy columns)
- ✅ Always accurate (derived from source of truth)
- ✅ No sync issues
- ✅ Easy to track specific copies
- ✅ Simple delete operations for damaged books

## 🚨 Error Handling

### Common Errors
| Status | Error | Cause |
|--------|-------|-------|
| 400 | "No available copies of this book to borrow" | User tried to borrow unavailable book |
| 401 | "Not authenticated" | Missing or invalid JWT token |
| 403 | "Admin access required" | Regular user tried admin operation |
| 403 | "Cannot access another user's transaction" | User tried to access other user's transaction |
| 404 | "User/Author/Book not found" | Resource doesn't exist |

## 🧪 Testing

### Manual Testing with cURL
See [Example Workflows](#-example-workflows) section above.

### Running Tests
```bash
# (Tests to be implemented)
pytest
```

## 🚀 Deployment

### Docker Compose
```bash
docker-compose up -d
```

### Production Considerations
- Change `SECRET_KEY` to a strong random value
- Update database credentials
- Use environment variable files
- Enable HTTPS
- Configure CORS properly
- Set up monitoring and logging
- Use a production-grade ASGI server

## 📚 Project Structure

```
creativescript-lms/
├── src/
│   ├── main.py                 # FastAPI app entry point
│   ├── cli.py                  # Admin bootstrap CLI
│   ├── api/
│   │   ├── db/
│   │   │   ├── config.py       # DB configuration
│   │   │   ├── session.py      # DB session management
│   │   │   └── __init__.py
│   │   ├── security/
│   │   │   ├── jwt_handler.py  # JWT token management
│   │   │   └── password.py     # Password hashing
│   │   └── v1/
│   │       ├── users/          # User entity and routes
│   │       ├── authors/        # Author entity and routes
│   │       ├── books/          # Book entity and routes
│   │       └── transactions/   # Transaction entity and routes
│   └── __pycache__/
├── boot/
│   └── docker-run.sh           # Docker startup script
├── docker-compose.yml          # Container orchestration
├── Dockerfile                  # App container definition
├── requirements.txt            # Python dependencies
├── .env.compose                # Environment variables
└── README.md                   # This file
```

## 🤝 Contributing

1. Follow the existing code structure
2. Use the repository pattern for data access
3. Add proper error handling
4. Document new endpoints
5. Test manually before committing

## 📄 License

Internal project - CreativeScript LMS

---

**Last Updated**: November 11, 2025  
**Version**: 1.0.0
