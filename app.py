from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import tempfile
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class CodeRequest(BaseModel):
    code: str

class TestRequest(BaseModel):
    questionId: int
    code: str

@app.post("/run-code")
async def run_code(request: CodeRequest):
    with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False) as temp_file:
        temp_file.write(request.code.encode())
        temp_file_name = temp_file.name

    try:
        # Compile the C++ code
        compile_process = subprocess.run(["g++", temp_file_name, "-o", "temp_executable"], 
                                         capture_output=True, text=True, check=True)
        
        # Run the compiled executable
        run_process = subprocess.run(["./temp_executable"], 
                                     capture_output=True, text=True, timeout=5)
        
        return {"output": run_process.stdout}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=400, detail=f"Compilation error: {e.stderr}")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=400, detail="Code execution timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary files
        os.remove(temp_file_name)
        if os.path.exists("temp_executable"):
            os.remove("temp_executable")

@app.post("/run-tests")
async def run_tests(request: TestRequest):
    # In a real app, you'd have test cases for each question
    # and run the submitted code against those tests
    return {"result": f"Tests not implemented yet for question {request.questionId}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

