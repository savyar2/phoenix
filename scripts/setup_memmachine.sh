#!/bin/bash
# Setup script for MemMachine integration with Phoenix Protocol

echo "🧠 Setting up MemMachine for Phoenix Protocol..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY environment variable not set."
    echo "   MemMachine requires an OpenAI API key for language models."
    echo "   You can:"
    echo "   1. Set it now: export OPENAI_API_KEY=your-key-here"
    echo "   2. Or provide it during MemMachine setup"
    echo ""
    read -p "Do you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create temporary directory for MemMachine
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

echo "📥 Downloading MemMachine..."
echo ""

# Get the latest release URL
TARBALL_URL=$(curl -s https://api.github.com/repos/MemMachine/MemMachine/releases/latest \
  | grep '"tarball_url"' \
  | head -n 1 \
  | sed -E 's/.*"tarball_url": "(.*)",/\1/')

if [ -z "$TARBALL_URL" ]; then
    echo "❌ Failed to get MemMachine release URL"
    exit 1
fi

# Download the tarball
curl -L "$TARBALL_URL" -o MemMachine-latest.tar.gz

if [ ! -f MemMachine-latest.tar.gz ]; then
    echo "❌ Failed to download MemMachine"
    exit 1
fi

# Extract the archive
echo "📦 Extracting MemMachine..."
tar -xzf MemMachine-latest.tar.gz

# Find the extracted directory
EXTRACTED_DIR=$(find . -maxdepth 1 -type d -name "MemMachine-*" | head -n 1)

if [ -z "$EXTRACTED_DIR" ]; then
    echo "❌ Failed to extract MemMachine"
    exit 1
fi

cd "$EXTRACTED_DIR"

echo ""
echo "🚀 Starting MemMachine installation..."
echo "   This will guide you through the setup process."
echo "   You'll be prompted to enter your OpenAI API key."
echo ""

# Run the setup script
if [ -f "./memmachine-compose.sh" ]; then
    chmod +x ./memmachine-compose.sh
    ./memmachine-compose.sh
else
    echo "❌ Setup script not found in MemMachine directory"
    exit 1
fi

echo ""
echo "✅ MemMachine setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Verify MemMachine is running: curl http://localhost:8080/health"
echo "2. Add to your .env file:"
echo "   MEMMACHINE_ENABLED=true"
echo "   MEMMACHINE_BASE_URL=http://localhost:8080"
echo "   MEMMACHINE_API_KEY="
echo "3. Install Python client: cd router && pip install memmachine-client"
echo "4. Test integration: curl http://localhost:8787/api/memmachine/health"
echo ""
echo "📚 For more information, see: docs/MEMMACHINE-SETUP.md"

