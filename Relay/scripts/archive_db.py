import sqlite3
import pandas as pd
import os
import sys

def convert_db_to_excel(db_path, excel_path):
    """
    Converts a SQLite database to an Excel file.
    
    Args:
        db_path (str): Path to the SQLite database.
        excel_path (str): Path to the output Excel file.
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        
        # Create Excel writer object
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Export 'emails' table
            try:
                emails_df = pd.read_sql_query("SELECT * FROM emails", conn)
                emails_df.to_excel(writer, sheet_name='emails', index=False)
                print(f"Exported {len(emails_df)} rows from 'emails' table.")
            except Exception as e:
                print(f"Error reading 'emails' table: {e}")

            # Export 'attachments' table
            try:
                attachments_df = pd.read_sql_query("SELECT * FROM attachments", conn)
                attachments_df.to_excel(writer, sheet_name='attachments', index=False)
                print(f"Exported {len(attachments_df)} rows from 'attachments' table.")
            except Exception as e:
                print(f"Error reading 'attachments' table: {e}")
        
        conn.close()
        print(f"Successfully created '{excel_path}'")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 archive_db.py <db_file> <excel_file>")
        sys.exit(1)

    db_file = sys.argv[1]
    excel_file = sys.argv[2]
    convert_db_to_excel(db_file, excel_file)
