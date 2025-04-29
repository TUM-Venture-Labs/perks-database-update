# airtable_utils.py

from pyairtable import Table
import config

# Initialize Airtable table connection once
table = Table(
    config.AIRTABLE_API_KEY,
    config.AIRTABLE_BASE_ID,
    config.AIRTABLE_TABLE_ID
)

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

        print(f"✅ Record {record_id} updated successfully.")
    except Exception as e:
        print("❌ Error updating record in Airtable:")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print("Response Status Code:", e.response.status_code)
            print("Response Body:", e.response.text)
        raise
