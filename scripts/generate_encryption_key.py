#!/usr/bin/env python3
"""
Generate a secure encryption key for the wallet store.
"""
from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key()
    print("Generated encryption key:")
    print(key.decode())
    print("\nAdd this to your .env file as WALLET_ENCRYPTION_KEY")

