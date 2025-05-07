#!/usr/bin/env python3
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get GitHub token from environment
github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    raise ValueError("GITHUB_TOKEN environment variable not found. Please check your .env file.")

# API endpoint
api_url = "https://gitsummit-backend-sb5gnt3soq-uc.a.run.app/api/chat"

# Repository information
repo_name = "bennysun1/alien_height_prediction"

def query_repository(question, messages=None):
    """
    Send a query to the repository through the API
    
    Args:
        question: The question to ask about the repository
        messages: Optional list of previous messages for conversation context
        
    Returns:
        The API response
    """
    if messages is None:
        messages = []
        
    headers = {
        "Content-Type": "application/json",
        "GitHub-Token": github_token
    }
    
    data = {
        "repository": repo_name,
        "question": question,
        "messages": messages
    }
    
    response = requests.post(api_url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def main():
    print(f"Testing API with repository: {repo_name}")
    
    # First query - ask about file existence
    question1 = """Do any of these files exist in the repository? Please check each one and respond with Yes or No for each: 
    1) Height-Heredity-One-Generations-Impact.pdf 
    2) avg_parent_child.ipynb 
    3) ben_imputer_fix.ipynb 
    4) ben_notebook3_2_best.ipynb 
    5) cleaned_code.ipynb 
    6) final_height_prediction.ipynb 
    7) heritarty analysis.ipynb 
    8) rebekah119.ipynb 
    9) rebekah_cleaned_code.ipynb"""
    
    print("\n=== Query 1: File Existence ===")
    response1 = query_repository(question1)
    
    if response1:
        print(response1["response"])
        
        # Store first message for conversation history
        messages = [
            {"role": "user", "content": question1},
            {"role": "assistant", "content": response1["response"]}
        ]
        
        # Second query - ask for all files with conversation history
        question2 = "Please double-check the full repository and list EVERY single file that exists in it."
        
        print("\n=== Query 2: Full File List (with conversation history) ===")
        response2 = query_repository(question2, messages)
        
        if response2:
            print(response2["response"])
    
    # Third query - ask about ML models used
    print("\n=== Query 3: ML Models Used ===")
    question3 = "What machine learning models are used in this repository? Please be specific about which files contain which models."
    response3 = query_repository(question3)
    
    if response3:
        print(response3["response"])

if __name__ == "__main__":
    main() 