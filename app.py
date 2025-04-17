import os
import subprocess
import tempfile
import requests  # Added requests for API calls
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from prompt import prompt

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust this to your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str
    problem_statement: str
    expected_output: str
    # actual_output is not sent for run-code, it's generated
    conversation_history: str
    # solution: str # Removed if not used by generate_socratic_response

# New model specifically for hint requests
class HintRequest(BaseModel):
    code: str
    problem_statement: str
    expected_output: str
    actual_output: str  # This is the output currently shown in the UI
    conversation_history: str
    # solution: str # Removed if not used by generate_socratic_response

# Get OpenRouter API key
openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
if not openrouter_api_key:
    raise ValueError("OPENROUTER_API_KEY environment variable not set")

def generate_socratic_response(problem_statement, current_code, expected_output, actual_output, conversation_history):
    formatted_prompt = prompt.format(
        current_code=current_code,
        expected_output=expected_output,
        actual_output=actual_output,
        problem_statement=problem_statement,
        conversation_history=conversation_history
    )

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openrouter_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemini-flash-1.5",
                "messages": [
                    {"role": "user", "content": formatted_prompt}
                ]
            }
        )
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        result = response.json()
        # Assuming the response structure follows OpenAI's format
        if result.get("choices") and len(result["choices"]) > 0:
             message = result["choices"][0].get("message")
             if message and message.get("content"):
                 return message["content"].strip()
        # Fallback or error handling if the expected structure isn't found
        raise HTTPException(status_code=500, detail="Failed to parse response from OpenRouter API")

    except requests.exceptions.RequestException as e:
        # Handle connection errors, timeouts, etc.
        raise HTTPException(status_code=503, detail=f"Error connecting to OpenRouter API: {e}")
    except Exception as e:
        # Catch other potential errors during API call or response processing
        # Log the error for debugging: print(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error processing AI response: {e}")

def compile_code(cpp_file_path):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_exec_file:
        executable_path = temp_exec_file.name
    compile_process = subprocess.run(['g++', '-std=c++20', cpp_file_path, '-o', executable_path],
                                     capture_output=True, text=True, timeout=10)
    if compile_process.returncode != 0:
        os.unlink(executable_path)
        raise HTTPException(status_code=400, detail=f"Compilation error: {compile_process.stderr}")
    return executable_path

def run_compiled_code(executable_path: str) -> str:
    run_process = subprocess.run([executable_path], capture_output=True, text=True, timeout=5)
    return run_process.stderr if run_process.returncode != 0 else run_process.stdout

# Endpoint for running code AND getting a hint based on the *execution* output
@app.post("/run-code")
async def run_code(request: CodeRequest):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as temp_file:
        temp_file.write(request.code)
        temp_file_path = temp_file.name

    executable_path = None
    try:
        executable_path = compile_code(temp_file_path)
        output = run_compiled_code(executable_path)

        response = generate_socratic_response(
            request.problem_statement, request.code, request.expected_output, output, request.conversation_history
        )

        return {
            "output": output,
            "response": response
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=400, detail="Code execution timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary files
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        if executable_path and os.path.exists(executable_path):
            os.unlink(executable_path)

# New endpoint specifically for requesting hints without running code
@app.post("/request-hint")
async def request_hint(request: HintRequest):
    try:
        # Directly generate response without compiling/running
        response = generate_socratic_response(
            request.problem_statement,
            request.code,
            request.expected_output,
            request.actual_output, # Use the output state sent from frontend
            request.conversation_history
        )
        return {"response": response}
    except Exception as e:
        # Handle potential errors during AI response generation
        raise HTTPException(status_code=500, detail=f"Error generating hint: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
