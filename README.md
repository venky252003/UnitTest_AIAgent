Of course. As an AI expert, I'll guide you through the design and implementation of an AI Agent that automates unit testing and documentation for FastAPI applications.

This is a fantastic use case for AI, blending code analysis, code generation, and process automation. We'll build this system step-by-step.

### Conceptual Architecture of the AI Agent

An "AI Agent" isn't a single magical entity but a system of components working in concert. Our agent will have the following architecture:

1.  **Code Analyzer (The "Eyes"):** This component reads and understands the user's FastAPI source code. Instead of just reading text, we'll use Python's Abstract Syntax Tree (`ast`) module for a structured, reliable understanding of the API endpoints, methods, and data models (Pydantic schemas).
2.  **LLM Prompt Engine (The "Brainstem"):** Based on the structured data from the analyzer, this component constructs a highly detailed and specific prompt for a Large Language Model (LLM) like GPT-4. The quality of this prompt is critical for getting high-quality output.
3.  **AI Core - LLM (The "Cerebral Cortex"):** This is the generative heart of our agent. We'll use an LLM (e.g., via the OpenAI API) to generate two distinct artifacts based on our prompt:
    *   Python code for `pytest` unit tests.
    *   Markdown for technical API documentation.
4.  **File System Operator (The "Hands"):** This component takes the generated code and documentation from the LLM and saves them into appropriate files (e.g., `test_generated_api.py`, `api_documentation.md`).
5.  **Test Executor & Reporter (The "Voice"):** This component runs the newly created test file using `pytest` via a subprocess. It then captures the output (passes, failures, errors) and presents a clear report to the user.

Here is a visual flow of the process:

```
[FastAPI App: main.py] -> [1. Code Analyzer] -> [2. LLM Prompt Engine] -> [3. AI Core (LLM)]
                                                                                |
                                     +------------------------------------------+
                                     |                                          |
                        [Generated Test Code]                        [Generated Documentation]
                                     |                                          |
                     [4. File System Operator]                    [4. File System Operator]
                                     |                                          |
                    [Saves test_generated_api.py]                  [Saves api_documentation.md]
                                     |
                       [5. Test Executor & Reporter]
                                     |
                       [Runs Pytest & Shows Output]
```

---

### Practical Implementation in Python

Let's build this agent.

#### Step 1: Prerequisites

First, ensure you have the necessary libraries installed.

```bash
pip install fastapi uvicorn "uvicorn[standard]" pytest requests openai
```

You will also need an OpenAI API key. Set it as an environment variable for security.

```bash
# In Linux/macOS
export OPENAI_API_KEY='your-api-key-here'

# In Windows (Command Prompt)
set OPENAI_API_KEY=your-api-key-here
```

#### Step 2: The Example FastAPI Application

Let's create a simple but representative FastAPI application that our agent will work on.

**Save this file as `main.py`:**

```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(
    title="Simple Item API",
    description="A basic API to demonstrate the AI Agent.",
    version="1.0.0"
)

# In-memory "database"
fake_db = {}

class Item(BaseModel):
    name: str = Field(..., example="Laptop")
    description: Optional[str] = Field(None, example="A powerful computing device")
    price: float = Field(..., gt=0, example=1299.99)
    is_offer: Optional[bool] = None

@app.get("/", tags=["General"])
def read_root():
    """Returns a welcome message."""
    return {"message": "Welcome to the Simple Item API"}

@app.get("/items", response_model=List[Item], tags=["Items"])
def get_all_items():
    """Retrieve all items from the database."""
    return list(fake_db.values())

@app.post("/items", response_model=Item, status_code=201, tags=["Items"])
def create_item(item: Item):
    """Create a new item and add it to the database."""
    item_id = len(fake_db) + 1
    fake_db[item_id] = item
    return item

@app.get("/items/{item_id}", response_model=Item, tags=["Items"])
def get_item_by_id(item_id: int):
    """Retrieve a specific item by its ID."""
    if item_id not in fake_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return fake_db[item_id]
```

#### Step 3: The AI Agent Code

Now, for the core of our solution. This script will perform all the steps we outlined in the architecture.

**Save this file as `agent.py`:**

```python
# agent.py
import os
import ast
import subprocess
import openai

# --- Configuration ---
# Ensure your OpenAI API key is set as an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

TARGET_FASTAPI_FILE = "main.py"
GENERATED_TEST_FILE = "test_generated_api.py"
GENERATED_DOCS_FILE = "api_documentation.md"
LLM_MODEL = "gpt-4-turbo-preview" # Or "gpt-3.5-turbo" for a faster, cheaper option

# --- 1. Code Analyzer ---
def analyze_fastapi_code(filepath: str) -> dict:
    """
    Analyzes the FastAPI source code using AST to extract endpoints and schemas.
    """
    with open(filepath, "r") as source:
        tree = ast.parse(source.read())

    endpoints = []
    schemas = []

    for node in ast.walk(tree):
        # Find Pydantic Models (classes inheriting from BaseModel)
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == 'BaseModel':
                    schemas.append(ast.unparse(node))

        # Find FastAPI endpoint decorators
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if (isinstance(decorator, ast.Call) and
                    isinstance(decorator.func, ast.Attribute) and
                    isinstance(decorator.func.value, ast.Name) and
                    decorator.func.value.id == 'app'):
                    
                    endpoint_info = {
                        "path": decorator.args[0].value,
                        "method": decorator.func.attr.upper(),
                        "function_name": node.name,
                        "details": ast.unparse(decorator)
                    }
                    endpoints.append(endpoint_info)

    return {"endpoints": endpoints, "schemas": schemas}

# --- 2. LLM Prompt Engine ---
def construct_llm_prompt(analysis: dict) -> str:
    """
    Constructs a detailed, structured prompt for the LLM.
    """
    prompt = f"""
You are an expert Python developer specializing in FastAPI. Your task is to generate unit tests and technical documentation for the following FastAPI application.

### Application Analysis:
Here is a structured analysis of the FastAPI code:

**Pydantic Schemas:**
```python
{"\n\n".join(analysis['schemas'])}
```

**API Endpoints:**
```json
{analysis['endpoints']}
```

### Your Instructions:

**1. Generate PyTest Unit Tests:**
- Create a complete Python script using `pytest` and FastAPI's `TestClient`.
- Import `TestClient` from `fastapi.testclient` and the `app` from `main`.
- Write test cases for each endpoint.
- For each endpoint, include at least one "happy path" test (successful request).
- For endpoints that can fail (e.g., getting a non-existent item), include a "sad path" test.
- Use appropriate assertions (`assert response.status_code == ...`, `assert response.json() == ...`).
- Make up realistic sample data for POST requests based on the Pydantic schemas.

**2. Generate Technical Documentation:**
- Create documentation in Markdown format.
- For each endpoint, create a section with the following structure:
  - **Endpoint:** `HTTP_METHOD /path` (e.g., `POST /items`)
  - **Description:** A brief explanation of what the endpoint does (infer from code).
  - **Request Body:** If applicable, describe the JSON body and show an example based on the Pydantic schema.
  - **Success Response:** Describe the success status code and show an example JSON response.
  - **Error Response:** If applicable, describe potential error status codes and responses.

### Output Format:
Provide your response in two distinct, clearly marked blocks. Do not include any other text or explanations outside of these blocks.

`### TEST_CODE_START ###`
(Your complete pytest script here)
`### TEST_CODE_END ###`

`### DOCS_START ###`
(Your complete Markdown documentation here)
`### DOCS_END ###`
"""
    return prompt

# --- 3. AI Core (LLM) ---
def generate_with_llm(prompt: str) -> str:
    """
    Sends the prompt to the LLM and gets the generated content.
    """
    print("🤖 Contacting AI Core... This may take a moment.")
    try:
        response = openai.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2, # Lower temperature for more deterministic code
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error communicating with OpenAI: {e}")
        return None

def parse_llm_response(response: str) -> (str, str):
    """
    Parses the LLM's response to extract the code and docs.
    """
    try:
        test_code = response.split("### TEST_CODE_START ###")[1].split("### TEST_CODE_END ###")[0].strip()
        docs = response.split("### DOCS_START ###")[1].split("### DOCS_END ###")[0].strip()
        return test_code, docs
    except IndexError:
        print("❌ Error: LLM response was not in the expected format.")
        print("--- Raw LLM Response ---")
        print(response)
        return None, None

# --- 4. File System Operator ---
def save_files(test_code: str, docs: str):
    """
    Saves the generated content to files.
    """
    with open(GENERATED_TEST_FILE, "w") as f:
        f.write(test_code)
    print(f"✅ Test file saved: {GENERATED_TEST_FILE}")

    with open(GENERATED_DOCS_FILE, "w") as f:
        f.write(docs)
    print(f"✅ Documentation saved: {GENERATED_DOCS_FILE}")

# --- 5. Test Executor & Reporter ---
def run_tests() -> (bool, str):
    """
    Executes the generated pytest file and captures the output.
    """
    print("\n🚀 Running generated tests with pytest...")
    print("-" * 50)
    process = subprocess.run(
        ["pytest", "-v", GENERATED_TEST_FILE],
        capture_output=True,
        text=True
    )
    print(process.stdout)
    if process.stderr:
        print("--- Pytest Errors ---")
        print(process.stderr)
    print("-" * 50)
    
    success = process.returncode == 0
    return success, process.stdout

# --- Main Agent Orchestrator ---
def main():
    print("--- AI Agent for Testing & Docs: Initializing ---")
    
    # 1. Analyze Code
    print(f"🧐 Analyzing source code: {TARGET_FASTAPI_FILE}...")
    code_analysis = analyze_fastapi_code(TARGET_FASTAPI_FILE)
    
    # 2. Construct Prompt
    print("🧠 Constructing prompt for LLM...")
    prompt = construct_llm_prompt(code_analysis)
    
    # 3. Generate Content
    llm_response = generate_with_llm(prompt)
    if not llm_response:
        return # Exit if LLM call failed

    # 4. Parse & Save
    test_code, docs = parse_llm_response(llm_response)
    if not test_code or not docs:
        return # Exit if parsing failed

    save_files(test_code, docs)
    
    # 5. Execute & Report
    success, output = run_tests()
    
    if success:
        print("✅ All generated tests passed!")
    else:
        print("❌ Some generated tests failed. Please review the output above.")
        
    print(f"\n📄 Technical documentation has been generated at: {GENERATED_DOCS_FILE}")
    print("--- AI Agent Task Complete ---")


if __name__ == "__main__":
    main()
```

#### Step 4: How to Run the Agent

1.  Make sure `main.py` and `agent.py` are in the same directory.
2.  Ensure your `OPENAI_API_KEY` is set.
3.  Run the agent from your terminal:

    ```bash
    python agent.py
    ```

#### Step 5: Expected Output

When you run the agent, you will see a series of outputs in your terminal, culminating in the `pytest` results.

**Terminal Output:**

```
--- AI Agent for Testing & Docs: Initializing ---
🧐 Analyzing source code: main.py...
🧠 Constructing prompt for LLM...
🤖 Contacting AI Core... This may take a moment.
✅ Test file saved: test_generated_api.py
✅ Documentation saved: api_documentation.md

🚀 Running generated tests with pytest...
--------------------------------------------------
============================= test session starts ==============================
...
collected 5 items

test_generated_api.py::test_read_root PASSED                               [ 20%]
test_generated_api.py::test_create_item_happy_path PASSED                  [ 40%]
test_generated_api.py::test_get_all_items PASSED                           [ 60%]
test_generated_api.py::test_get_item_by_id_happy_path PASSED               [ 80%]
test_generated_api.py::test_get_item_by_id_not_found_sad_path PASSED       [100%]

============================== 5 passed in ...s ===============================
--------------------------------------------------
✅ All generated tests passed!

📄 Technical documentation has been generated at: api_documentation.md
--- AI Agent Task Complete ---
```

**Generated Documentation (`api_documentation.md`):**

This file will contain clean, well-formatted Markdown similar to this:

````markdown
# API Technical Documentation

## General

### **Endpoint:** `GET /`
- **Description:** Returns a simple welcome message to confirm the API is running.
- **Request Body:** None.
- **Success Response:**
  - **Code:** `200 OK`
  - **Body:**
    ```json
    {
      "message": "Welcome to the Simple Item API"
    }
    ```
- **Error Response:** None.

## Items

### **Endpoint:** `POST /items`
- **Description:** Creates a new item and stores it in the database.
- **Request Body:**
  - A JSON object conforming to the `Item` schema.
  - **Example:**
    ```json
    {
      "name": "Gaming Mouse",
      "description": "A high-precision mouse for gaming",
      "price": 75.50,
      "is_offer": true
    }
    ```
- **Success Response:**
  - **Code:** `201 Created`
  - **Body:** The created item object.
- **Error Response:**
  - **Code:** `422 Unprocessable Entity` if the request body is invalid.

### **Endpoint:** `GET /items`
- **Description:** Retrieves a list of all items currently in the database.
- **Request Body:** None.
- **Success Response:**
  - **Code:** `200 OK`
  - **Body:** A JSON array of item objects.
    ```json
    [
      {
        "name": "Laptop",
        "description": "A powerful computing device",
        "price": 1299.99,
        "is_offer": false
      }
    ]
    ```

### **Endpoint:** `GET /items/{item_id}`
- **Description:** Retrieves a single item by its unique ID.
- **Request Body:** None.
- **Success Response:**
  - **Code:** `200 OK`
  - **Body:** The requested item object.
- **Error Response:**
  - **Code:** `404 Not Found` if an item with the specified ID does not exist.
  - **Body:**
    ```json
    {
      "detail": "Item not found"
    }
    ```
````

This agent provides a powerful, automated workflow for maintaining code quality and documentation, freeing up developer time to focus on building features. You can easily extend it to handle more complex scenarios like database mocking, authentication headers, and different project structures.
