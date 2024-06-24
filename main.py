from flask import Flask, request, redirect, flash
import string
import random
import sqlite3
import os
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session

# SQLite database initialization
conn = sqlite3.connect('url_shortener.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS urls
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              original_url TEXT NOT NULL,
              short_code TEXT UNIQUE NOT NULL)''')
conn.commit()


def generate_short_code():
    characters = string.ascii_letters + string.digits
    while True:
        short_code = ''.join(random.choices(characters, k=6))  # Generate a 6-character code
        c.execute("SELECT id FROM urls WHERE short_code = ?", (short_code,))
        if c.fetchone() is None:
            return short_code


def insert_url(original_url, short_code):
    try:
        c.execute("INSERT INTO urls (original_url, short_code) VALUES (?, ?)", (original_url, short_code))
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    return True


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        original_url = request.form['url'].strip()  # Remove leading/trailing spaces
        custom_short_code = request.form['custom_code'].strip()  # Custom short code

        # If the URL does not start with 'http://' or 'https://', prepend 'http://'
        if not urlparse(original_url).scheme:
            original_url = 'http://' + original_url

        # Validate URL
        if not validate_url(original_url):
            flash('Invalid URL. Please enter a valid URL.', 'error')
            return redirect('/')

        # If custom short code is provided, use it; otherwise generate a new one
        if custom_short_code:
            if not is_valid_custom_code(custom_short_code):
                flash('Invalid custom code. Use only letters and digits.', 'error')
                return redirect('/')
            short_code = custom_short_code
        else:
            short_code = generate_short_code()

        # Try to insert URL into the database with the chosen short code
        if not insert_url(original_url, short_code):
            flash(f'Custom code "{short_code}" already exists. Please choose another.', 'error')
            return redirect('/')

        short_url = request.host_url + short_code
        return '''
        <h2>URL Shortener</h2>
        <p>Shortened URL: <a href="{0}">{0}</a></p>
        '''.format(short_url)

    return '''
    <h2>URL Shortener</h2>
    <form method="post" action="/">
        <label for="url">Enter your URL:</label><br>
        <input type="text" id="url" name="url" required><br><br>
        <label for="custom_code">Custom Short Code (optional):</label><br>
        <input type="text" id="custom_code" name="custom_code"><br><br>
        <input type="submit" value="Shorten URL">
    </form>
    '''


@app.route('/<short_code>')
def redirect_to_url(short_code):
    original_url = get_original_url(short_code)
    if original_url:
        return redirect(original_url)
    else:
        flash('URL not found!', 'error')
        return redirect('/')


def validate_url(url):
    # Basic URL validation using urlparse from urllib.parse
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def is_valid_custom_code(custom_code):
    # Check if the custom code only contains letters and digits
    return custom_code.isalnum()


def get_original_url(short_code):
    c.execute("SELECT original_url FROM urls WHERE short_code = ?", (short_code,))
    result = c.fetchone()
    return result[0] if result else None


if __name__ == '__main__':
    app.run(debug=True)
