import re
import os
import json
import time
import requests
from typing import Dict
from langfuse import Langfuse
langfuse = Langfuse()
from langfuse.openai import OpenAI

import config
from src.gpt_extractor import extract_with_gpt
import src.utils 

os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["PERPLEXITY_API_KEY"] = config.PERPLEXITY_API_KEY
# get keys for your project from https://cloud.langfuse.com
os.environ["LANGFUSE_PUBLIC_KEY"] = config.LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_SECRET_KEY"] = config.LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_HOST"] = config.LANGFUSE_HOST
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY

############# Handle printing
def print_perks(perks):
    if perks is None:  
        print("Error: Data is None. No data to display.")
        return 
    
    for key, value in perks.items():
        line = f"{key}: {value}"
        print(f'{line[:100]}')  


def extract_with_perplexity(url, name, gpt_info, gpt_prompt):

    print("\nAnalysing with method 2 - There is still missing info. Running Perplexity prompt...")

    # run perplexity search
    info_perplexity = run_perplexity_search(url, name, gpt_prompt)
    #print_perks(info_perplexity)

    # combine additional information from perplexity with the one we already had from ChatGPT
    if info_perplexity:

        # Combine the information from GPT and Perplexity
        print("\nCombining information from GPT and Perplexity...")
        final_info =  enrich_with_perplexity(gpt_info, info_perplexity, gpt_prompt)

        #src.utils.print_perks(final_info)
        #print("\n")

        return final_info


def convert_to_json_schema(field_descriptions):
    properties = {}
    required = []
    for field, desc in field_descriptions.items():
        if desc.lower().startswith('string'):
            field_type = 'string'
        elif desc.lower().startswith('number'):
            field_type = 'number'
        else:
            field_type = 'string'
        properties[field] = {"type": field_type, "description": desc}
        required.append(field)
    return {
        "type": "object",
        "properties": properties,
        "required": required
    }


def run_perplexity_search(url, name, gpt_prompt):    
    # 1. Get your schema dictionary from gpt_prompt
    field_descriptions = gpt_prompt.config["json_schema"]

    # 2. Build proper JSON Schema structure
    properties = {}
    for field_name, description in field_descriptions.items():
        # Convert string descriptions to proper JSON Schema format
        if "number" in description.lower():
            properties[field_name] = {
                "type": "number",
                "description": description
            }
        else:
            properties[field_name] = {
                "type": "string", 
                "description": description
            }
    
    perplexity_json_schema = {
        "schema": {
            "type": "object",
            "properties": properties,
            "required": list(field_descriptions.keys())
        }
    }
        
    try:
        # 3. Prepare the payload
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a research assistant that finds detailed, factual information about startup perks, discounts, and special offers. "
                        "Be concise keeping each field to 1 to 2 sentences maximum. "
                        "Respond only with valid JSON, no extra text."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Research this URL: {url} and find current information about: {name}\n\n"
                        "Focus on German startup ecosystem offers from XPRENEURS, XPLORE, TechFounders, TUM Venture Labs, UVC, or public programs.\n"
                        "If information is missing, write \"Not found\".\n"
                        "Return only valid JSON matching the schema."
                    )
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": perplexity_json_schema
            }
        }

        # 4. Send the request
        headers = {
            "Authorization": f"Bearer {os.environ['PERPLEXITY_API_KEY']}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions", 
            json=payload, 
            headers=headers,
            timeout=60
        )
        
        # Check if request was successful
        if response.status_code != 200:
            print(f"API Error {response.status_code}: {response.text}")
            return {}
        
        # Get the response content
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]

        # Parse JSON response
        try:
            # Clean content if needed
            clean_content = content.strip()
            
            # Remove code blocks if present
            if clean_content.startswith("```"):
                clean_content = re.sub(r'```[a-z]*\n?', '', clean_content)
                clean_content = clean_content.replace('```', '')
            
            # Try to extract JSON object
            json_match = re.search(r'(\{.*\})', clean_content, re.DOTALL)
            if json_match:
                clean_content = json_match.group(1)
            
            # Parse JSON
            content_dict = json.loads(clean_content)
            print("Successfully extracted information with Perplexity.\n")
            return content_dict
            
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Failed content: {repr(clean_content)}")
            return {}

    except Exception as e:
        print(f"Error with Perplexity search: {e}")
        return {}


def enrich_with_perplexity(json_gpt, json_perplexity, gpt_prompt):
    
    try:
        langfuse = Langfuse()
        client = OpenAI()

        # Get current `production` version of a text prompt
        prompt = langfuse.get_prompt("join_chat_gpt_perplexity_answers")
        
        # Config handling with defaults
        if not prompt.config:
            prompt.config = {
                "model": "gpt-4.1-nano",
                "temperature": 0
            }

        model = prompt.config["model"]
        temperature = prompt.config["temperature"]
        
        # Stringify the JSON schema
        json_schema_str = ', '.join([f"'{key}': {value}" for key, value in gpt_prompt.config["json_schema"].items()])
        json_perplexity_str = ', '.join([f"'{key}': {value}" for key, value in json_perplexity.items()])
        json_gpt_str    = ', '.join([f"'{key}': {value}" for key, value in json_gpt.items()])

        # Insert variables into prompt template
        compiled_prompt = prompt.compile(
            json_gpt=json_gpt_str, 
            json_perplexity=json_perplexity_str, 
            json_schema = json_schema_str
        )
        
        # Format as OpenAI messages
        messages = [
            {"role":"system","content": compiled_prompt},
            {"role":"user","content":compiled_prompt}
        ]
        
        # Execute LLM call
        res = client.chat.completions.create(
            model       = model,
            temperature = temperature,
            messages    = messages,
            response_format = { "type": "json_object" },
            langfuse_prompt = prompt # capture used prompt version in trace
        )
        
        # Parse response as JSON
        res = json.loads(res.choices[0].message.content)
        
        # Extract the JSON part
        try:
            return res
        except Exception as e:
            print(f"⚠️ Parsing error during enrichment: {e}")
            return json_gpt
    except Exception as e:
        print(f"Error enriching with Perplexity data: {e}")
        return json_perplexity

