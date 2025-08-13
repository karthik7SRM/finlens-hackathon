from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
app.secret_key = "supersecretkey"  # needed for session management

# ----------------- MySQL -----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="karthik",
    database="cashflow"
)
cursor = db.cursor(dictionary=True)

# ----------------- ML Model -----------------
df_model = pd.read_csv("finance.csv")
df_model.columns = df_model.columns.str.strip().str.lower()
numeric_cols = ['monthly_revenue', 'average_transaction', 'number_of_customer']
x = df_model[numeric_cols]
y = df_model['operational_cost']

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
model = LinearRegression()
model.fit(x_train, y_train)

# ----------------- Routes -----------------

# Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('loginpage.html', error="Please enter both fields.")

        query = "SELECT * FROM users WHERE name=%s AND pwd=%s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = username
            return redirect(url_for('predict'))
        else:
            return render_template('loginpage.html', error="Invalid username or password")

    return render_template('loginpage.html')


# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return render_template('signup.html', error="Please enter both fields.")

        query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        try:
            cursor.execute(query, (username, password))
            db.commit()
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            return render_template('signup.html', error=f"Error: {err}")

    return render_template('signup.html')


# CSV upload page
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('predict.html')


# Handle CSV upload and predict
@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'username' not in session:
        return redirect(url_for('login'))

    if 'csv_file' not in request.files:
        return "No file uploaded", 400

    file = request.files['csv_file']
    if file.filename == '':
        return "No selected file", 400

    try:
        df_csv = pd.read_csv(file)
        df_csv.columns = df_csv.columns.str.strip().str.lower()

        # Check numeric columns exist
        if not all(col in df_csv.columns for col in numeric_cols):
            return "CSV missing required columns", 400

        # Use first row for prediction
        mr = float(df_csv[numeric_cols[0]].iloc[0])
        at = float(df_csv[numeric_cols[1]].iloc[0])
        no = float(df_csv[numeric_cols[2]].iloc[0])

        predicted_value = model.predict([[mr, at, no]])
        prediction = f"Predicted Operational Cost: Rs {predicted_value[0]:,.2f}"

        return render_template('predictmodel.html', prediction=prediction)

    except Exception as e:
        return f"Error processing CSV: {e}", 500


if __name__ == '__main__':
    app.run(debug=True)
