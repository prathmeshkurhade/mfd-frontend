import os
import jwt
from dotenv import load_dotenv

load_dotenv()

token = "eyJhbGciOiJFUzI1NiIsImtpZCI6ImUzYmMzZDQ2LWQ5OTktNGQyMy1iZGQzLTdmNWU3OTg1Nzc0ZiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3doamdtYnB0bmxzeHN3ZWhsZmhxLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI1Njc5NTBkOS03YTQ0LTQ3NmQtYjM0NC1jNWU0OGI3MjJiZDEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcxODQ0MjE2LCJpYXQiOjE3NzE4NDA2MTYsImVtYWlsIjoiYWRpdHlhLmNvZGVzMTIzQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzcxODQwNjE2fV0sInNlc3Npb25faWQiOiJkN2JhYjJiNS00YWYzLTQzZTktOGVmMC03MGY5N2ZhYThjYmMiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.AM0HwCx4njUPJLLll42hsOdoMtavK2RI2GHs_gsUVAPwXW7jRP1qA96olJSV8rOAnxTm-V4heSjXhNVtgKhajQ"

# Check the token header to see the algorithm
header = jwt.get_unverified_header(token)
print(f"Token algorithm: {header['alg']}")
print(f"Token header: {header}")

# Try with the correct algorithm
secret = os.getenv("SUPABASE_JWT_SECRET")
print(f"\nJWT Secret (first 10 chars): {secret[:10]}...")

try:
    payload = jwt.decode(
        token,
        secret,
        algorithms=[header['alg']],
        audience="authenticated"
    )
    print("✅ Token verified successfully!")
except Exception as e:
    print(f"❌ Failed: {e}")

# If HS256 fails, try without audience
print("\n--- Try without audience ---")
try:
    payload = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        options={"verify_aud": False}
    )
    print("✅ Token verified (no audience check)!")
except Exception as e:
    print(f"❌ Failed: {e}")