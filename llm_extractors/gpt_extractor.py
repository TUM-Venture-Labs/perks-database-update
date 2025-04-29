import re
import json
from openai import OpenAI
import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

def gpt_extract_info(text):
    # Detect if scraping was blocked
    blocked_keywords = ["blocked", "access denied", "forbidden", "403", "captcha", "not authorized"]
    was_blocked = any(keyword.lower() in text.lower() for keyword in blocked_keywords)

    # Adjust the prompt based on whether blocked
    if was_blocked:
        # If blocked, force all fields to "Blocked"
        return {
            "Brief description of the provider": "Blocked",
            "What you get": "Blocked",
            "How to get it": "Blocked",
            "Value": "Blocked"
        }

    prompt = f"""
You are an information extraction assistant.

Given the text below, extract the following fields:

- "Provider Description": A very brief (1-2 sentences) description of the company or organization offering the perk.
- "What You Get": Summarize clearly what the perk provides (discount, credits, service, etc.).
- "How To Get It": Instructions on how someone can claim or access the perk.
- "Money Value": The financial value of the perk (in USD or EUR if available). If no value is clear, return "Not found".

**Important rules**:
- Do not invent missing information.
- If a field cannot be found, respond exactly with "Not found".
- Output only valid JSON, no commentary.

Text to analyze:
\"\"\"
{text}
\"\"\"

Respond in this exact JSON format:
{{
    "Brief description of the provider": "",
    "What you get": "",
    "How to get it": "",
    "Value": ""
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    
    content = response.choices[0].message.content.strip()
    
    # Extract the JSON part only
    try:
        json_str = re.search(r"\{.*\}", content, re.DOTALL).group()
        extracted = json.loads(json_str)
    except Exception as e:
        print(f"⚠️ Parsing error: {e}")
        extracted = {
            "Brief description of the provider": "Error parsing",
            "What you get": "Error parsing",
            "How to get it": "Error parsing",
            "Value": "Error parsing"
        }
    
    return extracted
