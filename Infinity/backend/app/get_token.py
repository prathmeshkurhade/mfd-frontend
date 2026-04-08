import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Create a test user (only once)
try:
    response = supabase.auth.sign_up({
        "email": "aditya.codes123@gmail.com",
        "password": "test123"
    })
    print("User created!")
except Exception as e:
    print(f"User might already exist: {e}")

# Sign in and get token
response = supabase.auth.sign_in_with_password({
    "email": "aditya.codes123@gmail.com",
    "password": "test123"
})

token = response.session.access_token
print("\n🔑 Your JWT Token:")
print(token)
print("\n📋 Copy this and use in Swagger UI!")