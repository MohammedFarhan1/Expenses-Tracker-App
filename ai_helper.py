import os
import json
import requests
from datetime import datetime
import pandas as pd
import time

class AIExpenseAssistant:
    def __init__(self):
        self.api_key = os.environ.get('GROQ_API_KEY')
        self.model = "llama3-8b-8192"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def get_response(self, message, user_data=None):
        """Generate AI response based on user message and financial data"""
        try:
            # Prepare context with user's financial data if available
            context = self._prepare_context(user_data)
            
            # Create prompt with context and user message
            prompt = f"""You are an AI financial assistant for an expense tracking app. 
            Your goal is to provide helpful insights, suggestions, and answers about the user's finances.
            
            {context}
            
            User: {message}
            
            Assistant:"""
            
            # Call Groq API directly with requests
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 800
            }
            
            # Add retry mechanism
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        return response_data["choices"][0]["message"]["content"]
                    elif response.status_code == 429:  # Rate limit
                        print(f"Rate limit hit, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        print(f"API Error: {response.status_code}, {response.text}")
                        if attempt == max_retries - 1:
                            return "I'm sorry, I encountered an error processing your request. Please try again later."
                        time.sleep(retry_delay)
                except requests.exceptions.RequestException as e:
                    print(f"Request error: {e}")
                    if attempt == max_retries - 1:
                        return "I'm sorry, I encountered a connection error. Please try again later."
                    time.sleep(retry_delay)
            
            return "I'm sorry, I couldn't process your request after multiple attempts. Please try again later."
            
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return "I'm sorry, I encountered an error processing your request. Please try again later."
    
    def _prepare_context(self, user_data):
        """Prepare context with user's financial data"""
        if not user_data or not user_data.get('transactions'):
            return "I don't have access to your financial data yet, but I can still answer general questions about personal finance."
        
        # Format user data into context string
        context = "Here's a summary of your financial information:\n\n"
        
        if 'transactions' in user_data:
            # Calculate spending by category
            spending_by_category = {}
            for transaction in user_data['transactions']:
                if transaction['type'] == 'expense':
                    category = transaction['category']
                    if category in spending_by_category:
                        spending_by_category[category] += transaction['amount']
                    else:
                        spending_by_category[category] = transaction['amount']
            
            # Sort categories by amount (highest first)
            sorted_categories = sorted(spending_by_category.items(), key=lambda x: x[1], reverse=True)
            
            context += "Top spending categories:\n"
            for i, (category, amount) in enumerate(sorted_categories[:5]):  # Show top 5 categories
                context += f"- {category}: ₹{amount:.2f}\n"
        
        if 'summary' in user_data:
            summary = user_data['summary']
            context += f"\nThis month's summary:\n"
            context += f"- Total income: ₹{summary.get('total_income', 0):.2f}\n"
            context += f"- Total expenses: ₹{summary.get('total_expenses', 0):.2f}\n"
            context += f"- Net savings: ₹{summary.get('net_savings', 0):.2f}\n"
            
            # Calculate savings rate if income > 0
            if summary.get('total_income', 0) > 0:
                savings_rate = (summary.get('net_savings', 0) / summary.get('total_income', 0)) * 100
                context += f"- Savings rate: {savings_rate:.1f}%\n"
        
        # Add some guidance for the AI
        context += "\nPlease provide helpful financial insights, budget recommendations, or answer the user's questions based on this data. Format your response in short bullet points rather than paragraphs. Use specific numbers from their data when relevant."
        
        return context
    
    def analyze_spending(self, transactions):
        """Analyze spending patterns from transactions"""
        try:
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(transactions)
            
            # Filter expenses
            expenses = df[df['type'] == 'expense']
            
            # Analysis by category
            category_analysis = expenses.groupby('category')['amount'].agg(['sum', 'mean', 'count'])
            
            # Analysis by time (monthly)
            expenses['month'] = pd.to_datetime(expenses['date']).dt.strftime('%Y-%m')
            time_analysis = expenses.groupby('month')['amount'].sum()
            
            # Find top spending categories
            top_categories = category_analysis.sort_values('sum', ascending=False).head(3)
            
            # Prepare analysis results
            analysis = {
                'top_categories': top_categories.to_dict(),
                'monthly_spending': time_analysis.to_dict(),
                'total_expenses': expenses['amount'].sum(),
                'transaction_count': len(expenses)
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing spending: {e}")
            return None
    
    def suggest_budget(self, transactions, income=None):
        """Suggest budget based on spending patterns"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(transactions)
            expenses = df[df['type'] == 'expense']
            
            # Calculate average monthly spending by category
            expenses['month'] = pd.to_datetime(expenses['date']).dt.strftime('%Y-%m')
            monthly_by_category = expenses.groupby(['month', 'category'])['amount'].sum().reset_index()
            avg_by_category = monthly_by_category.groupby('category')['amount'].mean()
            
            # If income is provided, calculate budget as percentage of income
            # Otherwise, use historical spending with small buffer
            budget_suggestions = {}
            
            if income:
                # Use 50/30/20 rule as a starting point
                # 50% needs, 30% wants, 20% savings
                needs_categories = ['Housing', 'Utilities', 'Groceries', 'Transportation', 'Healthcare']
                wants_categories = ['Entertainment', 'Shopping', 'Dining', 'Personal']
                
                needs_budget = income * 0.5
                wants_budget = income * 0.3
                savings = income * 0.2
                
                # Distribute based on historical spending ratios
                for category in avg_by_category.index:
                    if category in needs_categories:
                        category_ratio = avg_by_category[category] / avg_by_category[avg_by_category.index.isin(needs_categories)].sum()
                        budget_suggestions[category] = needs_budget * category_ratio
                    elif category in wants_categories:
                        category_ratio = avg_by_category[category] / avg_by_category[avg_by_category.index.isin(wants_categories)].sum()
                        budget_suggestions[category] = wants_budget * category_ratio
                    else:
                        budget_suggestions[category] = avg_by_category[category] * 1.1  # 10% buffer
                
                budget_suggestions['Savings'] = savings
                
            else:
                # Without income, suggest 10% less than average spending
                for category in avg_by_category.index:
                    budget_suggestions[category] = avg_by_category[category] * 0.9
            
            return budget_suggestions
            
        except Exception as e:
            print(f"Error suggesting budget: {e}")
            return None