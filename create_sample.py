import pandas as pd
import os

def create_sample():
    data = {
        'Customer Name': ['John Doe', 'John Doe', 'Jane Smith', 'Bob Wilson'],
        'Phone': ['0123456789', '0123456789', '0987654321', '1122334455'],
        'Product': ['Apple iPhone', 'Case Cover', 'Samsung S23', 'Charger Kabel'],
        'Price': [1200, 25, 950, 15]
    }
    
    df = pd.DataFrame(data)
    file_path = os.path.join(os.getcwd(), "sample_invoices.xlsx")
    df.to_excel(file_path, index=False)
    print(f"Sample file created at: {file_path}")

if __name__ == "__main__":
    create_sample()
