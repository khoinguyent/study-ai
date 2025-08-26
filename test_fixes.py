#!/usr/bin/env python3
"""
Test script to verify the fixes for the StudyAI application
"""

import sys
import os

# Add the shared directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'shared'))

def test_event_types():
    """Test that all event types are properly defined"""
    try:
        from events import EventType
        print("✅ Event types imported successfully")
        
        # Check if DLQ_ALERT exists
        if hasattr(EventType, 'DLQ_ALERT'):
            print("✅ DLQ_ALERT event type exists")
        else:
            print("❌ DLQ_ALERT event type missing")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Failed to import event types: {e}")
        return False

def test_event_publisher():
    """Test that the event publisher works"""
    try:
        from event_publisher import EventPublisher
        print("✅ Event publisher imported successfully")
        
        publisher = EventPublisher()
        print("✅ Event publisher created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create event publisher: {e}")
        return False

def test_infrastructure():
    """Test that infrastructure components work"""
    try:
        from infrastructure import get_message_broker, is_local_environment
        print("✅ Infrastructure components imported successfully")
        
        is_local = is_local_environment()
        print(f"✅ Environment detection works: {is_local}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to import infrastructure: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing StudyAI fixes...")
    print("=" * 50)
    
    tests = [
        test_event_types,
        test_event_publisher,
        test_infrastructure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The fixes should work.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
