#!/bin/bash

# Study AI - Vietnam History Upload using curl commands
# This script demonstrates how to use curl to upload historical documents

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

print_curl() {
    echo -e "${YELLOW}🔗 $1${NC}"
}

# Configuration
API_BASE="http://localhost"
AUTH_TOKEN=""
SUBJECT_ID=""
CATEGORY_ID=""
DOCUMENT_IDS=""

# Step 1: Login to get token
print_header "Step 1: Login to get authentication token"
echo "================================================"

print_curl "curl -X POST $API_BASE/auth/login \\"
print_curl "  -H 'Content-Type: application/json' \\"
print_curl "  -d '{\"email\": \"test@test.com\", \"password\": \"test123\"}'"

echo ""
print_status "Executing login request..."

response=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "test123"}')

if echo "$response" | jq -e '.access_token' > /dev/null; then
    AUTH_TOKEN=$(echo "$response" | jq -r '.access_token')
    print_success "Login successful! Token obtained."
    echo "Token: ${AUTH_TOKEN:0:20}..."
else
    print_error "Login failed!"
    echo "Response: $response"
    exit 1
fi

echo ""

# Step 2: Create subject "History"
print_header "Step 2: Create subject 'History'"
echo "======================================"

print_curl "curl -X POST $API_BASE/documents/simple-subject \\"
print_curl "  -H 'Authorization: Bearer $AUTH_TOKEN' \\"
print_curl "  -H 'Content-Type: application/json' \\"
print_curl "  -d '{\"name\": \"History\", \"description\": \"Historical events and periods\"}'"

echo ""
print_status "Creating subject 'History'..."

response=$(curl -s -X POST "$API_BASE/documents/simple-subject" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "History", "description": "Historical events and periods"}')

# Extract subject ID from response or use existing one
SUBJECT_ID=$(echo "$response" | jq -r '.id')
if [ "$SUBJECT_ID" = "null" ] || [ -z "$SUBJECT_ID" ]; then
    # If subject already exists, try to get it from the list
    print_status "Subject already exists, getting existing subject ID..."
    subjects_response=$(curl -s -X GET "$API_BASE/documents/subjects" \
      -H "Authorization: Bearer $AUTH_TOKEN")
    SUBJECT_ID=$(echo "$subjects_response" | jq -r '.[] | select(.name == "History") | .id')
    if [ "$SUBJECT_ID" = "null" ] || [ -z "$SUBJECT_ID" ]; then
        print_error "Failed to get existing subject ID"
        exit 1
    fi
    print_success "Using existing subject with ID: $SUBJECT_ID"
else
    print_success "Subject created with ID: $SUBJECT_ID"
fi

echo ""

# Step 3: Create category "Tay Son Rebellion"
print_header "Step 3: Create category 'Tay Son Rebellion'"
echo "================================================"

print_curl "curl -X POST $API_BASE/documents/categories \\"
print_curl "  -H 'Authorization: Bearer $AUTH_TOKEN' \\"
print_curl "  -H 'Content-Type: application/json' \\"
print_curl "  -d '{\"name\": \"Tay Son Rebellion\", \"description\": \"The conflict between Tay Son and Nguyen Dynasty\", \"subject_id\": $SUBJECT_ID}'"

echo ""
print_status "Creating category 'Tay Son Rebellion'..."

response=$(curl -s -X POST "$API_BASE/documents/categories" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Tay Son Rebellion\", \"description\": \"The conflict between Tay Son and Nguyen Dynasty\", \"subject_id\": $SUBJECT_ID}")

# Extract category ID from response or use existing one
CATEGORY_ID=$(echo "$response" | jq -r '.id')
if [ "$CATEGORY_ID" = "null" ] || [ -z "$CATEGORY_ID" ]; then
    # Category already exists, get the existing category ID
    print_status "Category already exists, getting existing category ID..."
    categories_response=$(curl -s -X GET "$API_BASE/documents/categories?subject_id=$SUBJECT_ID" \
      -H "Authorization: Bearer $AUTH_TOKEN")
    CATEGORY_ID=$(echo "$categories_response" | jq -r '.[] | select(.name == "Tay Son Rebellion") | .id')
    if [ "$CATEGORY_ID" = "null" ] || [ -z "$CATEGORY_ID" ]; then
        print_error "Failed to get existing category ID"
        exit 1
    fi
    print_success "Using existing category with ID: $CATEGORY_ID"
else
    print_success "Category created with ID: $CATEGORY_ID"
fi

echo ""

# Step 4: Upload documents
print_header "Step 4: Upload documents to vector database"
echo "=================================================="

# Function to upload a document
upload_document() {
    local filename="$1"
    local display_name="$2"
    
    print_status "Uploading: $display_name"
    
    print_curl "curl -X POST $API_BASE/documents/upload \\"
    print_curl "  -H 'Authorization: Bearer $AUTH_TOKEN' \\"
    print_curl "  -F 'file=@data/$filename' \\"
    print_curl "  -F 'subject_id=$SUBJECT_ID' \\"
    print_curl "  -F 'category_id=$CATEGORY_ID'"
    
    echo ""
    
    response=$(curl -s -X POST "$API_BASE/documents/upload" \
      -H "Authorization: Bearer $AUTH_TOKEN" \
      -F "file=@data/$filename" \
      -F "subject_id=$SUBJECT_ID" \
      -F "category_id=$CATEGORY_ID")
    
    if echo "$response" | jq -e '.id' > /dev/null; then
        local doc_id=$(echo "$response" | jq -r '.id')
        local status=$(echo "$response" | jq -r '.status')
        print_success "Document uploaded successfully!"
        echo "Document ID: $doc_id"
        echo "Status: $status"
        
        if [ -z "$DOCUMENT_IDS" ]; then
            DOCUMENT_IDS="$doc_id"
        else
            DOCUMENT_IDS="$DOCUMENT_IDS, $doc_id"
        fi
        
        echo "$doc_id"
    else
        print_error "Failed to upload document: $display_name"
        echo "Response: $response"
        exit 1
    fi
    
    echo ""
}

# Function to wait for document processing
wait_for_processing() {
    local doc_id="$1"
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for document $doc_id to be processed and indexed..."
    
    while [ $attempt -le $max_attempts ]; do
        print_curl "curl -X GET $API_BASE/documents/documents/$doc_id \\"
        print_curl "  -H 'Authorization: Bearer $AUTH_TOKEN'"
        
        response=$(curl -s -X GET "$API_BASE/documents/documents/$doc_id" \
          -H "Authorization: Bearer $AUTH_TOKEN")
        
        if echo "$response" | jq -e '.status' > /dev/null; then
            local status=$(echo "$response" | jq -r '.status')
            
            if [ "$status" = "completed" ]; then
                print_success "Document $doc_id processing completed and indexed in vector database!"
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

# Upload documents in chronological order
echo "Uploading 4 historical documents about the Tay Son Rebellion:"
echo ""

doc1_id=$(upload_document "01_rise_of_tay_son_rebellion.txt" "The Rise of the Tay Son Rebellion (1771-1786)")
wait_for_processing "$doc1_id"

doc2_id=$(upload_document "02_nguyen_hue_conquests.txt" "Nguyen Hue's Conquests and the Peak of Tay Son Power (1786-1789)")
wait_for_processing "$doc2_id"

doc3_id=$(upload_document "03_nguyen_anh_exile_return.txt" "Nguyen Anh's Exile and Return (1787-1802)")
wait_for_processing "$doc3_id"

doc4_id=$(upload_document "04_final_victory_nguyen_dynasty.txt" "The Final Victory: Nguyen Anh's Triumph and the Establishment of the Nguyen Dynasty (1802-1820)")
wait_for_processing "$doc4_id"

echo ""

# Step 5: List documents in category
print_header "Step 5: List all documents in the category"
echo "================================================"

print_curl "curl -X GET $API_BASE/documents/categories/$CATEGORY_ID/documents \\"
print_curl "  -H 'Authorization: Bearer $AUTH_TOKEN'"

echo ""
print_status "Listing documents in category $CATEGORY_ID..."

response=$(curl -s -X GET "$API_BASE/documents/categories/$CATEGORY_ID/documents" \
  -H "Authorization: Bearer $AUTH_TOKEN")

if echo "$response" | jq -e '.[]' > /dev/null; then
    print_success "Documents found in category:"
    echo "$response" | jq -r '.[] | "  ID: \(.id), Name: \(.filename), Status: \(.status), Size: \(.file_size) bytes"'
else
    print_warning "No documents found in category"
fi

echo ""

# Step 6: Verify vector indexing
print_header "Step 6: Verify vector indexing"
echo "===================================="

print_curl "curl -X GET $API_BASE/indexing/chunks/subject/$SUBJECT_ID \\"
print_curl "  -H 'Authorization: Bearer $AUTH_TOKEN'"

echo ""
print_status "Checking vector chunks for subject $SUBJECT_ID..."

response=$(curl -s -X GET "$API_BASE/indexing/chunks/subject/$SUBJECT_ID" \
  -H "Authorization: Bearer $AUTH_TOKEN")

if echo "$response" | jq -e '.[]' > /dev/null; then
    chunk_count=$(echo "$response" | jq 'length')
    print_success "Vector indexing completed!"
    echo "Total chunks indexed: $chunk_count"
    echo "Documents are now searchable in the vector database"
else
    print_warning "No chunks found - indexing may still be in progress"
fi

echo ""

# Step 7: Test document selection for quiz generation
print_header "Step 7: Test document selection for quiz generation"
echo "=========================================================="

print_curl "curl -X POST $API_BASE/quizzes/generate/selected-documents \\"
print_curl "  -H 'Authorization: Bearer $AUTH_TOKEN' \\"
print_curl "  -H 'Content-Type: application/json' \\"
print_curl "  -d '{"
print_curl "    \"topic\": \"Early Tay Son Rebellion\","
print_curl "    \"difficulty\": \"medium\","
print_curl "    \"num_questions\": 3,"
print_curl "    \"document_ids\": [$doc1_id, $doc2_id]"
print_curl "  }'"

echo ""
print_status "Generating quiz from selected documents (Documents 1 & 2)..."

response=$(curl -s -X POST "$API_BASE/quizzes/generate/selected-documents" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"topic\": \"Early Tay Son Rebellion\",
    \"difficulty\": \"medium\",
    \"num_questions\": 3,
    \"document_ids\": [$doc1_id, $doc2_id]
  }")

if echo "$response" | jq -e '.quiz_id' > /dev/null; then
    quiz_id=$(echo "$response" | jq -r '.quiz_id')
    title=$(echo "$response" | jq -r '.title')
    questions_count=$(echo "$response" | jq -r '.questions_count')
    documents_used=$(echo "$response" | jq -r '.documents_used | join(", ")')
    
    print_success "Quiz generated successfully from selected documents!"
    echo "Quiz ID: $quiz_id"
    echo "Title: $title"
    echo "Questions: $questions_count"
    echo "Documents used: $documents_used"
else
    print_error "Failed to generate quiz"
    echo "Response: $response"
fi

echo ""

# Summary
print_header "Summary"
echo "========"
print_success "Vietnam History documents successfully uploaded and indexed!"
echo ""
echo "What was accomplished:"
echo "1. ✅ Login successful - obtained authentication token"
echo "2. ✅ Created subject 'History' (ID: $SUBJECT_ID)"
echo "3. ✅ Created category 'Tay Son Rebellion' (ID: $CATEGORY_ID)"
echo "4. ✅ Uploaded 4 historical documents:"
echo "   - Document 1: The Rise of the Tay Son Rebellion (ID: $doc1_id)"
echo "   - Document 2: Nguyen Hue's Conquests (ID: $doc2_id)"
echo "   - Document 3: Nguyen Anh's Exile and Return (ID: $doc3_id)"
echo "   - Document 4: Final Victory and Nguyen Dynasty (ID: $doc4_id)"
echo "5. ✅ All documents processed and indexed in vector database"
echo "6. ✅ Tested document selection for quiz generation"
echo ""
echo "Document IDs: $DOCUMENT_IDS"
echo ""
echo "You can now:"
echo "• Generate quizzes from specific documents using document selection"
echo "• Search through the historical content using vector search"
echo "• Create custom document sets for different learning objectives"
echo "• Use the documents for targeted learning about Vietnamese history"

echo ""
print_header "Example curl commands for further testing:"
echo "================================================"

echo "# List all subjects:"
echo "curl -X GET $API_BASE/documents/subjects \\"
echo "  -H 'Authorization: Bearer $AUTH_TOKEN'"
echo ""

echo "# List all categories:"
echo "curl -X GET $API_BASE/documents/categories \\"
echo "  -H 'Authorization: Bearer $AUTH_TOKEN'"
echo ""

echo "# Search for content about Nguyen Hue:"
echo "curl -X POST $API_BASE/indexing/search \\"
echo "  -H 'Authorization: Bearer $AUTH_TOKEN' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"query\": \"Nguyen Hue military campaigns\", \"limit\": 5}'"
echo ""

echo "# Generate quiz from all documents in category:"
echo "curl -X POST $API_BASE/quizzes/generate/category \\"
echo "  -H 'Authorization: Bearer $AUTH_TOKEN' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"category_id\": $CATEGORY_ID,"
echo "    \"topic\": \"Complete Tay Son Rebellion History\","
echo "    \"difficulty\": \"medium\","
echo "    \"num_questions\": 5"
echo "  }'" 