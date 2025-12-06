import pandas as pd

# 1. Load Data
df = pd.read_csv(r'c:\degitpla\Online_Retail.csv', encoding='ISO-8859-1')

# 2. Standard Cleaning (Your Steps)
df = df.drop_duplicates()
df = df.dropna(subset=['CustomerID'])
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

# 3. CRITICAL MISSING STEPS (Added for Objective 5)
# Remove Returns (Negative Quantity) and Errors (Zero UnitPrice)
df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]

# Remove Faulty Product Codes (Postage, Manual, etc.)
faulty_codes = ['POST', 'D', 'DOT', 'M', 'S', 'AMAZONFEE', 'm',
                'DCGSSBOY', 'DCGSSGIRL', 'PADS', 'B', 'CRUK', 'BANK CHARGES']
df = df[~df['StockCode'].isin(faulty_codes)]

# 4. Feature Engineering
df['TotalPrice'] = df['Quantity'] * df['UnitPrice']

# 5. Verify & Save
print("Final Shape:", df.shape)
print("Missing Values:", df.isnull().sum().sum())
print("Negative Quantities:", (df['Quantity'] <= 0).sum())

df.to_csv(r'c:\degitpla\Online_Retail_Cleaned.csv', index=False)
print("Cleaned data saved to Online_Retail_Cleaned.csv")