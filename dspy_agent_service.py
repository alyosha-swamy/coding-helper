import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import dspy

# Load the API key from an environment variable
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the OpenAI client with the GPT-4 model
gpt4_turbo = dspy.OpenAI(
    model='gpt-4o',
    api_key=api_key
)
# Configure the client as the default LM
dspy.configure(lm=gpt4_turbo)

class CodingTutor(dspy.Signature):
    """Generate Socratic questions to guide the implementation of a coding problem."""
    problem_description = dspy.InputField(desc="Description of the coding problem")
    language = dspy.InputField(desc="Programming language being used")
    code = dspy.InputField(desc="Current code for the problem")
    conversation_history = dspy.InputField(desc="Previous questions and answers")
    next_question = dspy.OutputField(desc="Next Socratic question to ask")
    hints = dspy.OutputField(desc="Subtle hints based on the current code, if needed")

tutor = dspy.ChainOfThoughtWithHint(CodingTutor)

class TutorRequest(BaseModel):
    problem_description: str
    language: str
    code: str
    conversation_history: str

class QuestionResponse(BaseModel):
    id: int
    question: str
    hints: str

# In-memory storage for questions and hints
questions_store = {}
current_id = 0

@app.post("/generate-question")
async def generate_question(request: TutorRequest):
    global current_id
    try:
        result = tutor(
            problem_description=request.problem_description,
            language=request.language,
            code=request.code,
            conversation_history=request.conversation_history
        )
        current_id += 1
        questions_store[current_id] = QuestionResponse(
            id=current_id,
            question=result.next_question,
            hints=result.hints
        )
        return questions_store[current_id]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/questions/{question_id}")
async def get_question(question_id: int):
    if question_id not in questions_store:
        raise HTTPException(status_code=404, detail="Question not found")
    return questions_store[question_id]

@app.get("/latest-question")
async def get_latest_question():
    if not questions_store:
        raise HTTPException(status_code=404, detail="No questions available")
    return questions_store[max(questions_store.keys())]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
