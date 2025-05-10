import re
import os
import json
import requests
from typing import Dict

import config
from src.gpt_extractor import extract_with_gpt
from src.utils import print_perks

os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["PERPLEXITY_API_KEY"] = config.PERPLEXITY_API_KEY


def extract_perk_info_perplexity(url, perk_name, gpt_info):

    print("\nAnalysing with method 2 - There is still missing info. Running Perplexity prompt...")

    # run perplexity search
    info_perplexity = run_perplexity_search(url, perk_name)
    print_perks(info_perplexity)
    print("\n")

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
        final_info =  enrich_with_perplexity(gpt_perplexity_info, info_perplexity)

        print_perks(final_info)
        print("\n")

        return final_info


def run_perplexity_search(url, perk_name):

    try:
        
        url = "https://api.perplexity.ai/chat/completions"
        api_key = os.environ["PERPLEXITY_API_KEY"]
        
        # define the prompt for perplexity which extracts structured information
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a research assistant that finds detailed, factual information about startup perks, discounts, and special offers. "
                        "Focus on the German startup ecosystem (XPRENEURS, XPLORE, TechFounders, TUM Venture Labs, UVC, public programs). "
                        "Always answer in pure JSON (no markdown or commentary), and keep each field to 1–2 sentences maximum."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Search online for the most current, factual information about the following startup perk in the German ecosystem:\n"
                        f"\"{perk_name}\"\n\n"
                        "Focus on perks offered by organizations such as XPRENEURS, XPLORE, TechFounders, TUM Venture Labs, UVC, or relevant public programs.\n"
                        f"Do NOT use the information from this URL, but use it as a reference for the level of detail:\n"
                        f"{url}\n\n"
                        "Respond in this exact JSON format:\n"
                        "{{\n"
                        "    \"Brief description of the provider\": \"\",\n"
                        "    \"What you get\": \"\",\n"
                        "    \"How to get it\": \"\",\n"
                        "    \"Value\": \"\"\n"
                        "}}\n"
                        "Rules:\n"
                        "- Use 1-2 sentences per field.\n"
                        "- Do not invent missing information; if you can not find a field, use \"Not found\".\n"
                        "- Return only valid JSON, no commentary, no code blocks, no explanations."
                        "- The \"Value\" field must be a monetary value the startup gets, not text."
                    )
                }
            ]
        }


        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # run request using Perplexity
        response = requests.request("POST", url, json=payload, headers=headers)
        content = response.json()["choices"][0]["message"]["content"]

        try:
            content_dict = json.loads(content)
        except json.JSONDecodeError:
            content_dict = {}

        return content_dict

    except Exception as e:
        print(f"Error with Perplexity search: {e}")
        return ""


def enrich_with_perplexity(info_gpt: Dict[str, str], info_perplexity: str) -> Dict[str, str]:

    if not info_perplexity:
        return info_gpt
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        prompt = f"""
        You are a data enrichment assistant. Use the additional web information to improve or complete the initial company perk data.

        Initial data:
        {json.dumps(info_gpt, indent=2)}

        Additional information:
        {json.dumps(info_perplexity, indent=2)}

        ### Instructions
        Update initial JSON fields as follows:
        - Replace "Not found" with relevant info from additional data
        - Update existing fields with clearer/more detailed info if available
        - Only use explicitly supported information
        - Keep "Not found" when no reliable info exists

        For "Value" fields:
        - Must be a numerical value not text
        - Enter specific monetary amounts if clearly supported
        - Set to 0 for discounts/free benefits with no specific amount 
        - Keep as "Not found" if no relevant info exists
        - Never infer or fabricate values

        Return only the updated valid JSON without commentary.
        """

        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract the JSON part
        try:
            json_str = re.search(r"\{.*\}", content, re.DOTALL).group()
            enriched = json.loads(json_str)
            return enriched
        except Exception as e:
            print(f"⚠️ Parsing error during enrichment: {e}")
            return info_gpt
    except Exception as e:
        print(f"Error enriching with Perplexity data: {e}")
        return info_gpt



