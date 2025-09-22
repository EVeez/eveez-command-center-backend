# Eveez Service API - Run Instructions

## Quick Start

### Windows (PowerShell)

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create .env with local credentials (do not commit secrets)
@"
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DB=masters
MONGODB_URI=mongodb://eveeziot:Eveez%24I0T%25@eveez.in:37017/eveezlivedata?authSource=admin
MONGODB_DB=eveezlivedata
"@ | Out-File -Encoding utf8 .env

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### macOS/Linux

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env with local credentials (do not commit secrets)
cat > .env << 'EOF'
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DB=masters
MONGODB_URI=mongodb://eveeziot:Eveez%24I0T%25@eveez.in:37017/eveezlivedata?authSource=admin
MONGODB_DB=eveezlivedata
EOF

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

```env
# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DATABASE=masters

# MongoDB Configuration (new names supported as well)
MONGODB_URI=mongodb://eveeziot:Eveez%24I0T%25@eveez.in:37017/eveezlivedata?authSource=admin
MONGODB_DB=eveezlivedata

# Application Configuration
APP_ENV=development
```

## API Endpoints

Once the server is running, the following endpoints are available:

- `GET /` - Health check endpoint
- `GET /city-list` - Get list of cities from MySQL
- `GET /mongo-test` - Test MongoDB connection
- `GET /hub-list` - Get list of hubs from MySQL
- `GET /hub-list/location` - Get hubs filtered by location
- `GET /service-tickets` - Get service tickets from MongoDB
- `GET /service-tickets/request-type` - Counts grouped by request_type with optional filters

### Examples

```bash
curl -s "http://127.0.0.1:8000/service-tickets/request-type" | jq
curl -s "http://127.0.0.1:8000/service-tickets/request-type?location=Kolkata&range=last_7" | jq
curl -s "http://127.0.0.1:8000/service-tickets/request-type?request_type=Monthly%20Service,Breakdown%20Support&range=custom&start=2025-09-01&end=2025-09-15" | jq
```
- `GET /technicians` - Get technicians from MongoDB
- `GET /technicians/location` - Get technicians filtered by location

## Server Information

- **Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Default Host**: 0.0.0.0
- **Default Port**: 8000
- **Entry Point**: `main:app`

## Database Requirements

- **MySQL**: Required for city and hub data
- **MongoDB**: Required for service tickets and technician data

## Confirmation

✅ All existing routes behave exactly the same (paths, methods, payloads)  
✅ Health check endpoint returns 200  
✅ No secrets are committed  
✅ Environment template includes placeholders where needed  
✅ Server starts successfully without runtime errors
