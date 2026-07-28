from dotenv import load_dotenv
import os

load_dotenv()
key = os.getenv('TOGETHER_API_KEY')

if key:
    print("SUCCESS: API Key loaded from .env")
    print(f"Key preview: ...{key[-8:]}")
    print(f"Key length: {len(key)}")
else:
    print("ERROR: API Key NOT found in .env")
    print("Please add TOGETHER_API_KEY=your_key_here to .env file")

