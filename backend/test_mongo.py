from pymongo import MongoClient
import certifi

uri = "mongodb+srv://setup:u2eIkhlwU0k5rya8@cluster0.jsdumcm.mongodb.net/sirius?retryWrites=true&w=majority&tls=true"
client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=False, tlsCAFile=certifi.where())
try:
    client.admin.command("ping")
    print("Connection successful")
except Exception as e:
    print(f"Connection failed: {e}")
