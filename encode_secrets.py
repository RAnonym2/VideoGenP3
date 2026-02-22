import base64
import os

def encode_file(filename):
    if not os.path.exists(filename):
        return f"HIBA: Nincs meg a {filename}!"
        
    with open(filename, "rb") as f:
       
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return encoded

print("\n--- MÁSOLD KI EZEKET A GITHUB SECRETS-BE ---\n")

print("1. SECRET NEVE: GOOGLE_CLIENT_SECRETS_B64")
print("ÉRTÉKE (Másold ki az alatti hosszú sort):")
print(encode_file("client_secrets.json"))

print("\n---------------------------------\n")

print("2. SECRET NEVE: GOOGLE_TOKEN_PICKLE_B64")
print("ÉRTÉKE (Másold ki az alatti hosszú sort):")
print(encode_file("token.pickle"))