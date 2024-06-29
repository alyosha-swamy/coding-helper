import os
import subprocess
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from prompt import prompt
import dspy

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
    actual_output: str
    conversation_history: str

api_key = os.getenv('API_KEY')
if not api_key:
    raise ValueError("API_KEY environment variable not set")

gpt4_turbo = dspy.OpenAI(model='gpt-4', api_key=api_key)
dspy.configure(lm=gpt4_turbo)

class SocraticTutor(dspy.Signature):
    """Generate a Socratic question or hint based on the problem statement, code, and outputs."""
    problem_statement = dspy.InputField(desc="Description of the coding problem")
    current_code = dspy.InputField(desc="Current C++ code")
    expected_output = dspy.InputField(desc="Expected output of the code")
    actual_output = dspy.InputField(desc="Actual output of the code")
    conversation_history = dspy.InputField(desc="Previous questions, hints, and responses")
    response = dspy.OutputField(desc="A Socratic question or hint to guide the student's thinking")

tutor = dspy.ChainOfThought(SocraticTutor)

def generate_socratic_response(problem_statement, current_code, expected_output, actual_output, conversation_history):
    formatted_prompt = prompt.format(
        current_code=current_code,
        expected_output=expected_output,
        actual_output=actual_output,
        problem_statement=problem_statement,
        conversation_history=conversation_history
    )

    result = tutor(
        problem_statement=problem_statement,
        current_code=current_code,
        expected_output=expected_output,
        actual_output=actual_output,
        conversation_history=conversation_history
    )
    return result.response

def compile_code(cpp_file_path):
    compile_process = subprocess.run(['g++', '-std=c++20', file_path, '-o', 'output'], 
                                     capture_output=True, text=True, timeout=10)
    if compile_process.returncode != 0:
        raise HTTPException(status_code=400, detail=f"Compilation error: {compile_process.stderr}")
    return 'output'

def run_compiled_code(executable_path: str) -> str:
    run_process = subprocess.run([executable_path], capture_output=True, text=True, timeout=5)
    return run_process.stderr if run_process.returncode != 0 else run_process.stdout

@app.post("/run-code")
async def run_code(request: CodeRequest):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as temp_file:
        temp_file.write(request.code)
        temp_file_path = temp_file.name

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
        os.unlink(temp_file_path)
        if os.path.exists('output'):
            os.unlink('output')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)