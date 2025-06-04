from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
from io import BytesIO
from fpdf import FPDF
from ai_helper import AIExpenseAssistant

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')

# Initialize AI assistant - create a new instance
ai_assistant_obj = AIExpenseAssistant()

# MongoDB connection
client = MongoClient(os.environ.get('MONGO_URI', 'mongodb://localhost:27017/'))
db = client['expense_tracker']
users_collection = db['users']  
transactions_collection = db['transactions']
categories_collection = db['categories']

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        if users_collection.find_one({'email': email}):
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        user_id = users_collection.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.now()
        }).inserted_id
        
        # Add default expense categories for the user
        default_expense_categories = ['Food', 'Transportation', 'Housing', 'Utilities', 'Entertainment', 'Healthcare', 'Shopping', 'Personal', 'Education', 'Other']
        for category in default_expense_categories:
            categories_collection.insert_one({
                'user_id': str(user_id),
                'name': category,
                'type': 'expense'
            })
            
        # Add default income categories for the user
        default_income_categories = ['Salary', 'Freelance', 'Investments', 'Gifts', 'Other']
        for category in default_income_categories:
            categories_collection.insert_one({
                'user_id': str(user_id),
                'name': category,
                'type': 'income'
            })
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/admin')
def admin():
    # Check if user is admin
    if not session.get('is_admin'):
        flash('Access denied. Admin login required.', 'danger')
        return redirect(url_for('login'))
    
    # Get user statistics
    user_count = users_collection.count_documents({})
    
    # Get new users in the last 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    new_users_count = users_collection.count_documents({'created_at': {'$gte': seven_days_ago}})
    
    # Get transaction statistics
    transaction_count = transactions_collection.count_documents({})
    
    # Get active users in the last 30 days (users with transactions)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    active_user_ids = transactions_collection.distinct('user_id', {'date': {'$gte': thirty_days_ago}})
    active_users_count = len(active_user_ids)
    
    # Get all users with pagination
    users = list(users_collection.find().sort('created_at', -1))
    for user in users:
        user['_id'] = str(user['_id'])
    
    # Calculate total expenses and income
    total_expenses = sum(t['amount'] for t in transactions_collection.find({'type': 'expense'}))
    total_income = sum(t['amount'] for t in transactions_collection.find({'type': 'income'}))
    
    # Calculate average transactions per user
    avg_transactions_per_user = transaction_count / user_count if user_count > 0 else 0
    
    # Find most popular categories
    expense_categories = {}
    income_categories = {}
    
    for transaction in transactions_collection.find():
        if transaction['type'] == 'expense':
            category = transaction['category']
            expense_categories[category] = expense_categories.get(category, 0) + 1
        else:
            category = transaction['category']
            income_categories[category] = income_categories.get(category, 0) + 1
    
    most_popular_expense_category = max(expense_categories.items(), key=lambda x: x[1])[0] if expense_categories else 'None'
    most_popular_income_category = max(income_categories.items(), key=lambda x: x[1])[0] if income_categories else 'None'
    
    return render_template('admin.html', 
                          user_count=user_count,
                          transaction_count=transaction_count,
                          new_users_count=new_users_count,
                          active_users_count=active_users_count,
                          users=users,
                          total_expenses=f"₹{total_expenses:,.2f}",
                          total_income=f"₹{total_income:,.2f}",
                          avg_transactions_per_user=f"{avg_transactions_per_user:.1f}",
                          most_popular_expense_category=most_popular_expense_category,
                          most_popular_income_category=most_popular_income_category)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if it's the admin login
        if email == 'admin@et.com' and password == 'admin123':
            # Create a session for admin
            session['is_admin'] = True
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('admin'))
        
        user_data = users_collection.find_one({'email': email})
        
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # Clear admin session if exists
    if session.get('is_admin'):
        session.pop('is_admin', None)
    
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/budget')
@login_required
def budget():
    return render_template('budget.html')

@app.route('/ai_assistant')
@login_required
def ai_assistant():
    return render_template('ai_assistant.html')

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/account')
@login_required
def account():
    # Get user info from database
    user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})
    user_info = {}
    
    # Extract additional user info if available
    if 'fullname' in user_data:
        user_info['fullname'] = user_data['fullname']
    if 'phone' in user_data:
        user_info['phone'] = user_data['phone']
    if 'address' in user_data:
        user_info['address'] = user_data['address']
    if 'currency' in user_data:
        user_info['currency'] = user_data['currency']
    if 'default_view' in user_data:
        user_info['default_view'] = user_data['default_view']
    if 'notification' in user_data:
        user_info['notification'] = user_data['notification']
    
    return render_template('account.html', user_info=user_info)

# API Routes for Account Management
@app.route('/api/account/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.json
    
    # Update user profile in database
    result = users_collection.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$set': {
            'fullname': data.get('fullname', ''),
            'phone': data.get('phone', ''),
            'address': data.get('address', ''),
            'currency': data.get('currency', '₹')
        }}
    )
    
    if result.modified_count > 0:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'No changes were made'})

@app.route('/api/account/password', methods=['PUT'])
@login_required
def update_password():
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    # Get user from database
    user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})
    
    # Verify current password
    if not check_password_hash(user_data['password'], current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})
    
    # Update password
    hashed_password = generate_password_hash(new_password)
    result = users_collection.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$set': {'password': hashed_password}}
    )
    
    if result.modified_count > 0:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Failed to update password'})

@app.route('/api/account/preferences', methods=['PUT'])
@login_required
def update_preferences():
    data = request.json
    
    # Update user preferences in database
    result = users_collection.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$set': {
            'default_view': data.get('default_view', 'monthly'),
            'notification': data.get('notification', 'none')
        }}
    )
    
    if result.modified_count > 0:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'No changes were made'})

# API Routes for Transactions
@app.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    transaction_type = request.args.get('type', 'all')  # 'expense', 'income', or 'all'
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')
    
    # Build query
    query = {'user_id': current_user.id}
    
    if start_date and end_date:
        query['date'] = {
            '$gte': datetime.strptime(start_date, '%Y-%m-%d'),
            '$lte': datetime.strptime(end_date, '%Y-%m-%d')
        }
    
    if category and category != 'All':
        query['category'] = category
        
    if transaction_type and transaction_type != 'all':
        query['type'] = transaction_type
    
    if min_amount or max_amount:
        query['amount'] = {}
        if min_amount:
            query['amount']['$gte'] = float(min_amount)
        if max_amount:
            query['amount']['$lte'] = float(max_amount)
    
    # Get transactions
    transactions = list(transactions_collection.find(query).sort('date', -1))
    
    # Convert ObjectId to string for JSON serialization
    for transaction in transactions:
        transaction['_id'] = str(transaction['_id'])
        transaction['date'] = transaction['date'].strftime('%Y-%m-%d')
    
    return jsonify(transactions)

@app.route('/api/transactions', methods=['POST'])
@login_required
def add_transaction():
    data = request.json
    
    transaction = {
        'user_id': current_user.id,
        'title': data['title'],
        'amount': float(data['amount']),
        'category': data['category'],
        'type': data['type'],  # 'expense' or 'income'
        'date': datetime.strptime(data['date'], '%Y-%m-%d'),
        'description': data.get('description', ''),
        'created_at': datetime.now()
    }
    
    result = transactions_collection.insert_one(transaction)
    
    return jsonify({
        'success': True,
        'transaction_id': str(result.inserted_id)
    })

@app.route('/api/transactions/<transaction_id>', methods=['PUT'])
@login_required
def update_transaction(transaction_id):
    data = request.json
    
    # Ensure the transaction belongs to the current user
    transaction = transactions_collection.find_one({
        '_id': ObjectId(transaction_id),
        'user_id': current_user.id
    })
    
    if not transaction:
        return jsonify({'success': False, 'message': 'Transaction not found'}), 404
    
    update_data = {
        'title': data['title'],
        'amount': float(data['amount']),
        'category': data['category'],
        'type': data['type'],
        'date': datetime.strptime(data['date'], '%Y-%m-%d'),
        'description': data.get('description', '')
    }
    
    transactions_collection.update_one(
        {'_id': ObjectId(transaction_id)},
        {'$set': update_data}
    )
    
    return jsonify({'success': True})

@app.route('/api/transactions/<transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    # Ensure the transaction belongs to the current user
    result = transactions_collection.delete_one({
        '_id': ObjectId(transaction_id),
        'user_id': current_user.id
    })
    
    if result.deleted_count == 0:
        return jsonify({'success': False, 'message': 'Transaction not found'}), 404
    
    return jsonify({'success': True})

@app.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    category_type = request.args.get('type', 'all')  # 'expense', 'income', or 'all'
    
    if category_type == 'all':
        categories = list(categories_collection.find({'user_id': current_user.id}))
    else:
        categories = list(categories_collection.find({
            'user_id': current_user.id,
            'type': category_type
        }))
    
    # Convert ObjectId to string for JSON serialization
    for category in categories:
        category['_id'] = str(category['_id'])
    
    return jsonify(categories)

@app.route('/api/categories', methods=['POST'])
@login_required
def add_category():
    data = request.json
    
    # Check if category already exists
    if categories_collection.find_one({
        'user_id': current_user.id, 
        'name': data['name'],
        'type': data['type']
    }):
        return jsonify({'success': False, 'message': 'Category already exists'}), 400
    
    category = {
        'user_id': current_user.id,
        'name': data['name'],
        'type': data['type']  # 'expense' or 'income'
    }
    
    result = categories_collection.insert_one(category)
    
    return jsonify({
        'success': True,
        'category_id': str(result.inserted_id)
    })

@app.route('/api/ai_assistant', methods=['POST'])
@login_required
def process_ai_assistant():
    data = request.json
    user_message = data.get('message', '')
    
    # Get user's financial data for context
    user_data = {}
    
    # Get recent transactions
    transactions = list(transactions_collection.find({
        'user_id': current_user.id
    }).sort('date', -1).limit(50))
    
    # Convert ObjectId to string for JSON serialization
    for transaction in transactions:
        transaction['_id'] = str(transaction['_id'])
        transaction['date'] = transaction['date'].strftime('%Y-%m-%d')
    
    user_data['transactions'] = transactions
    
    # Get summary data
    today = datetime.now()
    start_date = datetime(today.year, today.month, 1)
    end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
    
    # Get transactions for the current month
    month_transactions = list(transactions_collection.find({
        'user_id': current_user.id,
        'date': {'$gte': start_date, '$lte': end_date}
    }))
    
    # Calculate summary
    expenses = [t for t in month_transactions if t['type'] == 'expense']
    incomes = [t for t in month_transactions if t['type'] == 'income']
    total_expenses = sum(expense['amount'] for expense in expenses)
    total_income = sum(income['amount'] for income in incomes)
    net_savings = total_income - total_expenses
    
    user_data['summary'] = {
        'total_expenses': total_expenses,
        'total_income': total_income,
        'net_savings': net_savings
    }
    
    # Get AI response using the object instance
    try:
        ai_response = ai_assistant_obj.get_response(user_message, user_data)
        return jsonify({
            'response': ai_response
        })
    except Exception as e:
        print(f"Error in AI assistant: {e}")
        return jsonify({
            'response': "I'm sorry, I encountered an error processing your request. Please try again later."
        }), 500

@app.route('/api/summary', methods=['GET'])
@login_required
def get_summary():
    # Get time period from query parameters (default to current month)
    period = request.args.get('period', 'month')
    
    # Calculate date range based on period
    today = datetime.now()
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'month':
        start_date = datetime(today.year, today.month, 1)
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
    elif period == 'year':
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31)
    else:  # Custom period
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
    
    # Get transactions for the period
    transactions = list(transactions_collection.find({
        'user_id': current_user.id,
        'date': {'$gte': start_date, '$lte': end_date}
    }))
    
    # Separate expenses and incomes
    expenses = [t for t in transactions if t['type'] == 'expense']
    incomes = [t for t in transactions if t['type'] == 'income']
    
    # Calculate totals
    total_expenses = sum(expense['amount'] for expense in expenses)
    total_income = sum(income['amount'] for income in incomes)
    net_savings = total_income - total_expenses
    
    # Calculate category-wise totals for expenses
    expense_category_totals = {}
    for expense in expenses:
        category = expense['category']
        if category in expense_category_totals:
            expense_category_totals[category] += expense['amount']
        else:
            expense_category_totals[category] = expense['amount']
    
    # Calculate category-wise totals for incomes
    income_category_totals = {}
    for income in incomes:
        category = income['category']
        if category in income_category_totals:
            income_category_totals[category] += income['amount']
        else:
            income_category_totals[category] = income['amount']
    
    # Calculate daily expenses and incomes for chart
    daily_expenses = {}
    daily_incomes = {}
    
    for transaction in transactions:
        date_str = transaction['date'].strftime('%Y-%m-%d')
        if transaction['type'] == 'expense':
            if date_str in daily_expenses:
                daily_expenses[date_str] += transaction['amount']
            else:
                daily_expenses[date_str] = transaction['amount']
        else:  # income
            if date_str in daily_incomes:
                daily_incomes[date_str] += transaction['amount']
            else:
                daily_incomes[date_str] = transaction['amount']
    
    # Sort daily transactions by date
    sorted_daily_expenses = {k: daily_expenses.get(k, 0) for k in sorted(set(daily_expenses.keys()) | set(daily_incomes.keys()))}
    sorted_daily_incomes = {k: daily_incomes.get(k, 0) for k in sorted(set(daily_expenses.keys()) | set(daily_incomes.keys()))}
    
    # Calculate average daily spending and income
    days_count = (end_date - start_date).days + 1
    avg_daily_spending = total_expenses / days_count if days_count > 0 else 0
    avg_daily_income = total_income / days_count if days_count > 0 else 0
    
    return jsonify({
        'total_expenses': total_expenses,
        'total_income': total_income,
        'net_savings': net_savings,
        'expense_category_totals': expense_category_totals,
        'income_category_totals': income_category_totals,
        'daily_expenses': sorted_daily_expenses,
        'daily_incomes': sorted_daily_incomes,
        'avg_daily_spending': avg_daily_spending,
        'avg_daily_income': avg_daily_income,
        'period': {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
    })

# Export routes
@app.route('/api/export/excel')
@login_required
def export_excel():
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    transaction_type = request.args.get('type', 'all')
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')
    
    # Build query
    query = {'user_id': current_user.id}
    
    if start_date and end_date:
        query['date'] = {
            '$gte': datetime.strptime(start_date, '%Y-%m-%d'),
            '$lte': datetime.strptime(end_date, '%Y-%m-%d')
        }
    
    if category and category != 'All':
        query['category'] = category
        
    if transaction_type and transaction_type != 'all':
        query['type'] = transaction_type
    
    if min_amount or max_amount:
        query['amount'] = {}
        if min_amount:
            query['amount']['$gte'] = float(min_amount)
        if max_amount:
            query['amount']['$lte'] = float(max_amount)
    
    # Get transactions
    transactions = list(transactions_collection.find(query).sort('date', -1))
    
    # Convert transactions to DataFrame
    data = []
    for transaction in transactions:
        data.append({
            'Date': transaction['date'].strftime('%Y-%m-%d'),
            'Title': transaction['title'],
            'Category': transaction['category'],
            'Type': transaction['type'].capitalize(),
            'Amount': transaction['amount'],
            'Description': transaction.get('description', '')
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Transactions', index=False)
        
        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Transactions']
        
        # Add a format for the header cells
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'border': 1
        })
        
        # Write the column headers with the defined format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Set column widths
        worksheet.set_column('A:A', 12)  # Date
        worksheet.set_column('B:B', 20)  # Title
        worksheet.set_column('C:C', 15)  # Category
        worksheet.set_column('D:D', 10)  # Type
        worksheet.set_column('E:E', 12)  # Amount
        worksheet.set_column('F:F', 30)  # Description
    
    output.seek(0)
    
    # Generate filename with date range
    filename = f"transactions_{start_date}_to_{end_date}.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/export/pdf')
@login_required
def export_pdf():
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    transaction_type = request.args.get('type', 'all')
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')
    
    # Build query
    query = {'user_id': current_user.id}
    
    if start_date and end_date:
        query['date'] = {
            '$gte': datetime.strptime(start_date, '%Y-%m-%d'),
            '$lte': datetime.strptime(end_date, '%Y-%m-%d')
        }
    
    if category and category != 'All':
        query['category'] = category
        
    if transaction_type and transaction_type != 'all':
        query['type'] = transaction_type
    
    if min_amount or max_amount:
        query['amount'] = {}
        if min_amount:
            query['amount']['$gte'] = float(min_amount)
        if max_amount:
            query['amount']['$lte'] = float(max_amount)
    
    # Get transactions
    transactions = list(transactions_collection.find(query).sort('date', -1))
    
    # Initialize PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Set font
    pdf.set_font('Arial', 'B', 16)
    
    # Title
    report_title = 'Financial Report'
    if transaction_type == 'expense':
        report_title = 'Expense Report'
    elif transaction_type == 'income':
        report_title = 'Income Report'
        
    pdf.cell(0, 10, report_title, 0, 1, 'C')
    pdf.cell(0, 10, f'From {start_date} to {end_date}', 0, 1, 'C')
    
    # Add user info
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'User: {current_user.username}', 0, 1)
    
    # Calculate totals
    expenses = [t for t in transactions if t['type'] == 'expense']
    incomes = [t for t in transactions if t['type'] == 'income']
    total_expenses = sum(expense['amount'] for expense in expenses)
    total_income = sum(income['amount'] for income in incomes)
    net_savings = total_income - total_expenses
    
    # Add summary
    pdf.cell(0, 10, f'Total Income: Rs. {total_income:.2f}', 0, 1)
    pdf.cell(0, 10, f'Total Expenses: Rs. {total_expenses:.2f}', 0, 1)
    pdf.cell(0, 10, f'Net Savings: Rs. {net_savings:.2f}', 0, 1)
    
    # Add line break
    pdf.ln(10)
    
    # Table header
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(25, 10, 'Date', 1, 0, 'C')
    pdf.cell(45, 10, 'Title', 1, 0, 'C')
    pdf.cell(35, 10, 'Category', 1, 0, 'C')
    pdf.cell(25, 10, 'Type', 1, 0, 'C')
    pdf.cell(25, 10, 'Amount', 1, 0, 'C')
    pdf.cell(35, 10, 'Description', 1, 1, 'C')
    
    # Table data
    pdf.set_font('Arial', '', 10)
    for transaction in transactions:
        pdf.cell(25, 10, transaction['date'].strftime('%Y-%m-%d'), 1, 0)
        pdf.cell(45, 10, transaction['title'], 1, 0)
        pdf.cell(35, 10, transaction['category'], 1, 0)
        pdf.cell(25, 10, transaction['type'].capitalize(), 1, 0)
        pdf.cell(25, 10, f"Rs. {transaction['amount']:.2f}", 1, 0)
        pdf.cell(35, 10, transaction.get('description', ''), 1, 1)
    
    # Generate PDF in memory
    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1'))
    pdf_output.seek(0)
    
    # Generate filename with date range
    filename = f"transactions_{start_date}_to_{end_date}.pdf"
    
    return send_file(
        pdf_output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

# API route for admin to delete users
@app.route('/api/admin/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Check if user is admin
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        # Delete user's transactions
        transactions_collection.delete_many({'user_id': user_id})
        
        # Delete user's categories
        categories_collection.delete_many({'user_id': user_id})
        
        # Delete the user
        result = users_collection.delete_one({'_id': ObjectId(user_id)})
        
        if result.deleted_count > 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)