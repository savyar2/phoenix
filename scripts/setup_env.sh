#!/bin/bash
# Setup script for Phoenix Protocol Phase 1

echo "🔥 Setting up Phoenix Protocol Phase 1..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your actual values."
else
    echo "⚠️  .env file already exists. Skipping..."
fi

# Generate encryption key if not set
if ! grep -q "WALLET_ENCRYPTION_KEY=" .env || grep -q "your-encryption-key-here" .env; then
    echo "Generating encryption key..."
    ENCRYPTION_KEY=$(python3 scripts/generate_encryption_key.py | grep -v "Generated" | grep -v "Add this")
    sed -i.bak "s/WALLET_ENCRYPTION_KEY=.*/WALLET_ENCRYPTION_KEY=${ENCRYPTION_KEY}/" .env
    rm .env.bak 2>/dev/null || true
    echo "✅ Encryption key generated and added to .env"
fi

echo ""
echo "📝 Next steps:"
echo "1. Edit .env with your Neo4j credentials"
echo "2. (Optional) Set up MemMachine: bash scripts/setup_memmachine.sh"
echo "3. Set up Python virtual environment: cd router && python3 -m venv venv"
echo "4. Install dependencies: source venv/bin/activate && pip install -r requirements.txt"
echo "5. Run the router: uvicorn app.main:app --reload --host 127.0.0.1 --port 8787"
echo ""
echo "✅ Setup complete!"
echo ""
echo "💡 Tip: See RUNNING.md for complete setup instructions including Docker Compose option."

