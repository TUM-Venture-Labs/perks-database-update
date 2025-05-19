import re
import os
import json
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


def extract_with_perplexity(url, perk_name, gpt_info, gpt_prompt):

    print("\nAnalysing with method 2 - There is still missing info. Running Perplexity prompt...")

    # run perplexity search
    info_perplexity = run_perplexity_search(url, perk_name, gpt_prompt)

    # combine additional information from perplexity with the one we already had from ChatGPT
    if info_perplexity:
        # Combine all text for final extraction
        combined_text = (
            json.dumps(gpt_info, indent=2)
            + "\n\nAdditional information from Perplexity search:\n"
            + json.dumps(info_perplexity, indent=2)
        )

        # Re-extract with all available information
        gpt_perplexity_info = extract_with_gpt(combined_text)
        
        # If there are still missing fields, use the enrichment function
        final_info =  enrich_with_perplexity(gpt_perplexity_info, info_perplexity, gpt_prompt)

        src.utils.print_perks(final_info)
        print("\n")

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

    # 2. Convert to valid JSON Schema
    perplexity_json_schema = convert_to_json_schema(field_descriptions)

    try:

        # 3. Prepare the payload
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a research assistant that finds detailed, factual information about startup perks, discounts, and special offers. "
                        "Be concise keeping each field to 1 to 2 sentences maximum."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Combine the information found at this URL: {url} with the most current, factual information from online sources about the following startup perk or funding in the German ecosystem:\n"
                        f"\"{name}\"\n\n"
                        "Focus on offers from XPRENEURS, XPLORE, TechFounders, TUM Venture Labs, UVC, or relevant public programs.\n"
                        "If a field is missing from all sources, write \"Not found\".\n"
                        "Use 1–2 sentences per field. Output only valid JSON matching the provided schema-no commentary, code blocks, or extra text.\n"
                        "The \"Value\" field must be a numeric monetary amount, or \"Not found\"."
                    )

                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": perplexity_json_schema,
            }
        }

        # 4. Send the request
        headers = {
            "Authorization": f"Bearer {os.environ['PERPLEXITY_API_KEY']}",
            "Content-Type": "application/json"
        }
        
        response = requests.post("https://api.perplexity.ai/chat/completions", json=payload, headers=headers)
        content = response.json()["choices"][0]["message"]["content"]


        try:
            # Try to clean the content before parsing as JSON. Sometimes LLMs add extra text before/after JSON
            json_pattern = r'({.*})'
            match = re.search(json_pattern, content, re.DOTALL)
            
            if match:
                clean_content = match.group(1)
            else:
                clean_content = content
                
            content_dict = json.loads(clean_content)
            return content_dict
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Content causing error: {content}")
            # Return empty dict instead of empty string
            return {}

    except Exception as e:
        print(f"Error with Perplexity search: {e}")
        # Return empty dict instead of empty string
        return {}


def enrich_with_perplexity(json_gpt, json_perplexity, gpt_prompt):
    
    try:
        langfuse = Langfuse()
        client = OpenAI()

        # Get current `production` version of a text prompt
        prompt = langfuse.get_prompt("join_chat_gpt_perplexity_answers")

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
            model       = prompt.config["model"],
            temperature = prompt.config["temperature"],
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

