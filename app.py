from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import subprocess
import dotenv
import tempfile
import os
import dspy
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
load_dotenv()
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
    prompt = f"""
    You are an experienced programming tutor and I am a student asking you for help with my C++ code.
    - Use the Socratic method to ask me one question at a time or give me one hint at a time in order to guide me to discover the answer on my own. Do NOT directly give me the answer. Even if I give up and ask you for the answer, do not give me the answer. Instead, ask me just the right question at each point to get me to think for myself.
    - Do NOT edit my code or write new code for me since that might give away the answer. Instead, give me hints of where to look in my existing code for where the problem might be. You can also print out specific parts of my code to point me in the right direction.
    - Do NOT use advanced concepts that students in an introductory class have not learned yet. Instead, use concepts that are taught in introductory-level classes and beginner-level programming tutorials. Also, prefer the C++ standard library and built-in features over external libraries.
    Here is my C++ code, which uses C++20 with GNU C++ extensions:
    {current_code}
    Help me fix this bug. I expect to see:
    {expected_output}
    but instead I see:
    {actual_output}
    The question I am solving:
    {problem_statement}

    Previous conversation:
    {conversation_history}

    Based on this information, provide a Socratic question or hint to guide the student's thinking:
    """

    result = tutor(
        problem_statement=problem_statement,
        current_code=current_code,
        expected_output=expected_output,
        actual_output=actual_output,
        conversation_history=conversation_history
    )
    return result.response

@app.post("/run-code")
async def run_code(request: CodeRequest):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as temp_file:
        temp_file.write(request.code)
        temp_file_path = temp_file.name

    try:
        # Compile the C++ code
        compile_process = subprocess.run(['g++', '-std=c++20', temp_file_path, '-o', 'output'], 
                                         capture_output=True, text=True, timeout=10)
        
        if compile_process.returncode != 0:
            raise HTTPException(status_code=400, detail=f"Compilation error: {compile_process.stderr}")

        # Run the compiled code
        run_process = subprocess.run(['./output'], capture_output=True, text=True, timeout=5)
        
        output = run_process.stdout if run_process.returncode == 0 else f"Runtime error: {run_process.stderr}"

        # Generate Socratic response
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
