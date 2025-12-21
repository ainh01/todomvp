# Hierarchical Todo App - Frontend  

React-based frontend for hierarchical todo application with real-time synchronization.  

## 🚀 Quick Start  

### Prerequisites  
- Node.js 18+ and npm/yarn  
- Backend API running  

### Installation  

1. **Install dependencies:**  
```bash  
npm install  
# or  
yarn install  
```  

2. **Configure environment:**  
```bash  
cp .env.example .env  
# Edit .env with your API URL and JWT token  
```  

3. **Start development server:**  
```bash  
npm run dev  
# or  
yarn dev  
```  

Application will start at `http://localhost:3000`  

## 🏗️ Project Structure  

```  
src/  
├── components/          # React components  
│   ├── TaskItem.jsx    # Individual task with subtasks  
│   ├── TaskList.jsx    # Task list container  
│   ├── TaskForm.jsx    # Create/edit form  
│   └── DeleteButton.jsx # Delete with confirmation  
├── hooks/              # Custom React hooks  
│   ├── useSSE.js      # SSE connection management  
│   └── useTasks.js    # Task state management  
├── api/               # API client layer  
│   └── taskApi.js     # Axios client and methods  
├── utils/             # Utility functions  
│   └── dateFormat.js  # Date formatting helpers  
├── App.jsx            # Main application component  
├── App.css            # Application styles  
└── main.jsx           # Entry point  
```  

## 🎨 Features  

### Hierarchical Task Structure  
- Create root-level tasks and nested subtasks  
- Unlimited nesting depth  
- Visual indentation for hierarchy  

### Real-time Synchronization  
- Server-Sent Events (SSE) for live updates  
- Automatic reconnection with exponential backoff  
- Updates reflected instantly across all clients  

### Intuitive UI  
- Checkbox for quick completion toggle  
- Inline editing by clicking task  
- Collapsible subtask lists  
- Confirmation before deletion  

### Responsive Design  
- Mobile-friendly interface  
- Touch-optimized interactions  
- Adaptive layout for all screen sizes  

## 🔧 Configuration  

### Environment Variables  

Create `.env` file:  

```env  
VITE_API_URL=http://localhost:8000/api  
VITE_JWT_TOKEN=your_jwt_token_here  
```  

### Generating JWT Token  

For development, generate a test token:  

```javascript  
// Node.js script  
const jwt = require('jsonwebtoken');  

const token = jwt.sign(  
  { user_id: 'test_user_123' },  
  'your-secret-key',  
  { expiresIn: '24h' }  
);  

console.log(token);  
```  

## 📡 Real-time Updates  

The application uses Server-Sent Events (SSE) for real-time synchronization:  

- **Automatic Reconnection**: Implements exponential backoff  
- **Heartbeat**: 30-second intervals to keep connection alive  
- **Event Types**:  
  - `task_created` - New task added  
  - `task_updated` - Task modified  
  - `task_deleted` - Task removed  

## 🎯 Usage  

### Creating Tasks  

1. Click "Create New Task" button  
2. Enter title and optional description  
3. Click "Add Task"  

### Creating Subtasks  

1. Click ➕ icon on any task  
2. Enter subtask details  
3. Submit form  

### Editing Tasks  

1. Click on any task to edit inline  
2. Modify title/description  
3. Click "Update" to save  

### Completing Tasks  

- Click checkbox next to task title  
- Completed tasks show strikethrough  
- Click again to mark incomplete  

### Deleting Tasks  

1. Click 🗑️ icon  
2. Confirm deletion  
3. All subtasks are also deleted  

## 🐛 Troubleshooting  

**SSE not connecting:**  
- Check backend is running  
- Verify JWT token is valid  
- Check browser console for errors  

**Tasks not updating:**  
- Check SSE connection status (indicator in header)  
- Click reconnect button  
- Refresh page to reload all tasks  

**Can't create subtasks:**  
- Ensure parent task is not completed  
- Check network connectivity  

## 🔨 Build for Production  

```bash  
npm run build  
# or  
yarn build  
```  

Output will be in `dist/` directory.  

## 📦 Dependencies  

- **React 18** - UI library  
- **Axios** - HTTP client  
- **date-fns** - Date formatting  
- **Vite** - Build tool  

## 🎨 Customization  

### Styling  

All styles are in `src/App.css` using CSS custom properties. Modify variables in `:root` selector:  

```css  
:root {  
  --color-primary: #2563eb;  
  --color-success: #10b981;  
  /* ... more variables */  
}  
```  

### API Configuration  

Modify `src/api/taskApi.js` to change:  
- Request/response interceptors  
- Error handling logic  
- API endpoint paths  