Here's a structured approach to building your **AI Agent** to:

* Automatically generate **unit tests** for a given FastAPI application.
* Generate **technical documentation** for the API endpoints.
* Execute tests and report results.

### 🚀 **Complete Python-based AI Agent Solution:**

---

### ✅ **Step-by-Step Implementation:**

**Requirements**:

```bash
pip install fastapi uvicorn pytest openai
```

---

## 📁 **Project Structure**:

```
fastapi-ai-agent/
├── api_agent.py
├── main.py             # FastAPI Application
├── tests/              # Auto-generated unit tests
└── docs/               # Auto-generated documentation
```

---

## ▶️ **Step 1: Example FastAPI application (main.py)**:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@app.post("/items/")
async def create_item(name: str, price: float):
    return {"name": name, "price": price}
```

---

## 🤖 **Step 2: AI Agent Script (api\_agent.py)**:

```python
import openai
import subprocess
import os

openai.api_key = 'your-api-key'

def generate_unit_test(api_code):
    prompt = f"""
    Generate detailed pytest-based unit tests for this FastAPI endpoint:

    {api_code}

    The tests must cover both success and failure cases.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=800,
    )

    return response.choices[0].message.content

def generate_api_docs(api_code):
    prompt = f"""
    Generate clear and concise technical documentation in Markdown for the following FastAPI endpoints:

    {api_code}

    Include HTTP methods, request parameters, response structures, and sample responses.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=600,
    )

    return response.choices[0].message.content

def save_to_file(content, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

def run_pytest_and_get_results():
    result = subprocess.run(["pytest", "tests/"], capture_output=True, text=True)
    return result.stdout, result.stderr

if __name__ == "__main__":
    # Read API application source code
    with open("main.py", "r") as f:
        api_source = f.read()

    # Generate unit test cases
    test_code = generate_unit_test(api_source)
    save_to_file(test_code, "tests/test_main.py")
    print("✅ Unit tests generated at tests/test_main.py")

    # Generate API documentation
    api_docs = generate_api_docs(api_source)
    save_to_file(api_docs, "docs/api_documentation.md")
    print("✅ Documentation generated at docs/api_documentation.md")

    # Run the tests and print output
    stdout, stderr = run_pytest_and_get_results()
    print("\n--- 🧪 Test Execution Results ---")
    print(stdout)

    if stderr:
        print("\n--- ⚠️ Errors & Warnings ---")
        print(stderr)
```

---

## 🧪 **Step 3: Run the AI Agent**

```bash
python api_agent.py
```

---

## 🎯 **Example Output:**

```
✅ Unit tests generated at tests/test_main.py
✅ Documentation generated at docs/api_documentation.md

--- 🧪 Test Execution Results ---
=================== test session starts ====================
collected 2 items

tests/test_main.py ..                                  [100%]

==================== 2 passed in 0.50s =====================
```

---

## 📘 **Generated Documentation (Example):**

(`docs/api_documentation.md`)

````markdown
## API Endpoint Documentation

### 1. Get Item by ID (`GET /items/{item_id}`)

**Description**: Retrieves an item by its ID.

**Parameters**:

- `item_id` (int): The ID of the item.

**Response**:

```json
{
  "item_id": 1
}
````

---

### 2. Create Item (`POST /items/`)

**Description**: Creates a new item.

**Parameters**:

* `name` (string): Name of the item.
* `price` (float): Price of the item.

**Response**:

```json
{
  "name": "example",
  "price": 12.99
}
```

```

---

## 🔑 **Key Points & Recommendations**:

- Replace `'your-api-key'` with your OpenAI API Key.
- Extend the prompts for more complex tests (edge cases, auth, exceptions, etc.).
- Integrate this script into CI/CD pipelines (e.g., Jenkins, GitHub Actions) for automated continuous testing and documentation.

With this AI-driven solution, you automate essential testing and documentation tasks, dramatically enhancing development productivity and code quality.

Let me know if you need further customization!
```
