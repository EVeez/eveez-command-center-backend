# Changelog

## Fixes Applied

### 1. Removed Service Tickets Status Endpoint
- **File**: `backend/routes/service_tickets.py`
- **Change**: Removed `/service-tickets/status` endpoint as requested
- **Rationale**: Endpoint was removed per user request

### 2. Created Environment Configuration Template
- **File**: `backend/.env.example`
- **Change**: Created environment variables template with placeholders
- **Rationale**: No secrets hardcoded, provides clear configuration guidance

## Dependencies
- All dependencies were already properly specified in `requirements.txt`
- No additional dependencies were added or removed
- Python 3.12+ compatibility confirmed

## Environment Variables Required
The following environment variables are expected by the application:

- `MYSQL_HOST` - MySQL server host (default: localhost)
- `MYSQL_PORT` - MySQL server port (default: 3306)
- `MYSQL_USER` - MySQL username (default: root)
- `MYSQL_PASSWORD` - MySQL password (default: 1234)
- `MYSQL_DATABASE` - MySQL database name (default: masters)
- `MONGODB_URL` - MongoDB connection string
- `MONGODB_DATABASE` - MongoDB database name (default: eveezlivedata)
- `APP_ENV` - Application environment (default: development)

## Known Limitations
- Database connections are required to fully exercise data routes
- MongoDB connection uses external server (eveez.in:37017)
- MySQL connection uses localhost:3306 by default
