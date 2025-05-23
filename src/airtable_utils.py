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
def update_perks_info(table, scraped_info, entries_to_update):
    print(f"\n{'-' * 75}\nUpdating perks info on Airtable...\n{'-' * 75}")
    results = {}
    
    for record_id, record_info in scraped_info.items():
        # Initialize result entry for this record
        results[record_id] = {}
        
        try:
            # Get the fields from the record_info
            record_fields = record_info.get("fields", {})
            
            # Create the fields dict by looping over keys in record_fields
            fields = {}
            for key, value in record_fields.items():
                if key in entries_to_update:
                    # Skip problematic values that Airtable can't parse
                    if value in ["Not found", None]:
                        pass

                    else:
                        if key == "Value":
                            # Convert to float first to handle decimal values, then to int if it's a whole number
                            fields[key] = int(value) 
                    
                        else:
                            # Handle other fields
                            if value is not None:
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


# updates fields on airtable with the info extracted from crawling (perk description, value, etc)
def update_funding_info(table, scraped_info, entries_to_update):
    print(f"\n{'-' * 75}\nUpdating funding info on Airtable...\n{'-' * 75}")
    results = {}
    
    for record_id, record_info in scraped_info.items():
        # Initialize result entry for this record
        results[record_id] = {}
        
        try:
            # Get the fields from the record_info
            record_fields = record_info.get("fields", {})
            
            # Create the fields dict by looping over keys in record_fields
            fields = {}
            for key, value in record_fields.items():
                if key in entries_to_update:
                    # Skip problematic values that Airtable can't parse
                    if value in ["Not found", None]:
                        pass

                    else:
                        if key == "Funding amount":
                            # Convert to float first to handle decimal values, then to int if it's a whole number
                            fields[key] = int(value) 
                        elif key in ["Industry focus", "EXIST phase", "Region", "Target group", "Program duration"]:
                            pass
                    
                        else:
                            # Handle other fields
                            if value is not None:
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