from app import db, users_collection, categories_collection

# Add default categories for all users
for user in users_collection.find():
    user_id = str(user['_id'])
    
    # Check if user already has categories
    if not categories_collection.find_one({'user_id': user_id}):
        print(f'Adding categories for user {user_id}')
        
        # Add default expense categories
        default_expense_categories = ['Food', 'Transportation', 'Housing', 'Utilities', 'Entertainment', 'Healthcare', 'Shopping', 'Personal', 'Education', 'Other']
        for category in default_expense_categories:
            categories_collection.insert_one({
                'user_id': user_id,
                'name': category,
                'type': 'expense'
            })
        
        # Add default income categories
        default_income_categories = ['Salary', 'Freelance', 'Investments', 'Gifts', 'Other']
        for category in default_income_categories:
            categories_collection.insert_one({
                'user_id': user_id,
                'name': category,
                'type': 'income'
            })
        
        print('Categories added successfully')
    else:
        print(f'User {user_id} already has categories')

print('Done')