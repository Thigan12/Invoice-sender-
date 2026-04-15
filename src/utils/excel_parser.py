import pandas as pd
import os
from typing import List, Dict

class ExcelParser:
    @staticmethod
    def parse_invoice_data(file_path: str):
        """
        Parses Excel file and returns (DataFrame, error_message).
        """
        try:
            # Check if file exists and is not locked
            if not os.path.exists(file_path):
                return pd.DataFrame(), "File does not exist."
                
            df = pd.read_excel(file_path)
            
            if df.empty:
                return pd.DataFrame(), "The selected Excel file is empty."

            # Basic mapping logic (case-insensitive)
            mapping = {
                'customer name': 'Customer Name',
                'name': 'Customer Name',
                'customer': 'Customer Name',
                'phone': 'Phone',
                'number': 'Phone',
                'mobile': 'Phone',
                'product': 'Product',
                'item': 'Product',
                'price': 'Price',
                'amount': 'Price',
                'rate': 'Price'
            }
            
            new_cols = {}
            for col in df.columns:
                clean_col = str(col).lower().strip()
                if clean_col in mapping:
                    new_cols[col] = mapping[clean_col]
            
            df = df.rename(columns=new_cols)
            
            # Ensure required columns exist
            for col in ['Customer Name', 'Phone', 'Product', 'Price']:
                if col not in df.columns:
                    df[col] = None

            # CRITICAL FIX: Forward fill names and phones 
            # (In case the Excel only has the name on the first row of a group)
            df['Customer Name'] = df['Customer Name'].replace('', None).ffill().fillna('Unknown')
            df['Phone'] = df['Phone'].replace('', None).ffill().fillna('')
            
            # Clean data
            df['Customer Name'] = df['Customer Name'].astype(str).str.strip().str.title()
            
            # Professional Phone Cleaning (Handle Excel decimals like 123.0)
            def clean_phone(p):
                p_str = str(p).strip()
                if p_str.endswith('.0'): p_str = p_str[:-2]
                return "".join(filter(str.isdigit, p_str)) # Keep only digits
            
            df['Phone'] = df['Phone'].apply(clean_phone)
            df['Product'] = df['Product'].fillna('Item').astype(str).str.strip()
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
            
            return df, None
        except Exception as e:
            error_msg = str(e)
            if "install openpyxl" in error_msg.lower():
                error_msg = "Please install the 'openpyxl' library to read .xlsx files."
            elif "Permission denied" in error_msg:
                error_msg = "Permission denied. Please close the Excel file if it's open in another app."
            return pd.DataFrame(), error_msg

    @staticmethod
    def group_by_customer(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Groups the dataframe by customer name and phone.
        """
        # Ensure name and phone are strings/clean
        df['name'] = df['name'].astype(str).str.strip().str.title()
        df['phone'] = df['phone'].astype(str).str.strip().str.replace('.0', '', regex=False)
        
        groups = {}
        for (name, phone), group in df.groupby(['name', 'phone']):
            key = f"{name}_{phone}"
            groups[key] = group
            
        return groups
