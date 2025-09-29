#!/usr/bin/env python3

"""
GraphQL API Token Generator

Install required packages:
pip install requests

Usage:
python login.py [target_url]
"""

import requests
import json
import sys
from typing import Dict

class GraphQLUser:
    def __init__(self, name: str, email: str, password: str):
        self.name = name
        self.email = email
        self.password = password

def login(user: GraphQLUser, target_url: str = "http://localhost:4000") -> Dict[str, str]:
    """
    Login as a user and return a dict containing tokens needed for authenticated requests.
    
    Args:
        user: GraphQLUser object with email and password
        target_url: Base URL of the GraphQL API
    
    Returns:
        Dict containing the JWT token and user info
    """
    
    # GraphQL login mutation
    query = """
    mutation Login($input: LoginInput!) {
        login(input: $input) {
            token
            user {
                id
                email
                firstName
                lastName
                role
            }
        }
    }
    """
    
    variables = {
        "input": {
            "email": user.email,
            "password": user.password
        }
    }
    
    # GraphQL request payload
    payload = {
        "query": query,
        "variables": variables
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{target_url}/graphql",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "errors" in data:
                print(f"❌ GraphQL Error: {data['errors']}")
                return {}
            
            login_data = data.get("data", {}).get("login", {})
            token = login_data.get("token")
            user_info = login_data.get("user", {})
            
            if token:
                return {
                    "token": f"Bearer {token}",
                    "user_id": user_info.get("id"),
                    "email": user_info.get("email"),
                    "role": user_info.get("role"),
                    "name": f"{user_info.get('firstName', '')} {user_info.get('lastName', '')}".strip()
                }
            else:
                print("❌ No token received in response")
                return {}
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return {}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        return {}

def get_all_tokens(target_url: str = "http://localhost:4000") -> Dict[str, Dict[str, str]]:
    """
    Get tokens for all default users (admin and regular user).
    
    Args:
        target_url: Base URL of the GraphQL API
    
    Returns:
        Dict containing tokens for all users
    """
    
    # Default users from the API
    users = [
        GraphQLUser("Admin User", "admin@test.com", "admin123"),
        GraphQLUser("Regular User", "user@test.com", "user123")
    ]
    
    tokens = {}
    
    for user in users:
        print(f"🔐 Getting token for {user.name} ({user.email})...")
        result = login(user, target_url)
        
        if result:
            tokens[user.email] = result
            print(f"✅ Success: {result['name']} ({result['role']})")
            print(f"   Token: {result['token'][:50]}...")
        else:
            print(f"❌ Failed to get token for {user.email}")
        
        print()
    
    return tokens

def test_api_with_token(token: str, target_url: str = "http://localhost:4000") -> bool:
    """
    Test the API with a token by making a simple GraphQL query.
    
    Args:
        token: JWT token to test
        target_url: Base URL of the GraphQL API
    
    Returns:
        True if successful, False otherwise
    """
    
    query = """
    query {
        me {
            id
            email
            firstName
            lastName
            role
        }
    }
    """
    
    payload = {
        "query": query
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    
    try:
        response = requests.post(
            f"{target_url}/graphql",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" not in data:
                user_data = data.get("data", {}).get("me", {})
                print(f"✅ Token test successful: {user_data.get('email')} ({user_data.get('role')})")
                return True
            else:
                print(f"❌ GraphQL Error: {data['errors']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        return False

if __name__ == "__main__":
    # Get target URL from command line or use default
    target_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:4000"
    
    print(f"🎯 Target URL: {target_url}")
    print("=" * 50)
    
    # Get tokens for all default users
    tokens = get_all_tokens(target_url)
    
    if tokens:
        print("📋 Summary of obtained tokens:")
        print("=" * 50)
        
        for email, token_info in tokens.items():
            print(f"👤 {token_info['name']} ({email})")
            print(f"   Role: {token_info['role']}")
            print(f"   Token: {token_info['token']}")
            print()
        
        # Test tokens
        print("🧪 Testing tokens...")
        print("=" * 50)
        
        for email, token_info in tokens.items():
            print(f"Testing token for {email}...")
            test_api_with_token(token_info['token'], target_url)
            print()
    
    else:
        print("❌ No tokens obtained. Check if the API is running and accessible.")
        print(f"   Try: curl {target_url}/health")

