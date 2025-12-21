# Hierarchical Todo API - Backend  

FastAPI backend service for hierarchical todo application with real-time synchronization.  

## 🚀 Quick Start  

### Prerequisites  
- Python 3.9+  
- Upstash Redis account  

### Installation  

1. **Create virtual environment:**  
```bash  
python -m venv venv  
source venv/bin/activate  # On Windows: venv\Scripts\activate  
```  

2. **Install dependencies:**  
```bash  
pip install -r requirements.txt  
```  

3. **Configure environment:**  
```bash  
cp .env.example .env  
# Edit .env with your Upstash Redis credentials  
```  

4. **Run the server:**  
```bash  
uvicorn app.main:app --reload --port 8000  
```  

Server will start at `http://localhost:8000`  

## 📚 API Documentation  

Once running, visit:  
- **Swagger UI**: http://localhost:8000/docs  
- **ReDoc**: http://localhost:8000/redoc  

## 🔐 Authentication  

All endpoints (except `/health` and `/`) require JWT authentication:  

```bash  
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/api/getusertodos  
```  

### JWT Token Structure  
```json  
{  
  "user_id": "user_123",  
  "exp": 1234567890  
}  
```  

## 📡 API Endpoints  

### Tasks  
- `POST /api/addnewusertodo` - Create new task  
- `GET /api/getusertodos` - Get all user tasks  
- `PUT /api/edittodo` - Update task  
- `DELETE /api/deletetodos` - Delete tasks  

### Real-time  
- `GET /api/stream` - SSE connection for live updates  

## 🗄️ Redis Schema  

### Data Structures  
1. **Task Hash**: `task:{id}` - stores task fields  
2. **User Active Tasks**: `user:{userId}:tasks` (Sorted Set)  
3. **User Completed Tasks**: `user:{userId}:tasks:completed` (Sorted Set)  
4. **Task Subtasks**: `task:{id}:subtasks` (Sorted Set)  
5. **Task Counter**: `task:id:counter` (String)  

## 🧪 Testing  

Create a test JWT token:  
```python  
from jose import jwt  
from datetime import datetime, timedelta  

token = jwt.encode(  
    {"user_id": "test_user", "exp": datetime.utcnow() + timedelta(hours=24)},  
    "your-secret-key",  
    algorithm="HS256"  
)  
print(token)  
```  

## 📝 Environment Variables  

```env  
UPSTASH_REDIS_REST_URL=https://your-db.upstash.io  
UPSTASH_REDIS_REST_TOKEN=your-token  
JWT_SECRET_KEY=your-secret-key  
JWT_ALGORITHM=HS256  
BACKEND_PORT=8000  
FRONTEND_URL=http://localhost:3000  
```  

## 🏗️ Project Structure  

```  
backend/  
├── app/  
│   ├── main.py              # FastAPI app initialization  
│   ├── config.py            # Configuration management  
│   ├── routes/  
│   │   └── todos.py         # API endpoints  
│   ├── services/  
│   │   ├── task_service.py  # Business logic  
│   │   └── sse_service.py   # Real-time events  
│   ├── database/  
│   │   ├── redis_client.py  # Redis connection  
│   │   └── lua_scripts.py   # Atomic operations  
│   ├── models/  
│   │   └── task.py          # Pydantic models  
│   └── auth/  
│       └── jwt_handler.py   # Authentication  
├── requirements.txt  
└── README.md  
```  

## 🐛 Troubleshooting  

**Connection refused to Redis:**  
- Verify Upstash credentials in `.env`  
- Check network connectivity  

**JWT verification failed:**  
- Ensure JWT_SECRET_KEY matches token issuer  
- Check token expiration  

**SSE connection drops:**  
- Normal behavior; client should reconnect automatically  
- Check nginx/proxy timeout settings  