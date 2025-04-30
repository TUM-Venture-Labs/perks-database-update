from pyairtable import Table
import config

# Initialize Airtable table connection once
table = Table(
    config.AIRTABLE_API_KEY,
    config.AIRTABLE_BASE_ID,
    config.AIRTABLE_TABLE_ID
)

# extracts all rows from airtable
def get_records():
    """
    Fetches all records from the Airtable table.

    Returns:
        list: List of records from Airtable.
    Raises:
        Exception: If fetching records fails.
    """
    try:
        print("Connecting to Airtable...")
        records = table.all()
        print(f"Successfully fetched {len(records)} records.")
        return records
    except Exception as e:
        print("ERROR fetching records from Airtable:")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print("Response Status Code:", e.response.status_code)
            print("Response Body:", e.response.text)
        raise

# updates only the status of the perks (active or inactive/broken)
def update_record(record_id, fields):
    """
    Updates a record in the Airtable table.

    Args:
        record_id (str): The ID of the record to update.
        fields (dict): The fields to update.
    """
    try:
        print(f"Updating record with ID: {record_id}")

        # If fields is a BaseModel, convert to dict
        if hasattr(fields, "model_dump"):
            fields = fields.model_dump()

        # Now update Airtable
        table.update(record_id, fields)

        print(f"OK: Record {record_id} updated successfully.")
    except Exception as e:
        print("ERROR: updating record in Airtable:")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print("Response Status Code:", e.response.status_code)
            print("Response Body:", e.response.text)
        raise

# updates fields on airtable with the info extracted from crawling (perk description, value, etc)
def update_perks_info(scraped_info):
    """
    Updates Airtable with scraped perk information.
    
    Args:
        scraped_info (dict): Dictionary with company names as keys and perk info dictionaries as values
    
    Returns:
        dict: Results with status of each update operation
    """
    print(f"\n{'-' * 75}\nUpdating perks info on Airtable...\n{'-' * 75}")
    results = {}
    
    for company_name, perk_info in scraped_info.items():
        try:
            # Search for existing record
            records = table.all(formula=f"{{Name}}='{company_name}'")
            
            # Map the fields to Airtable column names
            fields = {
                "Name": company_name,
                "Brief description of the provider": perk_info["Brief description of the provider"],
                "What you get": perk_info["What you get"],
                "How to get it": perk_info["How to get it"]
            }
            
            # Only add Value if it contains numbers and is not "Not found"
            value = perk_info.get("Value", "")
            if value != "Not found" and any(char.isdigit() for char in value):
                # Extract only the digits and convert to number
                import re
                numeric_value = re.findall(r'\d+', value)
                if numeric_value:
                    # Join and convert to number (handles cases like "1,000")
                    fields["Value"] = float(''.join(numeric_value))
            
            if records:
                # Update existing record
                record_id = records[0]['id']
                update_record(record_id, fields)
                results[company_name] = "updated"
            else:
                # Create new record
                table.create(fields)
                results[company_name] = "created"
                
        except Exception as e:
            results[company_name] = f"error: {str(e)}"
    
    return results