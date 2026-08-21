import os
import json
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are a code generation engine. 
The user will give you a task. Your job is to write Python code that accomplishes it and produces an output file.

You MUST respond with ONLY a valid JSON object — no explanation, no markdown, no backticks.

The JSON must follow this exact schema:
{
  "code": "<complete python code as a string>",
  "output_filename": "<the exact filename the code saves output to>",
  "output_type": "<one of: image, audio, pdf, csv, text>",
  "description": "<one sentence describing what was produced>"
}

Rules for the code:
- The code must save its output to a file in the current working directory
- Use only these libraries: matplotlib, pandas, numpy, pydub, reportlab, Pillow, scipy, seaborn
- For charts: use matplotlib, save as 'output.png' using plt.savefig('output.png')
- For audio: use pydub, save as 'output.mp3'
- For PDFs: use reportlab, save as 'output.pdf'
- For data/tables: use pandas, save as 'output.csv'
- Do NOT use plt.show() — only savefig()
- Do NOT read any external files
- Do NOT make any network requests
- The code must be completely self-contained
"""


def generate_code(prompt: str, context: str = "") -> dict:
    """
    Sends the user prompt to Gemini.
    Returns parsed JSON: { code, output_filename, output_type, description }
    """

    user_message = prompt
    if context:
        user_message += f"\n\nAdditional context:\n{context}"

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=user_message,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "temperature": 0.2,       # lower = more deterministic code output
        }
    )

    raw = response.text.strip()

    # strip markdown fences if Gemini wraps in ```json
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    parsed = json.loads(raw)

    # validate required keys
    required = ["code", "output_filename", "output_type", "description"]
    for key in required:
        if key not in parsed:
            raise ValueError(f"LLM response missing key: {key}")

    return parsed