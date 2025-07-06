"""
Sample FastAPI Application for Testing the AI Agent
"""
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Sample API", description="A sample FastAPI application for testing", version="1.0.0")

# Pydantic models
class User(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None

class UserCreate(BaseModel):
    name: str
    email: str
    age: Optional[int] = None

class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    owner_id: int

# In-memory storage
users_db = []
items_db = []

@app.get("/")
def root():
    """Root endpoint - returns welcome message"""
    return {"message": "Welcome to the Sample API"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "sample-api"}

@app.get("/users", response_model=List[User])
def get_users():
    """Get all users"""
    return users_db

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    """Get a specific user by ID"""
    for user in users_db:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/users", response_model=User)
def create_user(user: UserCreate):
    """Create a new user"""
    new_user = {
        "id": len(users_db) + 1,
        "name": user.name,
        "email": user.email,
        "age": user.age
    }
    users_db.append(new_user)
    return new_user

@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserCreate):
    """Update an existing user"""
    for i, existing_user in enumerate(users_db):
        if existing_user["id"] == user_id:
            updated_user = {
                "id": user_id,
                "name": user.name,
                "email": user.email,
                "age": user.age
            }
            users_db[i] = updated_user
            return updated_user
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Delete a user"""
    for i, user in enumerate(users_db):
        if user["id"] == user_id:
            deleted_user = users_db.pop(i)
            return {"message": f"User {deleted_user['name']} deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/items", response_model=List[Item])
def get_items():
    """Get all items"""
    return items_db

@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    """Get a specific item by ID"""
    for item in items_db:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.post("/items", response_model=Item)
def create_item(item: Item):
    """Create a new item"""
    # Check if owner exists
    owner_exists = any(user["id"] == item.owner_id for user in users_db)
    if not owner_exists:
        raise HTTPException(status_code=400, detail="Owner does not exist")
    
    new_item = {
        "id": len(items_db) + 1,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "owner_id": item.owner_id
    }
    items_db.append(new_item)
    return new_item

@app.get("/users/{user_id}/items", response_model=List[Item])
def get_user_items(user_id: int):
    """Get all items owned by a specific user"""
    # Check if user exists
    user_exists = any(user["id"] == user_id for user in users_db)
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_items = [item for item in items_db if item["owner_id"] == user_id]
    return user_items

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)