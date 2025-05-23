# 💸 Expenses Tracker App

A simple and intuitive web application to manage and track your daily expenses. This app helps users log, categorize, and review their expenses over time using a clean and minimal interface.

---

## 🚀 Features

```markdown
- Add, edit, and delete expense records
- Categorize expenses (Food, Transport, Utilities, etc.)
- View a summary of total expenses
- Simple and clean HTML interface using Flask templates
- Lightweight and easy to set up
📁 Project Structure
plaintext
Copy
Edit
Expenses-Tracker-App/
├── app.py                  # Core Flask application
├── run.py                  # Script to run the application
├── add_categories.py       # Utility script to initialize categories
├── requirements.txt        # List of Python packages
├── templates/              # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   └── add_expense.html
└── README.md               # Project documentation

## 🛠 Installation Guide
# Step 1: Clone the repository
git clone https://github.com/MohammedFarhan1/Expenses-Tracker-App.git
cd Expenses-Tracker-App

# Step 2: Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4 (Optional): Seed categories
python add_categories.py

# Step 5: Run the app
python run.py

# Visit http://localhost:5000 in your web browser

## 🧰 Tech Stack
- Python 3.x
- Flask Web Framework
- SQLite Database (can be changed)
- HTML, CSS (via Jinja templates)

## 📌 Future Plans
- Implement user authentication (login, register)
- Add charts and analytics (monthly, category-wise)
- Export expense data to CSV or PDF
- Add mobile-responsive styling
- Deploy on platforms like Heroku or Render
- Add dark mode toggle

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
🙋‍♂️ Author

Developed by Mohammed Farhan  
GitHub: https://github.com/MohammedFarhan1

Pull requests and suggestions are welcome!
