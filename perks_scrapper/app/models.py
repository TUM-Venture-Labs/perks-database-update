from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal

class PerkDetails(BaseModel):
    """Structured representation of the extracted perk information."""
    name: Optional[str] = Field(None, description="The official name of the perk or program.")
    description: Optional[str] = Field(None, description="A concise summary of the perk's benefits and purpose.")
    funding_or_credits: Optional[str] = Field(None, description="Details about funding amounts, credits (e.g., AWS credits), or discounts offered.")
    duration: Optional[str] = Field(None, description="The duration of the program or the validity period of the perk.")
    application_deadline: Optional[str] = Field(None, description="The next upcoming application deadline, if applicable.")
    eligibility_criteria: Optional[str] = Field(None, description="Key requirements for startups to qualify for the perk.")
    source_urls: List[HttpUrl] = Field(default_factory=list, description="List of URLs where the information was found.")

class ScrapingDecision(BaseModel):
    """Model's decision on whether to continue scraping or searching."""
    action: Literal['scrape_further', 'search_web', 'aggregate', 'stop'] = Field(..., description="The next action to take based on the current information.")
    relevant_urls_to_scrape: Optional[List[HttpUrl]] = Field(None, description="List of relevant URLs extracted from the current page to scrape next (if action is 'scrape_further'). Only include URLs highly likely to contain perk details.")
    search_query: Optional[str] = Field(None, description="Optimized search query for Exa if action is 'search_web'.")
    reasoning: str = Field(..., description="Brief explanation for the chosen action.")

class AggregatedPerkInfo(BaseModel):
    """Final aggregated information about the perk."""
    record_id: str
    initial_url: HttpUrl
    updated_details: PerkDetails = Field(..., description="The aggregated and most up-to-date perk details found.")
    status: Literal['updated', 'needs_review', 'error'] = Field(..., description="Status of the update process.")
    message: Optional[str] = Field(None, description="Any relevant messages or error details.")

class PerkUpdateRequest(BaseModel):
    """Request model for the API endpoint."""
    airtable_record_id: str = Field(..., description="The ID of the Airtable record to process.")

# Potential model for Airtable interaction (can be expanded)
class AirtableRecord(BaseModel):
    id: str
    url: HttpUrl
    current_description: Optional[str] = None
    # Add other fields as needed based on AIRTABLE_*_FIELD env vars 