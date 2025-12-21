# 📋 Hierarchical Todo Application  

Full-stack todo application with real-time synchronization, hierarchical task structures, and soft delete functionality.  

## 🌟 Features  

### Core Functionality  
- ✅ **Hierarchical Tasks** - Unlimited nesting of subtasks  
- ✅ **Real-time Sync** - SSE-powered live updates across all clients  
- ✅ **Soft Delete** - Cascade deletion with data preservation  
- ✅ **Task Completion** - Track progress with completion timestamps  
- ✅ **User Isolation** - JWT-based authentication and authorization  

### Technical Highlights  
- **Backend**: FastAPI with async/await, Upstash Redis, Pydantic validation  
- **Frontend**: React 18 with hooks, optimistic updates, auto-reconnecting SSE  
- **Database**: Redis with Lua scripts for atomic operations  
- **Architecture**: RESTful API with SSE for real-time events  

## 🏗️ Architecture Overview  

```  
┌─────────────┐         ┌──────────────┐         ┌────────────────┐  
│   React     │◄───SSE──┤   FastAPI    │◄────────┤ Upstash Redis  │  
│   Frontend  │         │   Backend    │         │   Database     │  
│             ├────HTTP─►│              │         │                │  
└─────────────┘         └──────────────┘         └────────────────┘  
     │                         │                         │  
     │                         │                         │  
  Browser                  Python 3.9+              REST API  
                          JWT Auth                 Lua Scripts  
```  

## 🚀 Quick Start  

### Prerequisites  

- **Python 3.9+** for backend  
- **Node.js 18+** for frontend  
- **Upstash Redis** account ([Get free account](https://upstash.com/))  

### 1. Clone Repository  

```bash  
git clone <repository-url>  
cd hierarchical-todo-app  
```  

### 2. Backend Setup  

```bash  
cd backend  

# Create virtual environment  
python -m venv venv  
source venv/bin/activate  # Windows: venv\Scripts\activate  

# Install dependencies  
pip install -r requirements.txt  

# Configure environment  
cp .env.example .env  
# Edit .env with your Upstash credentials  

# Start server  
uvicorn app.main:app --reload --port 8000  
```  

Backend will run at `http://localhost:8000`  

### 3. Frontend Setup  

```bash  
cd frontend  

# Install dependencies  
npm install  

# Configure environment  
cp .env.example .env  
# Edit .env with API URL and JWT token  

# Start development server  
npm run dev  
```  

Frontend will run at `http://localhost:3000`  

### 4. Generate Test JWT Token  

```python  
# Python script  
from jose import jwt  
from datetime import datetime, timedelta  

token = jwt.encode(  
    {"user_id": "test_user", "exp": datetime.utcnow() + timedelta(hours=24)},  
    "your-secret-key",  # Must match JWT_SECRET_KEY in backend .env  
    algorithm="HS256"  
)  
print(token)  
```  

Add this token to `frontend/.env` as `VITE_JWT_TOKEN`  

## 📚 Documentation  

- **[Backend Documentation](./backend/README.md)** - API details, Redis schema, setup  
- **[Frontend Documentation](./frontend/README.md)** - Component structure, hooks, styling  
- **[API Documentation](http://localhost:8000/docs)** - Interactive Swagger UI (when backend running)  

## 🗄️ Database Schema  

### Redis Data Structures  

```  
task:{id}                          # Hash - Task data  
user:{userId}:tasks                # Sorted Set - Active tasks (score: created_at)  
user:{userId}:tasks:completed      # Sorted Set - Completed tasks  
task:{taskId}:subtasks             # Sorted Set - Subtask relationships  
task:id:counter                    # String - Auto-increment ID  
```  

### Task Hash Fields  

```json  
{  
  "id": "123",  
  "user_id": "user_456",  
  "title": "Task title",  
  "description": "Description",  
  "parent_id": "0",  
  "created_at": "2024-01-15T10:30:00Z",  
  "completed_at": "",  
  "deleted_at": "",  
  "updated_at": "2024-01-15T10:30:00Z"  
}  
```  

## 🔌 API Endpoints  

| Method | Endpoint | Description |  
|--------|----------|-------------|  
| POST | `/api/addnewusertodo` | Create new task |  
| GET | `/api/getusertodos` | Get all user tasks |  
| PUT | `/api/edittodo` | Update task |  
| DELETE | `/api/deletetodos` | Delete tasks (soft delete) |  
| GET | `/api/stream` | SSE stream for real-time updates |  

## 🧪 Testing  

### Test Task Creation  

```bash  
curl -X POST http://localhost:8000/api/addnewusertodo \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{  
    "title": "Test Task",  
    "description": "Test Description",  
    "parent_id": "0"  
  }'  
```  

### Test Real-time Updates  

1. Open application in two browser tabs  
2. Create/update/delete task in one tab  
3. See changes instantly reflected in other tab  

## 🔒 Security  

- **JWT Authentication** - All endpoints require valid JWT token  
- **User Isolation** - Users can only access their own tasks  
- **Input Validation** - Pydantic models validate all input  
- **SQL Injection Prevention** - Redis with parameterized Lua scripts  

## 📈 Performance  

- **Atomic Operations** - Lua scripts ensure consistency  
- **Efficient Queries** - O(log N) sorted set operations  
- **Connection Pooling** - Upstash REST API manages connections  
- **Optimistic Updates** - Instant UI feedback with SSE verification  

## 🚢 Deployment  

### Backend (Example: Render/Railway)  

```bash  
# Build command  
pip install -r requirements.txt  

# Start command  
uvicorn app.main:app --host 0.0.0.0 --port $PORT  
```  

### Frontend (Example: Vercel/Netlify)  

```bash  
# Build command  
npm run build  

# Output directory  
dist  
```  

### Environment Variables  

**Backend:**  
- `UPSTASH_REDIS_REST_URL`  
- `UPSTASH_REDIS_REST_TOKEN`  
- `JWT_SECRET_KEY`  

**Frontend:**  
- `VITE_API_URL`  
- `VITE_JWT_TOKEN`  

## 🛠️ Technology Stack  

### Backend  
- **FastAPI** - Modern async Python web framework  
- **Upstash Redis** - Serverless Redis database  
- **Pydantic** - Data validation  
- **python-jose** - JWT handling  
- **sse-starlette** - Server-Sent Events  

### Frontend  
- **React 18** - UI library with hooks  
- **Vite** - Fast build tool  
- **Axios** - HTTP client  
- **date-fns** - Date formatting  

## 📝 License  

MIT License - feel free to use for personal or commercial projects  

## 🤝 Contributing  

Contributions welcome! Please open an issue or pull request.  

## 📧 Support  

For issues or questions, please open a GitHub issue.  

---  

**Made with ❤️ using FastAPI and React**  
```  

---  

## **PHASE 3: Final Verification & Testing**  

### **✅ Checklist Verification**  

Let me verify all tasks from our original TODO list:  

**Backend Development:**  
- ✅ 1.1-1.4: Project setup complete  
- ✅ 2.1-2.6: Redis operations implemented  
- ✅ 3.1-3.5: Pydantic models defined  
- ✅ 4.1-4.3: JWT authentication implemented  
- ✅ 5.1-5.5: Business logic services complete  
- ✅ 6.1-6.6: All API routes implemented with CORS  
- ✅ 7.1-7.3: Error handling and logging added  

**Frontend Development:**  
- ✅ 8.1-8.4: React project setup complete  
- ✅ 9.1-9.5: API client layer implemented  
- ✅ 10.1-10.3: Custom hooks (useSSE, useTasks) complete  
- ✅ 11.1-11.6: All React components implemented  
- ✅ 12.1-12.4: State management with hooks complete  
- ✅ 13.1-13.5: Styling and utilities complete  
- ✅ 14.1-14.5: Documentation complete  

**Testing & Deployment:**  
- ✅ 15.1-15.3: Manual testing procedures documented  

---  

### **🧪 Final Testing Guide**  

#### **Test 1: Backend API**  

```bash  
# Terminal 1 - Start backend  
cd backend  
source venv/bin/activate  
uvicorn app.main:app --reload --port 8000  

# Terminal 2 - Test endpoints  
# Generate token first  
python  
>>> from jose import jwt  
>>> from datetime import datetime, timedelta  
>>> token = jwt.encode({"user_id": "test_user", "exp": datetime.utcnow() + timedelta(hours=24)}, "your-secret-key", algorithm="HS256")  
>>> print(token)  
>>> exit()  

# Create task  
curl -X POST http://localhost:8000/api/addnewusertodo \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Task", "description": "Testing", "parent_id": "0"}'  

# Get tasks  
curl http://localhost:8000/api/getusertodos \
  -H "Authorization: Bearer YOUR_TOKEN"  

# Test SSE  
curl -N http://localhost:8000/api/stream \
  -H "Authorization: Bearer YOUR_TOKEN"  
```  

#### **Test 2: Frontend Integration**  

```bash  
# Terminal 3 - Start frontend  
cd frontend  
npm run dev  

# Open browser to http://localhost:3000  
# 1. Create a root task  
# 2. Add subtask to root task  
# 3. Complete a task  
# 4. Edit a task  
# 5. Delete a task  
```  

#### **Test 3: Real-time Sync**  

1. Open app in **two browser tabs**  
2. In Tab 1: Create a task  
3. In Tab 2: Watch it appear automatically  
4. In Tab 2: Complete the task  
5. In Tab 1: Watch it update in real-time  
6. Verify SSE connection indicator shows "Live" in both tabs  

---  

### **🚀 Quick Start Commands**  

```bash  
# Complete Setup Script  
# =====================  

# 1. Backend Setup  
cd backend  
python -m venv venv  
source venv/bin/activate  # Windows: venv\Scripts\activate  
pip install -r requirements.txt  
cp .env.example .env  
# Edit .env with Upstash credentials  
uvicorn app.main:app --reload --port 8000 &  

# 2. Frontend Setup  
cd ../frontend  
npm install  
cp .env.example .env  
# Edit .env with API URL and JWT token  
npm run dev &  

# 3. Open browser  
open http://localhost:3000  
```  

---  

### **📋 Environment Configuration Summary**  

#### **Backend `.env`**  
```env  
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io  
UPSTASH_REDIS_REST_TOKEN=your_token_here  
JWT_SECRET_KEY=your-secret-key-min-32-chars  
JWT_ALGORITHM=HS256  
```  

#### **Frontend `.env`**  
```env  
VITE_API_URL=http://localhost:8000/api  
VITE_JWT_TOKEN=your.jwt.token.here  
```  