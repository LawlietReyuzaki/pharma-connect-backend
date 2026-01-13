"""
Test script for Enhanced Wikipedia Medical Agent
Demonstrates intelligent keyword extraction and combined search.
"""

from services.wikipedia_medical_agent import (
    process_medical_query,
    extract_keywords_only,
    get_enhanced_wiki_agent
)


def test_keyword_extraction():
    """Test keyword extraction without fetching data"""
    
    print("=" * 70)
    print("TESTING KEYWORD EXTRACTION")
    print("=" * 70)
    
    test_queries = [
        "what are main symptoms of disease syphilis",
        "medicine for fever",
        "tell me about diabetes",
        "how to treat tuberculosis",
        "what is aspirin used for",
        "I have headache and fever",
        "recommend medicine for cough",
    ]
    
    from services.wikipedia_medical_agent import extract_keywords_only
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print("="*60)
        
        extracted = extract_keywords_only(query)
        
        print(f"Topic Type: {extracted.topic_type.value}")
        print(f"Primary Keyword: {extracted.primary_keyword}")
        print(f"Wiki Keywords: {extracted.wiki_keywords}")
        print(f"Medicine Keywords: {extracted.medicine_keywords}")
        print(f"Confidence: {extracted.extraction_confidence:.2f}")
        print(f"Search Wikipedia: {extracted.should_search_wikipedia}")
        print(f"Search Medicines: {extracted.should_search_medicines}")
        print(f"Reason: {extracted.reason}")
        print()


# Example usage
if __name__ == "__main__":
    # Test queries
    test_queries = [
        "what are main symptoms of disease syphilis",
        "medicine for diabetes",
        "tell me about hypertension",
        "what is paracetamol used for",
        "treatment for fever"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print("="*60)
        
        result = process_medical_query(query)
        
        print(f"Primary Keyword: {result['extracted'].primary_keyword}")
        print(f"Medicine Keywords: {result['extracted'].medicine_keywords}")
        print(f"Wikipedia: {result['wikipedia']['title'] if result['wikipedia'] else 'None'}")
        print(f"Medicines Found: {len(result['medicines'])}")
