from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import tempfile
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str

@app.post("/run-code")
async def run_code(request: CodeRequest):
    logger.info(f"Received code: {request.code}")
    
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False, mode="w") as temp_file:
        temp_file.write(request.code)
        temp_file_name = temp_file.name

    try:
        # Compile the C++ code
        compile_process = subprocess.run(["g++", temp_file_name, "-o", "temp_executable"], 
                                         capture_output=True, text=True, check=True)
        
        # Run the compiled executable with a longer timeout
        run_process = subprocess.run(["./temp_executable"], 
                                     capture_output=True, text=True, timeout=10)
        
        return {"output": run_process.stdout}
    except subprocess.CalledProcessError as e:
        logger.error(f"Compilation error: {e.stderr}")
        raise HTTPException(status_code=400, detail=f"Compilation error: {e.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("Code execution timed out")
        raise HTTPException(status_code=400, detail="Code execution timed out. Your program may have an infinite loop or is taking too long to execute.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary files
        os.remove(temp_file_name)
        if os.path.exists("temp_executable"):
            os.remove("temp_executable")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
