from pyairtable import Table
import config
import re

from datetime import datetime




# extracts all rows from airtable
def get_records(table):
    """
    Fetches all records from the Airtable table.
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


# updates fields on airtable with the info extracted from crawling (perk description, value, etc)
def update_perks_info(table, scraped_info):
    print(f"\n{'-' * 75}\nUpdating perks info on Airtable...\n{'-' * 75}")
    results = {}
    
    for record_id, record_info in scraped_info.items():
        # Initialize result entry for this record
        results[record_id] = {}
        
        try:
            # Map the fields to Airtable column names
            fields = {
                "Status": record_info.get("fields", {}).get("Status", ""),
                "Name": record_info.get("fields", {}).get("Name", ""),
                "Brief description of the provider": record_info.get("fields", {}).get("Brief description of the provider"),
                "What you get": record_info.get("fields", {}).get("What you get"),
                "How to get it": record_info.get("fields", {}).get("How to get it"),
                "Last edited time": datetime.now().strftime("%Y-%m-%d")
            }
            
            # Check if the Value field exists in the original record
            value_field = record_info.get("fields", {}).get("Value")
            if value_field is not None:
                fields["Value"] = str(value_field)
            
            # Update existing record
            table.update(record_id, fields)
                
        except Exception as e:
            results[record_id]["error"] = str(e)
            print(f"Failed to update {record_id}: {str(e)}")
    
    return results


# updates fields on airtable with the info extracted from crawling (perk description, value, etc)
def update_funding_info(table, scraped_info):
    print(f"\n{'-' * 75}\nUpdating perks info on Airtable...\n{'-' * 75}")
    results = {}
    
    for record_id, record_info in scraped_info.items():
        # Initialize result entry for this record
        results[record_id] = {}
        
        try:
            # Get the fields from the record_info
            record_fields = record_info.get("fields", {})
            
            # Create the fields dict by looping over keys in record_fields
            # This automatically maps field names to Airtable columns with the same name
            fields = {}
            for key, value in record_fields.items():
                # Handle the Value field specially if needed
                if key == "Attachment Summary" and value is not None:
                    fields[key] = str(value)
                else:
                    fields[key] = value
            
            # Add the Last edited time field
            fields["Last edited time"] = datetime.now().strftime("%Y-%m-%d")
            
            # Update existing record
            table.update(record_id, fields)
            
        except Exception as e:
            results[record_id]["error"] = str(e)
            print(f"Failed to update {record_id}: {str(e)}")
    
    return results