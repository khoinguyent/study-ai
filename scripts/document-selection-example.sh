#!/bin/bash

# Study AI - Document Selection Example Script
# This script demonstrates how to select specific documents for quiz generation

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

# Configuration
API_BASE="http://localhost:8000"
AUTH_TOKEN=""

# Function to get auth token
get_auth_token() {
    print_status "Getting authentication token..."
    
    response=$(curl -s -X POST "$API_BASE/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email": "test@test.com", "password": "test123"}')
    
    if echo "$response" | jq -e '.access_token' > /dev/null; then
        AUTH_TOKEN=$(echo "$response" | jq -r '.access_token')
        print_success "Authentication successful"
    else
        print_error "Authentication failed"
        exit 1
    fi
}

# Function to create a subject
create_subject() {
    local name="$1"
    local description="$2"
    
    print_status "Creating subject: $name"
    
    response=$(curl -s -X POST "$API_BASE/documents/subjects" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$name\", \"description\": \"$description\"}")
    
    if echo "$response" | jq -e '.id' > /dev/null; then
        local subject_id=$(echo "$response" | jq -r '.id')
        print_success "Subject created with ID: $subject_id"
        echo "$subject_id"
    else
        print_error "Failed to create subject"
        exit 1
    fi
}

# Function to create a category
create_category() {
    local name="$1"
    local description="$2"
    local subject_id="$3"
    
    print_status "Creating category: $name"
    
    response=$(curl -s -X POST "$API_BASE/documents/categories" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$name\", \"description\": \"$description\", \"subject_id\": $subject_id}")
    
    if echo "$response" | jq -e '.id' > /dev/null; then
        local category_id=$(echo "$response" | jq -r '.id')
        print_success "Category created with ID: $category_id"
        echo "$category_id"
    else
        print_error "Failed to create category"
        exit 1
    fi
}

# Function to upload a document
upload_document() {
    local filename="$1"
    local subject_id="$2"
    local category_id="$3"
    
    print_status "Uploading document: $filename"
    
    # Create a sample file if it doesn't exist
    if [ ! -f "$filename" ]; then
        echo "Sample content for $filename" > "$filename"
    fi
    
    response=$(curl -s -X POST "$API_BASE/documents/upload" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -F "file=@$filename" \
        -F "subject_id=$subject_id" \
        -F "category_id=$category_id")
    
    if echo "$response" | jq -e '.id' > /dev/null; then
        local doc_id=$(echo "$response" | jq -r '.id')
        print_success "Document uploaded with ID: $doc_id"
        echo "$doc_id"
    else
        print_error "Failed to upload document"
        exit 1
    fi
}

# Function to list documents in a category
list_category_documents() {
    local category_id="$1"
    
    print_status "Listing documents in category $category_id..."
    
    response=$(curl -s -X GET "$API_BASE/documents/categories/$category_id/documents" \
        -H "Authorization: Bearer $AUTH_TOKEN")
    
    if echo "$response" | jq -e '.[]' > /dev/null; then
        print_success "Documents in category:"
        echo "$response" | jq -r '.[] | "  ID: \(.id), Name: \(.filename), Status: \(.status)"'
    else
        print_warning "No documents found in category"
    fi
}

# Function to create a custom document set
create_document_set() {
    local name="$1"
    local description="$2"
    local document_ids="$3"
    local subject_id="$4"
    
    print_status "Creating custom document set: $name"
    
    response=$(curl -s -X POST "$API_BASE/quizzes/document-sets" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$name\",
            \"description\": \"$description\",
            \"document_ids\": [$document_ids],
            \"subject_id\": $subject_id
        }")
    
    if echo "$response" | jq -e '.id' > /dev/null; then
        local set_id=$(echo "$response" | jq -r '.id')
        print_success "Document set created with ID: $set_id"
        echo "$set_id"
    else
        print_error "Failed to create document set"
        exit 1
    fi
}

# Function to generate quiz from selected documents
generate_quiz_from_selected() {
    local topic="$1"
    local document_ids="$2"
    local num_questions="$3"
    
    print_status "Generating quiz from selected documents..."
    
    response=$(curl -s -X POST "$API_BASE/quizzes/generate/selected-documents" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"topic\": \"$topic\",
            \"difficulty\": \"medium\",
            \"num_questions\": $num_questions,
            \"document_ids\": [$document_ids]
        }")
    
    if echo "$response" | jq -e '.quiz_id' > /dev/null; then
        local quiz_id=$(echo "$response" | jq -r '.quiz_id')
        local title=$(echo "$response" | jq -r '.title')
        local questions_count=$(echo "$response" | jq -r '.questions_count')
        local generation_time=$(echo "$response" | jq -r '.generation_time')
        local documents_used=$(echo "$response" | jq -r '.documents_used | join(", ")')
        
        print_success "Quiz generated successfully!"
        echo "  Quiz ID: $quiz_id"
        echo "  Title: $title"
        echo "  Questions: $questions_count"
        echo "  Generation time: ${generation_time}s"
        echo "  Documents used: $documents_used"
    else
        print_error "Failed to generate quiz"
        echo "$response"
    fi
}

# Function to generate quiz from custom document set
generate_quiz_from_set() {
    local set_id="$1"
    local topic="$2"
    local num_questions="$3"
    
    print_status "Generating quiz from document set $set_id..."
    
    response=$(curl -s -X POST "$API_BASE/quizzes/generate/document-set/$set_id" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"topic\": \"$topic\",
            \"difficulty\": \"medium\",
            \"num_questions\": $num_questions
        }")
    
    if echo "$response" | jq -e '.quiz_id' > /dev/null; then
        local quiz_id=$(echo "$response" | jq -r '.quiz_id')
        local title=$(echo "$response" | jq -r '.title')
        local questions_count=$(echo "$response" | jq -r '.questions_count')
        local generation_time=$(echo "$response" | jq -r '.generation_time')
        local documents_used=$(echo "$response" | jq -r '.documents_used | join(", ")')
        
        print_success "Quiz generated successfully!"
        echo "  Quiz ID: $quiz_id"
        echo "  Title: $title"
        echo "  Questions: $questions_count"
        echo "  Generation time: ${generation_time}s"
        echo "  Documents used: $documents_used"
    else
        print_error "Failed to generate quiz"
        echo "$response"
    fi
}

# Main demonstration
main() {
    print_header "Study AI - Document Selection Example"
    echo "=============================================="
    echo ""
    
    # Check if services are running
    print_status "Checking if services are running..."
    if ! curl -s "$API_BASE/health" > /dev/null; then
        print_error "Services are not running. Please start them first:"
        print_warning "  ./scripts/setup-dev.sh"
        exit 1
    fi
    print_success "Services are running"
    
    # Get authentication token
    get_auth_token
    
    echo ""
    print_header "Step 1: Create Subject and Category"
    echo "-------------------------------------------"
    
    # Create a subject
    subject_id=$(create_subject "Computer Science" "Computer science and programming topics")
    
    # Create a category
    category_id=$(create_category "Python Programming" "Python language and frameworks" "$subject_id")
    
    echo ""
    print_header "Step 2: Upload Multiple Documents"
    echo "----------------------------------------"
    
    # Upload 10 documents to the category
    document_ids=""
    for i in {1..10}; do
        filename="python_doc_$i.txt"
        doc_id=$(upload_document "$filename" "$subject_id" "$category_id")
        
        if [ -z "$document_ids" ]; then
            document_ids="$doc_id"
        else
            document_ids="$document_ids, $doc_id"
        fi
        
        # Wait a bit for processing
        sleep 2
    done
    
    echo ""
    print_header "Step 3: List All Documents in Category"
    echo "---------------------------------------------"
    
    list_category_documents "$category_id"
    
    echo ""
    print_header "Step 4: Create Custom Document Set (Select 3 Documents)"
    echo "-------------------------------------------------------------"
    
    # Select only 3 documents (first, fifth, and tenth)
    first_doc=$(echo "$document_ids" | cut -d',' -f1 | tr -d ' ')
    fifth_doc=$(echo "$document_ids" | cut -d',' -f5 | tr -d ' ')
    tenth_doc=$(echo "$document_ids" | cut -d',' -f10 | tr -d ' ')
    
    selected_docs="$first_doc, $fifth_doc, $tenth_doc"
    
    set_id=$(create_document_set "Python Basics Set" "Selected documents for Python basics" "$selected_docs" "$subject_id")
    
    echo ""
    print_header "Step 5: Generate Quiz from Selected Documents (Method 1)"
    echo "---------------------------------------------------------------"
    
    # Method 1: Direct document selection
    generate_quiz_from_selected "Python Programming Basics" "$selected_docs" 5
    
    echo ""
    print_header "Step 6: Generate Quiz from Custom Document Set (Method 2)"
    echo "----------------------------------------------------------------"
    
    # Method 2: Using custom document set
    generate_quiz_from_set "$set_id" "Python Programming Basics" 5
    
    echo ""
    print_header "Step 7: Compare with Full Category Quiz"
    echo "-----------------------------------------------"
    
    # Generate quiz from entire category for comparison
    print_status "Generating quiz from entire category..."
    
    response=$(curl -s -X POST "$API_BASE/quizzes/generate/category" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"category_id\": $category_id,
            \"topic\": \"Python Programming (All Documents)\",
            \"difficulty\": \"medium\",
            \"num_questions\": 5
        }")
    
    if echo "$response" | jq -e '.quiz_id' > /dev/null; then
        local quiz_id=$(echo "$response" | jq -r '.quiz_id')
        local title=$(echo "$response" | jq -r '.title')
        local questions_count=$(echo "$response" | jq -r '.questions_count')
        
        print_success "Full category quiz generated!"
        echo "  Quiz ID: $quiz_id"
        echo "  Title: $title"
        echo "  Questions: $questions_count"
        echo "  Note: This quiz uses content from ALL 10 documents"
    fi
    
    echo ""
    print_header "Summary"
    echo "========"
    print_success "Document selection demonstration completed!"
    echo ""
    echo "What we demonstrated:"
    echo "1. ✅ Created a subject with 10 documents"
    echo "2. ✅ Selected only 3 specific documents for quiz generation"
    echo "3. ✅ Generated focused quizzes using only selected content"
    echo "4. ✅ Created reusable document sets for future use"
    echo "5. ✅ Compared with full category quiz generation"
    echo ""
    echo "Key benefits:"
    echo "• 🎯 Focused learning: Quiz questions based only on selected content"
    echo "• 🔄 Reusable sets: Save document combinations for repeated use"
    echo "• 📊 Granular control: Choose exactly which documents to include"
    echo "• ⚡ Efficient: Generate targeted quizzes without processing all content"
}

# Run the demonstration
main "$@" 