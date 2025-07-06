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
