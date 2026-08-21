from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llm import generate_code
from executor import run_code_in_sandbox

app = FastAPI(title="Sandbox Executor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExecuteRequest(BaseModel):
    prompt: str
    context: str = ""


class ExecuteResponse(BaseModel):
    success: bool
    output_type: str | None = None
    description: str | None = None
    data: str | None = None      # base64 encoded file
    code: str | None = None      # generated code, useful for debugging
    error: str | None = None


@app.post("/execute", response_model=ExecuteResponse)
async def execute(request: ExecuteRequest):
    # Step 1 — ask LLM to generate code
    try:
        llm_result = generate_code(request.prompt, request.context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")

    code = llm_result["code"]
    output_filename = llm_result["output_filename"]
    output_type = llm_result["output_type"]
    description = llm_result["description"]

    # Step 2 — run the code in sandbox
    execution_result = run_code_in_sandbox(code, output_filename)

    if not execution_result["success"]:
        return ExecuteResponse(
            success=False,
            code=code,
            error=execution_result["error"]
        )

    return ExecuteResponse(
        success=True,
        output_type=output_type,
        description=description,
        data=execution_result["data"],
        code=code
    )


@app.get("/health")
async def health():
    return {"status": "ok"}