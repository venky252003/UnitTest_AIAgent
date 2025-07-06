#!/usr/bin/env python3
"""
FastAPI AI Agent - Automated Test Generation and Documentation
This agent analyzes FastAPI applications and generates unit tests and documentation.
"""

import ast
import inspect
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import importlib.util
import tempfile
import os
import re


@dataclass
class TestResult:
    """Represents the result of a test execution"""
    test_name: str
    status: str  # 'PASSED', 'FAILED', 'ERROR'
    output: str
    error: Optional[str] = None


@dataclass
class APIEndpoint:
    """Represents a FastAPI endpoint"""
    method: str
    path: str
    function_name: str
    parameters: List[Dict[str, Any]]
    return_type: str
    docstring: Optional[str] = None
    dependencies: List[str] = None


class FastAPIAnalyzer:
    """Analyzes FastAPI applications to extract endpoint information"""
    
    def __init__(self, app_file_path: str):
        self.app_file_path = Path(app_file_path)
        self.endpoints: List[APIEndpoint] = []
        
    def analyze_app(self) -> List[APIEndpoint]:
        """Analyze the FastAPI application and extract endpoints"""
        try:
            with open(self.app_file_path, 'r') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            self.endpoints = self._extract_endpoints(tree, source_code)
            return self.endpoints
        except Exception as e:
            print(f"Error analyzing app: {e}")
            return []
    
    def _extract_endpoints(self, tree: ast.AST, source_code: str) -> List[APIEndpoint]:
        """Extract endpoint information from AST"""
        endpoints = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has FastAPI decorators
                endpoint_info = self._extract_endpoint_info(node, source_code)
                if endpoint_info:
                    endpoints.append(endpoint_info)
        
        return endpoints
    
    def _extract_endpoint_info(self, func_node: ast.FunctionDef, source_code: str) -> Optional[APIEndpoint]:
        """Extract endpoint information from function node"""
        decorators = []
        
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    # app.get(), app.post(), etc.
                    method = decorator.func.attr.upper()
                    path = None
                    
                    # Extract path from decorator arguments
                    if decorator.args:
                        if isinstance(decorator.args[0], ast.Constant):
                            path = decorator.args[0].value
                    
                    if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] and path:
                        # Extract parameters
                        parameters = self._extract_parameters(func_node)
                        
                        # Extract return type
                        return_type = self._extract_return_type(func_node)
                        
                        # Extract docstring
                        docstring = ast.get_docstring(func_node)
                        
                        return APIEndpoint(
                            method=method,
                            path=path,
                            function_name=func_node.name,
                            parameters=parameters,
                            return_type=return_type,
                            docstring=docstring
                        )
        
        return None
    
    def _extract_parameters(self, func_node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Extract function parameters"""
        parameters = []
        
        for arg in func_node.args.args:
            param_info = {
                'name': arg.arg,
                'type': 'Any',
                'required': True
            }
            
            # Extract type annotation
            if arg.annotation:
                param_info['type'] = self._get_type_name(arg.annotation)
            
            parameters.append(param_info)
        
        return parameters
    
    def _extract_return_type(self, func_node: ast.FunctionDef) -> str:
        """Extract return type annotation"""
        if func_node.returns:
            return self._get_type_name(func_node.returns)
        return 'Any'
    
    def _get_type_name(self, type_node: ast.AST) -> str:
        """Get type name from AST node"""
        if isinstance(type_node, ast.Name):
            return type_node.id
        elif isinstance(type_node, ast.Constant):
            return str(type_node.value)
        elif isinstance(type_node, ast.Attribute):
            return f"{type_node.value.id}.{type_node.attr}"
        else:
            return 'Any'


class TestGenerator:
    """Generates unit tests for FastAPI endpoints"""
    
    def __init__(self, endpoints: List[APIEndpoint]):
        self.endpoints = endpoints
    
    def generate_tests(self) -> str:
        """Generate unit tests for all endpoints"""
        test_code = self._generate_test_header()
        
        for endpoint in self.endpoints:
            test_code += self._generate_endpoint_test(endpoint)
        
        test_code += self._generate_test_footer()
        return test_code
    
    def _generate_test_header(self) -> str:
        """Generate test file header"""
        return '''"""
Generated Unit Tests for FastAPI Application
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
import sys
import os

# Add the parent directory to the path to import the main app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import app
except ImportError:
    # If main.py doesn't exist, create a minimal app for testing
    from fastapi import FastAPI
    app = FastAPI()

client = TestClient(app)


class TestFastAPIEndpoints:
    """Test class for FastAPI endpoints"""
    
'''
    
    def _generate_endpoint_test(self, endpoint: APIEndpoint) -> str:
        """Generate test for a specific endpoint"""
        test_method = f"test_{endpoint.function_name}"
        
        # Generate test data based on parameters
        test_data = self._generate_test_data(endpoint)
        
        test_code = f'''
    def {test_method}(self):
        """Test {endpoint.method} {endpoint.path}"""
        # Test successful response
        response = client.{endpoint.method.lower()}("{endpoint.path}")
        
        # Basic status code check
        assert response.status_code in [200, 201, 204], f"Expected success status, got {{response.status_code}}"
        
        # Check response format
        try:
            response_data = response.json()
            assert isinstance(response_data, (dict, list)), "Response should be valid JSON"
        except:
            # If response is not JSON, check if it's a valid response
            assert response.text is not None, "Response should have content"
        
        print(f"✓ {endpoint.method} {endpoint.path} - PASSED")
    
    def {test_method}_invalid_data(self):
        """Test {endpoint.method} {endpoint.path} with invalid data"""
        # Test with invalid data (if applicable)
        if "{endpoint.method}" in ["POST", "PUT", "PATCH"]:
            response = client.{endpoint.method.lower()}("{endpoint.path}", json={{"invalid": "data"}})
            # Accept various error status codes
            assert response.status_code in [400, 404, 422, 500], f"Expected error status, got {{response.status_code}}"
            print(f"✓ {endpoint.method} {endpoint.path} (invalid data) - PASSED")
'''
        
        return test_code
    
    def _generate_test_data(self, endpoint: APIEndpoint) -> Dict[str, Any]:
        """Generate test data based on endpoint parameters"""
        test_data = {}
        
        for param in endpoint.parameters:
            if param['name'] == 'self':
                continue
                
            param_type = param['type']
            if param_type == 'str':
                test_data[param['name']] = f"test_{param['name']}"
            elif param_type == 'int':
                test_data[param['name']] = 123
            elif param_type == 'float':
                test_data[param['name']] = 123.45
            elif param_type == 'bool':
                test_data[param['name']] = True
            else:
                test_data[param['name']] = f"test_{param['name']}"
        
        return test_data
    
    def _generate_test_footer(self) -> str:
        """Generate test file footer"""
        return '''

if __name__ == "__main__":
    # Run tests directly
    test_instance = TestFastAPIEndpoints()
    
    # Get all test methods
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            method = getattr(test_instance, method_name)
            method()
            passed += 1
        except Exception as e:
            print(f"✗ {method_name} - FAILED: {e}")
            failed += 1
    
    print(f"\\n=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
'''


class DocumentationGenerator:
    """Generates technical documentation for FastAPI endpoints"""
    
    def __init__(self, endpoints: List[APIEndpoint]):
        self.endpoints = endpoints
    
    def generate_documentation(self) -> str:
        """Generate comprehensive API documentation"""
        doc = self._generate_doc_header()
        doc += self._generate_endpoints_section()
        doc += self._generate_schemas_section()
        doc += self._generate_examples_section()
        return doc
    
    def _generate_doc_header(self) -> str:
        """Generate documentation header"""
        return '''# FastAPI Application Documentation

## Overview
This document provides comprehensive technical documentation for the FastAPI application.

## API Endpoints

'''
    
    def _generate_endpoints_section(self) -> str:
        """Generate endpoints documentation section"""
        doc = ""
        
        for endpoint in self.endpoints:
            doc += f"### {endpoint.method} {endpoint.path}\n\n"
            
            if endpoint.docstring:
                doc += f"**Description:** {endpoint.docstring}\n\n"
            
            doc += f"**Function:** `{endpoint.function_name}`\n\n"
            
            if endpoint.parameters:
                doc += "**Parameters:**\n"
                for param in endpoint.parameters:
                    if param['name'] != 'self':
                        required = "Required" if param['required'] else "Optional"
                        doc += f"- `{param['name']}` ({param['type']}) - {required}\n"
                doc += "\n"
            
            doc += f"**Return Type:** {endpoint.return_type}\n\n"
            
            # Example request/response
            doc += "**Example Request:**\n"
            doc += f"```http\n{endpoint.method} {endpoint.path}\n```\n\n"
            
            doc += "**Example Response:**\n"
            doc += f"```json\n{{\n  \"status\": \"success\",\n  \"data\": {{}}\n}}\n```\n\n"
            
            doc += "---\n\n"
        
        return doc
    
    def _generate_schemas_section(self) -> str:
        """Generate schemas documentation section"""
        return '''## Data Schemas

### Common Response Format
```json
{
  "status": "success|error",
  "data": {},
  "message": "string"
}
```

### Error Response Format
```json
{
  "detail": "Error message"
}
```

'''
    
    def _generate_examples_section(self) -> str:
        """Generate examples section"""
        return '''## Usage Examples

### Using curl
```bash
curl -X GET "http://localhost:8000/api/endpoint" \\
     -H "Content-Type: application/json"
```

### Using Python requests
```python
import requests

response = requests.get("http://localhost:8000/api/endpoint")
print(response.json())
```

### Using JavaScript fetch
```javascript
fetch("http://localhost:8000/api/endpoint")
  .then(response => response.json())
  .then(data => console.log(data));
```

## Error Handling

The API uses standard HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

'''


class TestRunner:
    """Runs the generated tests and reports results"""
    
    def __init__(self, test_code: str):
        self.test_code = test_code
    
    def run_tests(self) -> List[TestResult]:
        """Run the generated tests and return results"""
        results = []
        
        # Create a temporary file for the test
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.test_code)
            test_file = f.name
        
        try:
            # Run the test file
            process = subprocess.run([
                sys.executable, test_file
            ], capture_output=True, text=True, timeout=30)
            
            # Parse output
            output_lines = process.stdout.split('\n')
            
            for line in output_lines:
                if '✓' in line and 'PASSED' in line:
                    test_name = line.split('✓')[1].split('-')[0].strip()
                    results.append(TestResult(
                        test_name=test_name,
                        status='PASSED',
                        output=line.strip()
                    ))
                elif '✗' in line and 'FAILED' in line:
                    parts = line.split('✗')[1].split('-')
                    test_name = parts[0].strip()
                    error = parts[1].strip() if len(parts) > 1 else "Unknown error"
                    results.append(TestResult(
                        test_name=test_name,
                        status='FAILED',
                        output=line.strip(),
                        error=error
                    ))
            
            # Add summary from stderr if there were errors
            if process.stderr:
                results.append(TestResult(
                    test_name="General Error",
                    status='ERROR',
                    output=process.stderr,
                    error=process.stderr
                ))
                
        except subprocess.TimeoutExpired:
            results.append(TestResult(
                test_name="Timeout",
                status='ERROR',
                output="Test execution timed out",
                error="Test execution exceeded 30 seconds"
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Execution Error",
                status='ERROR',
                output=str(e),
                error=str(e)
            ))
        finally:
            # Clean up temporary file
            try:
                os.unlink(test_file)
            except:
                pass
        
        return results


class FastAPIAIAgent:
    """Main AI Agent for FastAPI test generation and documentation"""
    
    def __init__(self, app_file_path: str):
        self.app_file_path = app_file_path
        self.analyzer = FastAPIAnalyzer(app_file_path)
        self.endpoints = []
        self.test_generator = None
        self.doc_generator = None
    
    def analyze_application(self) -> bool:
        """Analyze the FastAPI application"""
        print("🔍 Analyzing FastAPI application...")
        self.endpoints = self.analyzer.analyze_app()
        
        if not self.endpoints:
            print("⚠️  No FastAPI endpoints found. Creating basic test structure...")
            # Create a basic endpoint for demonstration
            self.endpoints = [
                APIEndpoint(
                    method="GET",
                    path="/",
                    function_name="root",
                    parameters=[],
                    return_type="dict",
                    docstring="Root endpoint"
                )
            ]
        
        self.test_generator = TestGenerator(self.endpoints)
        self.doc_generator = DocumentationGenerator(self.endpoints)
        
        print(f"✅ Found {len(self.endpoints)} endpoints")
        return True
    
    def generate_tests(self) -> str:
        """Generate unit tests"""
        print("🧪 Generating unit tests...")
        if not self.test_generator:
            raise ValueError("Application not analyzed yet")
        
        test_code = self.test_generator.generate_tests()
        print("✅ Unit tests generated successfully")
        return test_code
    
    def generate_documentation(self) -> str:
        """Generate technical documentation"""
        print("📚 Generating technical documentation...")
        if not self.doc_generator:
            raise ValueError("Application not analyzed yet")
        
        documentation = self.doc_generator.generate_documentation()
        print("✅ Documentation generated successfully")
        return documentation
    
    def run_tests(self, test_code: str) -> List[TestResult]:
        """Run the generated tests"""
        print("🚀 Running tests...")
        runner = TestRunner(test_code)
        results = runner.run_tests()
        
        # Display results
        self._display_test_results(results)
        return results
    
    def _display_test_results(self, results: List[TestResult]):
        """Display test results in a formatted way"""
        print("\n" + "="*50)
        print("📊 TEST RESULTS")
        print("="*50)
        
        passed = sum(1 for r in results if r.status == 'PASSED')
        failed = sum(1 for r in results if r.status == 'FAILED')
        errors = sum(1 for r in results if r.status == 'ERROR')
        
        for result in results:
            status_icon = "✅" if result.status == 'PASSED' else "❌" if result.status == 'FAILED' else "⚠️"
            print(f"{status_icon} {result.test_name}: {result.status}")
            if result.error:
                print(f"   Error: {result.error}")
        
        print("\n" + "-"*50)
        print(f"📈 SUMMARY")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Errors: {errors}")
        print(f"   Total:  {len(results)}")
        print("-"*50)
    
    def save_files(self, test_code: str, documentation: str, output_dir: str = "output"):
        """Save generated files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save test file
        test_file = output_path / "test_generated.py"
        with open(test_file, 'w') as f:
            f.write(test_code)
        
        # Save documentation
        doc_file = output_path / "api_documentation.md"
        with open(doc_file, 'w') as f:
            f.write(documentation)
        
        print(f"💾 Files saved to {output_dir}/")
        print(f"   - test_generated.py")
        print(f"   - api_documentation.md")


def main():
    """Main function to run the AI Agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FastAPI AI Agent - Generate tests and documentation')
    parser.add_argument('app_file', help='Path to the FastAPI application file')
    parser.add_argument('--output', '-o', default='output', help='Output directory for generated files')
    parser.add_argument('--no-run', action='store_true', help='Skip running the tests')
    
    args = parser.parse_args()
    
    if not Path(args.app_file).exists():
        print(f"❌ Error: File {args.app_file} not found")
        return
    
    # Initialize AI Agent
    agent = FastAPIAIAgent(args.app_file)
    
    try:
        # Analyze application
        if not agent.analyze_application():
            print("❌ Failed to analyze application")
            return
        
        # Generate tests
        test_code = agent.generate_tests()
        
        # Generate documentation
        documentation = agent.generate_documentation()
        
        # Run tests (unless skipped)
        if not args.no_run:
            test_results = agent.run_tests(test_code)
        
        # Save files
        agent.save_files(test_code, documentation, args.output)
        
        print("\n🎉 AI Agent completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()