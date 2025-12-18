"""
Phoenix Protocol - Context Wallet Store

Local-first encrypted storage for Memory Cards.
"""
import sqlite3
import json
from typing import List, Optional
from datetime import datetime
from cryptography.fernet import Fernet
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Try both import paths (for local dev vs Docker)
try:
    from app.models.memory_card import MemoryCard
except ImportError:
    from router.app.models.memory_card import MemoryCard


class WalletStore:
    """Encrypted local storage for Memory Cards."""
    
    def __init__(self, db_path: str, encryption_key: str):
        # Resolve to absolute path
        if not os.path.isabs(db_path):
            # If relative, resolve from project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            self.db_path = os.path.join(project_root, db_path)
        else:
            self.db_path = db_path
        
        # Ensure encryption key is valid Fernet key (32 bytes base64-encoded)
        # If it's not, generate one from the provided key
        try:
            # Try to use the key directly
            self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        except Exception:
            # If key is invalid, derive a valid Fernet key from it
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            import base64
            
            # Derive a key from the provided string
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'phoenix_wallet_salt',  # Fixed salt for consistency
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key))
            self.cipher = Fernet(key)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the wallet database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_cards (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                domain TEXT NOT NULL,
                priority TEXT NOT NULL,
                text_encrypted TEXT NOT NULL,
                tags TEXT NOT NULL,
                persona TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_card(self, card: MemoryCard) -> MemoryCard:
        """Add a memory card to the wallet."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Encrypt the text
        encrypted_text = self.cipher.encrypt(card.text.encode()).decode()
        
        cursor.execute("""
            INSERT OR REPLACE INTO memory_cards 
            (id, type, domain, priority, text_encrypted, tags, persona, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            card.id,
            card.type,
            json.dumps(card.domain),
            card.priority,
            encrypted_text,
            json.dumps(card.tags),
            card.persona,
            card.created_at.isoformat(),
            datetime.utcnow().isoformat() if card.updated_at else None
        ))
        
        conn.commit()
        conn.close()
        return card
    
    def get_cards(self, persona: str = "Personal", domain: Optional[str] = None) -> List[MemoryCard]:
        """Retrieve memory cards, optionally filtered by persona and domain."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM memory_cards WHERE persona = ?"
        params = [persona]
        
        if domain:
            query += " AND domain LIKE ?"
            params.append(f'%"{domain}"%')
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        cards = []
        for row in rows:
            # Decrypt text
            decrypted_text = self.cipher.decrypt(row[4].encode()).decode()
            
            cards.append(MemoryCard(
                id=row[0],
                type=row[1],
                domain=json.loads(row[2]),
                priority=row[3],
                text=decrypted_text,
                tags=json.loads(row[5]),
                persona=row[6],
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8]) if row[8] else None
            ))
        
        return cards
    
    def get_card(self, card_id: str) -> Optional[MemoryCard]:
        """Get a specific memory card by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, type, domain, priority, text_encrypted, tags, persona, created_at, updated_at
            FROM memory_cards
            WHERE id = ?
        """, (card_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Decrypt text
        decrypted_text = self.cipher.decrypt(row[4].encode()).decode()
        
        return MemoryCard(
            id=row[0],
            type=row[1],
            domain=json.loads(row[2]),
            priority=row[3],
            text=decrypted_text,
            tags=json.loads(row[5]),
            persona=row[6],
            created_at=datetime.fromisoformat(row[7]),
            updated_at=datetime.fromisoformat(row[8]) if row[8] else None
        )
    
    def delete_card(self, card_id: str) -> bool:
        """Delete a memory card."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM memory_cards WHERE id = ?", (card_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted

