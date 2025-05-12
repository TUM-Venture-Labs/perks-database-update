from .models import PerkDetails, ScrapingDecision

# --- Developer Messages for OpenAI Responses API ---

DEV_MSG_EXTRACT_PERK = f"""
Extract structured information about the startup perk based on the provided text.
Focus on details like name, description, funding/credits, duration, deadlines, and eligibility.
Output should conform to the PerkDetails model.
"""

DEV_MSG_DECIDE_NEXT_STEP = f"""
Analyze the currently gathered perk information, the original description (if available), and the content of the last scraped page.
Decide the next best action: scrape relevant links further, perform a web search for more/recent info, aggregate the findings, or stop if enough info is gathered or depth limit is reached.
Consider the relevance of extracted links. Only suggest scraping URLs highly likely to contain specific perk details (avoid generic links like 'contact us', 'blog', 'careers').
Output should conform to the ScrapingDecision model.
"""

DEV_MSG_AGGREGATE_INFO = f"""
Synthesize all collected information from multiple sources (initial scrape, recursive scrapes, web search results) into a single, consolidated PerkDetails object.
Prioritize the most specific and recent information. Resolve conflicting details reasonably.
Output should conform to the PerkDetails model.
"""

# --- User Messages (Templates) ---

USER_MSG_EXTRACT_PERK_TEMPLATE = """
Please extract the perk details from the following content scraped from {url}:

```markdown
{scraped_content}
```
"""

USER_MSG_DECIDE_NEXT_STEP_TEMPLATE = """
Original Perk Description (from database): {original_description}

Information Gathered So Far:
{gathered_info_json}

Content from last scraped URL ({last_scraped_url}):
```markdown
{last_scraped_content}
```

Based on this, what is the next step? Current depth: {current_depth}/{max_depth}. Web search performed: {search_performed}.
"""

USER_MSG_AGGREGATE_INFO_TEMPLATE = """
Please aggregate the following information about the perk from different sources into a single summary.

Initial Data:
{initial_data_json}

Scraped Data:
{scraped_data_list_json}

Web Search Results:
{search_results_json}
""" 