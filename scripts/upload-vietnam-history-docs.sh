#!/bin/bash

# Study AI - Vietnam History Documents Upload Script
# This script uploads 4 historical documents about the Tay Son Rebellion and Nguyen Dynasty

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
SUBJECT_ID=""
CATEGORY_ID=""
DOCUMENT_IDS=""

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
    print_status "Creating subject: Vietnam History"
    
    response=$(curl -s -X POST "$API_BASE/documents/subjects" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"name": "Vietnam History", "description": "Historical events and periods in Vietnamese history"}')
    
    if echo "$response" | jq -e '.id' > /dev/null; then
        SUBJECT_ID=$(echo "$response" | jq -r '.id')
        print_success "Subject created with ID: $SUBJECT_ID"
    else
        print_error "Failed to create subject"
        exit 1
    fi
}

# Function to create a category
create_category() {
    print_status "Creating category: Tay Son Rebellion and Nguyen Dynasty"
    
    response=$(curl -s -X POST "$API_BASE/documents/categories" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"Tay Son Rebellion and Nguyen Dynasty\", \"description\": \"The conflict between Tay Son (Nguyen Hue) and Nguyen Dynasty (Nguyen Anh)\", \"subject_id\": $SUBJECT_ID}")
    
    if echo "$response" | jq -e '.id' > /dev/null; then
        CATEGORY_ID=$(echo "$response" | jq -r '.id')
        print_success "Category created with ID: $CATEGORY_ID"
    else
        print_error "Failed to create category"
        exit 1
    fi
}

# Function to upload a document
upload_document() {
    local filename="$1"
    local display_name="$2"
    
    print_status "Uploading document: $display_name"
    
    response=$(curl -s -X POST "$API_BASE/documents/upload" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -F "file=@data/$filename" \
        -F "subject_id=$SUBJECT_ID" \
        -F "category_id=$CATEGORY_ID")
    
    if echo "$response" | jq -e '.id' > /dev/null; then
        local doc_id=$(echo "$response" | jq -r '.id')
        print_success "Document uploaded with ID: $doc_id"
        
        if [ -z "$DOCUMENT_IDS" ]; then
            DOCUMENT_IDS="$doc_id"
        else
            DOCUMENT_IDS="$DOCUMENT_IDS, $doc_id"
        fi
        
        echo "$doc_id"
    else
        print_error "Failed to upload document: $display_name"
        echo "$response"
        exit 1
    fi
}

# Function to wait for document processing
wait_for_processing() {
    local doc_id="$1"
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for document $doc_id to be processed..."
    
    while [ $attempt -le $max_attempts ]; do
        response=$(curl -s -X GET "$API_BASE/documents/documents/$doc_id" \
            -H "Authorization: Bearer $AUTH_TOKEN")
        
        if echo "$response" | jq -e '.status' > /dev/null; then
            local status=$(echo "$response" | jq -r '.status')
            
            if [ "$status" = "completed" ]; then
                print_success "Document $doc_id processing completed"
                return 0
            elif [ "$status" = "failed" ]; then
                print_error "Document $doc_id processing failed"
                return 1
            fi
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_warning "Document $doc_id processing timeout"
    return 1
}

# Function to list documents in category
list_category_documents() {
    print_status "Listing documents in category $CATEGORY_ID..."
    
    response=$(curl -s -X GET "$API_BASE/documents/categories/$CATEGORY_ID/documents" \
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
    
    print_status "Creating custom document set: $name"
    
    response=$(curl -s -X POST "$API_BASE/quizzes/document-sets" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$name\",
            \"description\": \"$description\",
            \"document_ids\": [$document_ids],
            \"subject_id\": $SUBJECT_ID
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

# Main execution
main() {
    print_header "Study AI - Vietnam History Documents Upload"
    echo "=================================================="
    echo ""
    
    # Check if services are running
    print_status "Checking if services are running..."
    if ! curl -s "$API_BASE/health" > /dev/null; then
        print_error "Services are not running. Please start them first:"
        print_warning "  ./scripts/setup-dev.sh"
        exit 1
    fi
    print_success "Services are running"
    
    # Check if data files exist
    print_status "Checking data files..."
    for file in "01_rise_of_tay_son_rebellion.txt" "02_nguyen_hue_conquests.txt" "03_nguyen_anh_exile_return.txt" "04_final_victory_nguyen_dynasty.txt"; do
        if [ ! -f "data/$file" ]; then
            print_error "Data file not found: data/$file"
            exit 1
        fi
    done
    print_success "All data files found"
    
    # Get authentication token
    get_auth_token
    
    echo ""
    print_header "Step 1: Create Subject and Category"
    echo "-------------------------------------------"
    
    # Create subject and category
    create_subject
    create_category
    
    echo ""
    print_header "Step 2: Upload Historical Documents"
    echo "------------------------------------------"
    
    # Upload documents in chronological order
    doc1_id=$(upload_document "01_rise_of_tay_son_rebellion.txt" "The Rise of the Tay Son Rebellion (1771-1786)")
    wait_for_processing "$doc1_id"
    
    doc2_id=$(upload_document "02_nguyen_hue_conquests.txt" "Nguyen Hue's Conquests and the Peak of Tay Son Power (1786-1789)")
    wait_for_processing "$doc2_id"
    
    doc3_id=$(upload_document "03_nguyen_anh_exile_return.txt" "Nguyen Anh's Exile and Return (1787-1802)")
    wait_for_processing "$doc3_id"
    
    doc4_id=$(upload_document "04_final_victory_nguyen_dynasty.txt" "The Final Victory: Nguyen Anh's Triumph and the Establishment of the Nguyen Dynasty (1802-1820)")
    wait_for_processing "$doc4_id"
    
    echo ""
    print_header "Step 3: List All Documents in Category"
    echo "---------------------------------------------"
    
    list_category_documents
    
    echo ""
    print_header "Step 4: Create Custom Document Sets"
    echo "------------------------------------------"
    
    # Create different document sets for different learning objectives
    
    # Set 1: Early Period (Documents 1-2)
    early_period_ids="$doc1_id, $doc2_id"
    set1_id=$(create_document_set "Early Tay Son Period" "The rise of Tay Son and Nguyen Hue's early conquests" "$early_period_ids")
    
    # Set 2: Late Period (Documents 3-4)
    late_period_ids="$doc3_id, $doc4_id"
    set2_id=$(create_document_set "Nguyen Anh's Counter-Revolution" "Nguyen Anh's exile, return, and final victory" "$late_period_ids")
    
    # Set 3: Key Battles (Documents 2, 4)
    key_battles_ids="$doc2_id, $doc4_id"
    set3_id=$(create_document_set "Key Military Campaigns" "Major military campaigns and battles" "$key_battles_ids")
    
    echo ""
    print_header "Step 5: Generate Quizzes from Different Document Sets"
    echo "------------------------------------------------------------"
    
    # Generate quiz from early period documents
    generate_quiz_from_selected "Early Tay Son Rebellion" "$early_period_ids" 5
    
    echo ""
    # Generate quiz from late period documents
    generate_quiz_from_selected "Nguyen Anh's Counter-Revolution" "$late_period_ids" 5
    
    echo ""
    # Generate quiz from key battles documents
    generate_quiz_from_selected "Major Military Campaigns" "$key_battles_ids" 5
    
    echo ""
    print_header "Step 6: Generate Quiz from Custom Document Set"
    echo "----------------------------------------------------"
    
    # Generate quiz from custom document set
    print_status "Generating quiz from custom document set $set1_id..."
    
    response=$(curl -s -X POST "$API_BASE/quizzes/generate/document-set/$set1_id" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "topic": "Early Tay Son Period",
            "difficulty": "medium",
            "num_questions": 5
        }')
    
    if echo "$response" | jq -e '.quiz_id' > /dev/null; then
        local quiz_id=$(echo "$response" | jq -r '.quiz_id')
        local title=$(echo "$response" | jq -r '.title')
        local questions_count=$(echo "$response" | jq -r '.questions_count')
        local generation_time=$(echo "$response" | jq -r '.generation_time')
        local documents_used=$(echo "$response" | jq -r '.documents_used | join(", ")')
        
        print_success "Quiz generated successfully from document set!"
        echo "  Quiz ID: $quiz_id"
        echo "  Title: $title"
        echo "  Questions: $questions_count"
        echo "  Generation time: ${generation_time}s"
        echo "  Documents used: $documents_used"
    else
        print_error "Failed to generate quiz from document set"
        echo "$response"
    fi
    
    echo ""
    print_header "Summary"
    echo "========"
    print_success "Vietnam History documents upload and quiz generation completed!"
    echo ""
    echo "What we accomplished:"
    echo "1. ✅ Created 'Vietnam History' subject"
    echo "2. ✅ Created 'Tay Son Rebellion and Nguyen Dynasty' category"
    echo "3. ✅ Uploaded 4 historical documents in chronological order:"
    echo "   - Document 1: The Rise of the Tay Son Rebellion (1771-1786)"
    echo "   - Document 2: Nguyen Hue's Conquests (1786-1789)"
    echo "   - Document 3: Nguyen Anh's Exile and Return (1787-1802)"
    echo "   - Document 4: Final Victory and Nguyen Dynasty (1802-1820)"
    echo "4. ✅ Created 3 custom document sets:"
    echo "   - Early Tay Son Period (Documents 1-2)"
    echo "   - Nguyen Anh's Counter-Revolution (Documents 3-4)"
    echo "   - Key Military Campaigns (Documents 2, 4)"
    echo "5. ✅ Generated quizzes from different document combinations"
    echo ""
    echo "Document IDs: $DOCUMENT_IDS"
    echo "Subject ID: $SUBJECT_ID"
    echo "Category ID: $CATEGORY_ID"
    echo ""
    echo "You can now:"
    echo "• Generate focused quizzes from specific historical periods"
    echo "• Create custom learning paths through Vietnamese history"
    echo "• Test different document combinations for various topics"
    echo "• Use the document selection feature for targeted learning"
}

# Run the script
main "$@" 