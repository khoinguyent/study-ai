#!/bin/bash

# Study AI - Ollama Model Management Script
# This script helps manage Ollama models for the Study AI platform

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_status() {
    echo -e "${BLUE}📋 $1${NC}"
}

# Check if Ollama container is running
check_ollama() {
    if ! docker ps | grep -q "study-ai-ollama-dev"; then
        print_error "Ollama container is not running. Please start the development environment first:"
        print_warning "  ./scripts/setup-dev.sh"
        exit 1
    fi
    print_success "Ollama container is running"
}

# List available models
list_models() {
    print_header "Available Ollama Models"
    echo "=================================="
    
    response=$(curl -s http://localhost:11434/api/tags)
    model_count=$(echo "$response" | jq '.models | length')
    
    if [ "$model_count" -eq 0 ]; then
        print_warning "No models installed"
        return
    fi
    
    echo "$response" | jq -r '.models[] | "📦 \(.name) (\(.details.parameter_size) - \(.details.quantization_level))"'
    echo ""
    print_success "Found $model_count model(s)"
}

# Download recommended models
download_models() {
    print_header "Downloading Recommended Models for Study AI"
    echo "=================================================="
    
    # Models recommended for Study AI
    models=(
        "llama2:7b-chat"    # Good balance of performance and speed
        "llama2:3b"         # Fast responses for quick interactions
        "mistral:7b-instruct" # Alternative model with good instruction following
    )
    
    for model in "${models[@]}"; do
        print_status "Downloading $model..."
        if docker exec study-ai-ollama-dev ollama pull "$model"; then
            print_success "✅ Downloaded $model"
        else
            print_error "❌ Failed to download $model"
        fi
        echo ""
    done
}

# Test a model
test_model() {
    local model=${1:-"llama2:7b-chat"}
    
    print_header "Testing Model: $model"
    echo "=========================="
    
    # Simple test prompt
    test_prompt="Create a simple quiz question about programming."
    
    print_status "Sending test prompt: '$test_prompt'"
    
    response=$(curl -s -X POST http://localhost:11434/api/generate \
        -d "{\"model\": \"$model\", \"prompt\": \"$test_prompt\", \"stream\": false}")
    
    if echo "$response" | jq -e '.response' > /dev/null; then
        print_success "Model is working!"
        echo ""
        echo "Response:"
        echo "$response" | jq -r '.response' | head -5
        echo "..."
    else
        print_error "Model test failed"
        echo "Response: $response"
    fi
}

# Remove a model
remove_model() {
    local model=$1
    
    if [ -z "$model" ]; then
        print_error "Please specify a model to remove"
        echo "Usage: $0 remove <model_name>"
        exit 1
    fi
    
    print_header "Removing Model: $model"
    echo "=========================="
    
    if docker exec study-ai-ollama-dev ollama rm "$model"; then
        print_success "✅ Removed $model"
    else
        print_error "❌ Failed to remove $model"
    fi
}

# Show model info
model_info() {
    local model=${1:-"llama2:7b-chat"}
    
    print_header "Model Information: $model"
    echo "================================"
    
    response=$(curl -s http://localhost:11434/api/show -d "{\"name\": \"$model\"}")
    
    if echo "$response" | jq -e '.modelfile' > /dev/null; then
        echo "Model Details:"
        echo "$response" | jq -r '.modelfile' | head -10
        echo "..."
    else
        print_error "Could not get model information"
    fi
}

# Main script logic
case "${1:-help}" in
    "list")
        check_ollama
        list_models
        ;;
    "download")
        check_ollama
        download_models
        ;;
    "test")
        check_ollama
        test_model "$2"
        ;;
    "remove")
        check_ollama
        remove_model "$2"
        ;;
    "info")
        check_ollama
        model_info "$2"
        ;;
    "help"|*)
        echo "Study AI - Ollama Model Management"
        echo "=================================="
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  list                    - List all available models"
        echo "  download                - Download recommended models for Study AI"
        echo "  test [model_name]       - Test a specific model (default: llama2:7b-chat)"
        echo "  remove <model_name>     - Remove a specific model"
        echo "  info [model_name]       - Show information about a model"
        echo "  help                    - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 list"
        echo "  $0 download"
        echo "  $0 test llama2:7b-chat"
        echo "  $0 remove llama2:3b"
        echo "  $0 info llama2:7b-chat"
        ;;
esac 