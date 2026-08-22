from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llm import generate_code
from executor import run_code_in_sandbox
import sys

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
    try:
        llm_result = generate_code(request.prompt, request.context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")

    code = llm_result["code"]
    output_filename = llm_result["output_filename"]
    output_type = llm_result["output_type"]
    description = llm_result["description"]

    print(f"\n{'='*60}", flush=True)
    print(f"[ATTEMPT 1] Executing code for prompt: {request.prompt}", flush=True)
    print(f"[ATTEMPT 1] Output filename: {output_filename}", flush=True)
    print(f"{'='*60}", flush=True)

    execution_result = run_code_in_sandbox(code, output_filename)

    print(f"[ATTEMPT 1] Success: {execution_result['success']}", flush=True)
    if not execution_result["success"]:
        print(f"[ATTEMPT 1] Error:\n{execution_result['error']}", flush=True)

    # retry once if execution fails
    if not execution_result["success"]:
        retry_context = f"Previous attempt failed with this error:\n{execution_result['error']}\n\nFix the code and try again."

        print(f"\n{'='*60}", flush=True)
        print(f"[RETRY] Sending back to LLM with prompt:", flush=True)
        print(f"Original prompt: {request.prompt}", flush=True)
        print(f"Retry context:\n{retry_context}", flush=True)
        print(f"{'='*60}", flush=True)

        try:
            llm_result = generate_code(request.prompt, retry_context)
            code = llm_result["code"]
            output_filename = llm_result["output_filename"]
            output_type = llm_result["output_type"]
            description = llm_result["description"]

            print(f"[RETRY] New code generated, executing...")
            execution_result = run_code_in_sandbox(code, output_filename)
            print(f"[RETRY] Success: {execution_result['success']}")
            if not execution_result["success"]:
                print(f"[RETRY] Error:\n{execution_result['error']}")
            else:
                print(f"[RETRY] Output produced successfully")
        except Exception as e:
            print(f"[RETRY] LLM call failed: {str(e)}")

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