from jose import jwt  
from datetime import datetime, timedelta  

token = jwt.encode(  
    {"user_id": "test_user", "exp": datetime.utcnow() + timedelta(hours=24)},  
    "your-secret-key",  # Must match JWT_SECRET_KEY in backend .env  
    algorithm="HS256"  
)  
print(token)  