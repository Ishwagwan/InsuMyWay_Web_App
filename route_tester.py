#!/usr/bin/env python3
"""
Route Tester for InsuMyWay Web Application
Tests if all routes are accessible and return valid responses.
"""

import requests
import time
from urllib.parse import urljoin

def test_routes():
    """Test all application routes"""
    base_url = "http://127.0.0.1:5000"
    
    # Routes to test (without authentication required)
    public_routes = [
        "/",
        "/login",
        "/register", 
        "/privacy",
        "/terms"
    ]
    
    # Routes that might require authentication
    protected_routes = [
        "/dashboard",
        "/profile",
        "/products",
        "/recommendations",
        "/chat",
        "/admin",
        "/ai_recommendations",
        "/purchase",
        "/manage_policies",
        "/ml_dashboard"
    ]
    
    print("🌐 InsuMyWay Route Tester")
    print("=" * 50)
    
    # Test if server is running
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ Server is running at {base_url}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not accessible: {e}")
        print("💡 Make sure to start the Flask app first:")
        print("   py -3.9 app.py")
        return
    
    print("\n📋 Testing Public Routes:")
    print("-" * 30)
    
    for route in public_routes:
        url = urljoin(base_url, route)
        try:
            response = requests.get(url, timeout=5)
            status = "✅" if response.status_code == 200 else "⚠️"
            print(f"{status} {route:<20} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {route:<20} - Error: {str(e)[:50]}...")
    
    print("\n🔒 Testing Protected Routes:")
    print("-" * 30)
    
    for route in protected_routes:
        url = urljoin(base_url, route)
        try:
            response = requests.get(url, timeout=5, allow_redirects=False)
            if response.status_code == 200:
                status = "✅"
                note = "Accessible"
            elif response.status_code == 302:
                status = "🔄"
                note = "Redirects (likely to login)"
            elif response.status_code == 401:
                status = "🔒"
                note = "Authentication required"
            else:
                status = "⚠️"
                note = f"Status {response.status_code}"
            
            print(f"{status} {route:<20} - {note}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {route:<20} - Error: {str(e)[:50]}...")
    
    print("\n" + "=" * 50)
    print("🎯 Testing Complete!")
    print("\nLegend:")
    print("✅ = Working properly")
    print("🔄 = Redirects (normal for protected routes)")
    print("🔒 = Authentication required")
    print("⚠️ = Unexpected status code")
    print("❌ = Error or not accessible")

if __name__ == "__main__":
    test_routes()
