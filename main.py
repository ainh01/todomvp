from jose import jwt  
from datetime import datetime, timedelta  

token = jwt.encode(  
    {"user_id": "test_user", "exp": datetime.utcnow() + timedelta(hours=24)},  
    "45b10ce1fee3b62dcefd8df6589bb0e8b3b6eefff0c4eea428bb3bf633012384",  # Must match JWT_SECRET_KEY in backend .env  
    algorithm="HS256"  
)  
print(token)  