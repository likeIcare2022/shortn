from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from validators import url as validate_url
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///url_shortener.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)


# Database model for URL storage
class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(2048), nullable=False)
    short_code = db.Column(db.String(20), unique=True, nullable=False)
    click_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"URL('{self.original_url}', '{self.short_code}')"


def generate_random_code():
    """Generate a random alphanumeric code."""
    characters = string.ascii_letters + string.digits
    code_length = 6  # Adjust the length of the generated code as needed
    return ''.join(random.choice(characters) for _ in range(code_length))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        original_url = request.form['url']
        custom_short_code = request.form.get('custom_short_code', None)

        if not validate_url(original_url):
            return "Invalid URL", 400

        if custom_short_code:
            if URL.query.filter_by(short_code=custom_short_code).first():
                return "Custom short code already exists. Please choose another one.", 400
            short_code = custom_short_code
        else:
            short_code = generate_random_code()
            while URL.query.filter_by(short_code=short_code).first():
                short_code = generate_random_code()

        # Save to database
        url_entry = URL(original_url=original_url, short_code=short_code)
        db.session.add(url_entry)
        db.session.commit()

        return f"Shortened URL: <a href='{request.host_url}{short_code}'>{request.host_url}{short_code}</a>"

    # Render the form directly in the script
    form_html = '''
    <html>
    <head><title>URL Shortener</title></head>
    <body>
        <h1>URL Shortener</h1>
        <form method="POST" action="/">
            <label for="url">Enter your URL:</label><br>
            <input type="text" id="url" name="url" required><br><br>
            <label for="custom_short_code">Custom Short Code (optional):</label><br>
            <input type="text" id="custom_short_code" name="custom_short_code"><br><br>
            <input type="submit" value="Shorten URL">
        </form>
    </body>
    </html>
    '''

    return render_template_string(form_html)


@app.route('/<short_code>')
def redirect_to_url(short_code):
    url_entry = URL.query.filter_by(short_code=short_code).first_or_404()
    url_entry.click_count += 1
    db.session.commit()
    return redirect(url_entry.original_url)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
