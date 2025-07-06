#!/usr/bin/env python3
"""
Demo script showing how to use the FastAPI AI Agent
"""
import sys
import os
from pathlib import Path
import tempfile

# Import the AI Agent (assuming it's in the same directory)
try:
    from fastapi_ai_agent import FastAPIAIAgent
except ImportError:
    print("Please ensure fastapi_ai_agent.py is in the same directory")
    sys.exit(1)

def create_sample_app():
    """Create a sample FastAPI app file for demonstration"""
    sample_app_code = '''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Demo API", version="1.0.0")

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/users")
def get_users():
    """Get all users"""
    return [{"id": 1, "name": "John", "email": "john@example.com"}]

@app.post("/users")
def create_user(user: User):
    """Create a new user"""
    return {"message": "User created", "user": user}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    """Get user by ID"""
    return {"id": user_id, "name": "John", "email": "john@example.com"}
'''
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sample_app_code)
        return f.name

def demo_ai_agent():
    """Demonstrate the AI Agent capabilities"""
    print("🤖 FastAPI AI Agent Demo")
    print("=" * 50)
    
    # Create sample FastAPI app
    app_file = create_sample_app()
    print(f"📝 Created sample app at: {app_file}")
    
    try:
        # Initialize AI Agent
        agent = FastAPIAIAgent(app_file)
        
        # Step 1: Analyze the application
        print("\n1️⃣ Analyzing FastAPI Application...")
        success = agent.analyze_application()
        if not success:
            print("❌ Failed to analyze application")
            return
        
        # Step 2: Generate tests
        print("\n2️⃣ Generating Unit Tests...")
        test_code = agent.generate_tests()
        print("✅ Test generation completed")
        
        # Step 3: Generate documentation
        print("\n3️⃣ Generating Technical Documentation...")
        documentation = agent.generate_documentation()
        print("✅ Documentation generation completed")
        
        # Step 4: Run tests
        print("\n4️⃣ Running Generated Tests...")
        test_results = agent.run_tests(test_code)
        
        # Step 5: Save files
        print("\n5️⃣ Saving Generated Files...")
        output_dir = "demo_output"
        agent.save_files(test_code, documentation, output_dir)
        
        # Step 6: Display generated content preview
        print("\n6️⃣ Preview of Generated Content:")
        print("\n" + "="*50)
        print("📋 GENERATED TEST CODE (First 20 lines):")
        print("="*50)
        test_lines = test_code.split('\n')
        for i, line in enumerate(test_lines[:20]):
            print(f"{i+1:2d}: {line}")
        print("... (truncated)")
        
        print("\n" + "="*50)
        print("📖 GENERATED DOCUMENTATION (First 30 lines):")
        print("="*50)
        doc_lines = documentation.split('\n')