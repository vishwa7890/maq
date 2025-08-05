# Database Setup Guide

## PostgreSQL Database Configuration

### 1. Prerequisites
- PostgreSQL 13+ installed
- Python 3.8+ with required packages:
  ```bash
  pip install sqlalchemy asyncpg psycopg2-binary passlib python-jose
  ```

### 2. Database Setup

#### Create Database
```sql
CREATE DATABASE quotemaster;
CREATE USER quotemaster_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE quotemaster TO quotemaster_user;
```

#### Environment Variables
Create a `.env` file with:
```
DATABASE_URL=postgresql+asyncpg://quotemaster_user:your_password@localhost:5432/quotemaster
```

### 3. File Structure
```
database/
├── setup_database.py    # Database initialization script
├── models/
│   ├── db.py           # Database connection setup
│   └── models.py       # SQLAlchemy ORM models
└── README.md
```

### 4. Run Instructions

#### From project root:
```bash
python -m database.setup_database
```

#### Using absolute path:
```bash
python c:/path/to/2QUAI/database/setup_database.py
```

### 5. Tables Overview
- `users`: User accounts and authentication
- `quotes`: Client quotes and project details
- `chat_messages`: Conversation history
- `quote_interactions`: User interactions with quotes

### 6. Sample Data
Default admin credentials:
- Username: admin
- Password: admin123

Test user credentials:
- Username: testuser
- Password: testpass

### 7. Troubleshooting

#### Connection Issues
- Verify PostgreSQL service is running
- Check firewall settings
- Validate credentials in `.env` file

#### Setup Errors
- Ensure all dependencies are installed
- Check PostgreSQL logs for errors
- Run setup with `--verbose` flag for more details
