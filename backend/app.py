import sqlite3
from sqlite3 import Error
import bcrypt
import re
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_session import Session
from datetime import timedelta  # Import timedelta
import base64
import io
import PyPDF2
from PyPDF2 import PdfReader

app = Flask(__name__)
app.secret_key = 'avellin'
CORS(app, supports_credentials=True)

# Configure server-side session storage
app.config['SESSION_TYPE'] = 'filesystem'  # You can also use 'redis', 'memcached', etc.
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'session:'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # Set session lifetime
Session(app)

def validate_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def validate_password(password):
    return (len(password) >= 8 and 
            any(c.isupper() for c in password) and 
            any(c.islower() for c in password) and 
            any(c.isdigit() for c in password))

@app.route('/register/talent', methods=['POST'])
def register_talent():
    data = request.get_json()
    
    # Extract and validate fields
    name = data.get('name', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    resume = data.get('resume')
    
    # Comprehensive validation
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    if not validate_password(password):
        return jsonify({'error': 'Password must be at least 8 characters and contain uppercase, lowercase, and number'}), 400
    
    if not phone:
        return jsonify({'error': 'Phone number is required'}), 400
    
    if not resume:
        return jsonify({'error': 'Resume link is required'}), 400

    talent = TalentRegister(name, password, email, phone, resume)
    result = talent.register()
    
    if result:
        return jsonify({'message': 'Talent registered successfully'}), 201
    else:
        return jsonify({'error': 'Email already exists'}), 409

@app.route('/login/talent', methods=['POST'])
def login_talent():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    transcript_data = data.get('transcript')  # This will be a dict with file info
    
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    with Database('KoraQuest.db') as db:
        talent = db.fetchone('SELECT * FROM Talent WHERE email = ?', (email,))
    
    if talent:
        hashed_password = talent[2]
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
            session['email'] = email
            
            # Process and update resume/transcript if provided
            if transcript_data:
                try:
                    # Extract text from PDF
                    extracted_text = extract_text_from_pdf(transcript_data['content'])
                    
                    if not extracted_text:
                        return jsonify({'error': 'Could not extract text from PDF'}), 400
                    
                    # Clean and store the extracted text
                    cleaned_text = clean_transcript_text(extracted_text)
                    
                    with Database('KoraQuest.db') as db:
                        db.execute('''
                            UPDATE Talent 
                            SET resume = ? 
                            WHERE email = ?
                        ''', (cleaned_text, email))
                        
                except Exception as e:
                    print(f"Error processing PDF: {e}")
                    return jsonify({'error': 'Failed to process PDF file'}), 500
            
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'error': 'Incorrect password'}), 401
    else:
        return jsonify({'error': 'Email not found'}), 404

def extract_text_from_pdf(base64_content):
    """Extract text from a base64-encoded PDF file."""
    try:
        # Decode base64 content
        pdf_bytes = base64.b64decode(base64_content)
        pdf_file = io.BytesIO(pdf_bytes)
        
        # Create PDF reader object
        pdf_reader = PdfReader(pdf_file)
        
        # Extract text from all pages
        text_content = []
        for page in pdf_reader.pages:
            text_content.append(page.extract_text())
        
        return '\n'.join(text_content)
        
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def clean_transcript_text(text):
    """Clean and validate transcript text content."""
    if not text or not isinstance(text, str):
        return ""
    
    # Remove any null bytes
    text = text.replace('\x00', '')
    
    # Remove excessive whitespace while preserving paragraphs
    paragraphs = text.split('\n')
    cleaned_paragraphs = [' '.join(p.split()) for p in paragraphs if p.strip()]
    text = '\n'.join(cleaned_paragraphs)
    
    # Remove any non-printable characters
    text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\t'])
    
    # Limit the text length if needed (adjust the limit as needed)
    max_length = 1000000  # 1 million characters
    if len(text) > max_length:
        text = text[:max_length]
    
    return text

# Add a route to view the stored transcript
@app.route('/get/transcript', methods=['GET'])
def get_transcript():
    if 'email' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    email = session['email']
    
    with Database('KoraQuest.db') as db:
        talent = db.fetchone('SELECT resume FROM Talent WHERE email = ?', (email,))
        
    if talent and talent[0]:
        # Format the text for better readability
        formatted_text = format_transcript_text(talent[0])
        return jsonify({
            'transcript': formatted_text,
            'raw_transcript': talent[0]
        }), 200
    else:
        return jsonify({'error': 'No transcript found'}), 404

def format_transcript_text(text):
    """Format the transcript text for better readability."""
    if not text:
        return ""
    
    # Split into paragraphs
    paragraphs = text.split('\n')
    
    # Remove empty paragraphs and add proper spacing
    formatted_paragraphs = []
    for p in paragraphs:
        if p.strip():
            # Remove excessive spaces while preserving intentional indentation
            cleaned_p = re.sub(r'\s+', ' ', p).strip()
            formatted_paragraphs.append(cleaned_p)
    
    return '\n\n'.join(formatted_paragraphs)

@app.route('/register/organization', methods=['POST'])
def register_organization():
    data = request.get_json()
    
    # Extract and validate fields
    org_names = data.get('name', '').strip()
    org_password = data.get('password', '')
    org_email = data.get('email', '').strip()
    org_phone = data.get('phone', '').strip()
    
    # Comprehensive validation
    if not org_names:
        return jsonify({'error': 'Organization name is required'}), 400
    
    if not validate_email(org_email):
        return jsonify({'error': 'Invalid email format'}), 400
      
    if not validate_password(org_password):
        return jsonify({'error': 'Password must be at least 8 characters and contain uppercase, lowercase, and number'}), 400

    organization = Organization(org_names, org_password, org_email, org_phone)
    result = organization.register()
    
    if result:
        return jsonify({'message': 'Organization registered successfully'}), 201
    else:
        return jsonify({'error': 'Organization name or email already exists'}), 409

@app.route('/login/organization', methods=['POST'])
def login_organization():
    data = request.get_json()
    org_email = data.get('email', '').strip()
    org_password = data.get('password', '').strip()
    
    if not validate_email(org_email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    with Database('KoraQuest.db') as db:
        organization = db.fetchone('SELECT * FROM Organization WHERE org_email = ?', (org_email,))
    
    if organization:
        hashed_password = organization[2]
        if bcrypt.checkpw(org_password.encode('utf-8'), hashed_password):
            session.permanent = True
            session['org_email'] = org_email
            with Database('KoraQuest.db') as db:
                org_names = db.fetchone('SELECT org_names FROM Organization WHERE org_email = ?', (org_email,))
            session['org_names'] = org_names[0]
            print("Session set:", session)
            return jsonify({'message': 'Login successful', 'org_email': org_email}), 200
        else:
            return jsonify({'error': 'Incorrect password'}), 401
    else:
        return jsonify({'error': 'Email not found'}), 404 

@app.route('/post/job', methods=['POST'])
def post_job():
    if 'org_email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    
    org_email = session.get('org_email')
    org_names = session.get('org_names')
    job_title = data.get('title', '').strip()
    job_description = data.get('description', '').strip()
    job_location = data.get('place', '').strip()
    job_type = data.get('jobType', '').strip()
    is_remote = 1 if data.get('isremote', False) else 0  # Convert boolean to INTEGER

    if not all([job_title, job_description, job_location, job_type]):
        return jsonify({'error': 'All fields are required'}), 400

    try:
        with Database('KoraQuest.db') as db:
            db.execute('''
                INSERT INTO Jobs (
                    org_email, job_title, job_description, job_location, 
                    job_type, is_remote, org_names, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                org_email, job_title, job_description, job_location,
                job_type, is_remote, org_names, 'created'
            ))
            
        return jsonify({'message': 'Job posted successfully'}), 201
    except Exception as e:
        print(f"Error posting job: {e}")
        return jsonify({'error': 'Failed to post job'}), 500

@app.route('/jobs', methods=['GET'])
def get_jobs():
    with Database('KoraQuest.db') as db:
        jobs = db.fetchall('SELECT * FROM Jobs')
    jobs_list = []
    for job in jobs:
        job_dict = {
            'id': job[0],
            'org_email': job[1],
            'job_title': job[2],
            'job_description': job[3],
            'job_location': job[4],
            'job_type': job[5],
            'is_remote': job[6],
            'org_name': job[7],
        }
        jobs_list.append(job_dict)
    
    return jsonify(jobs_list), 200

@app.route('/local_search/jobs', methods=['POST'])
def search_local():
    data = request.get_json()
    job_location = data.get('location', '').strip()
    job_type = data.get('jobType', '').strip()
    is_remote = data.get('isremote', False)
    job_title = data.get('title', '').strip()
    with Database('KoraQuest.db') as db:
        jobs = db.fetchall('SELECT * FROM Jobs WHERE job_location = ? AND job_type = ? AND is_remote = ? AND job_title = ?', (job_location, job_type, is_remote, job_title))
    jobs_list = []
    for job in jobs:
        job_dict = {
            'id': job[0],
            'org_email': job[1],
            'job_title': job[2],
            'job_description': job[3],
            'job_location': job[4],
            'job_type': job[5],
            'is_remote': job[6],
            'org_name': job[7],
        }
        jobs_list.append(job_dict)
    return jsonify(jobs_list), 200

@app.route('/apply/job', methods=['POST'])
def apply_job():
    data = request.get_json()
    
    # Extract and validate fields
    talent_email = data.get('talent_email', '').strip()
    job_id = data.get('job_id', '')
    
    # Comprehensive validation
    if not talent_email:
        return jsonify({'error': 'Talent email is required'}), 400
    
    if not job_id:
        return jsonify({'error': 'Job ID is required'}), 400
    
    with Database('KoraQuest.db') as db:
        job = db.fetchone('SELECT * FROM Jobs WHERE id = ?', (job_id,))
    
    if job:
        return jsonify({'message': 'Job application successful'}), 200
    else:
        return jsonify({'error': 'Job ID not found'}), 404

@app.route('/organization/applications', methods=['GET'])
def view_applications():
    org_email = session.get('org_email')
    if not org_email:
        print('no org_email')
        return jsonify({'error': 'Unauthorized'}), 401

    with Database('KoraQuest.db') as db:
        applications = db.fetchall('SELECT * FROM Jobs WHERE org_email = ?', (org_email,))
    
    applications_list = []
    for application in applications:
        application_dict = {
            'id': application[0],
            'org_email': application[1],
            'job_title': application[2]
        }
        applications_list.append(application_dict)
    
    print("Applications:", applications_list)
    return jsonify(applications_list), 200

class Database:
    def __init__(self, db_file):
        self.db_file = db_file

    def __enter__(self):
        self.connection = sqlite3.connect(self.db_file)
        self.cursor = self.connection.cursor()
        self.cursor.execute('PRAGMA foreign_keys = ON')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.cursor.close()
            self.connection.close()

    def execute(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return True
        except Error as err:
            print(f"Error: {err}")
            return False

    def fetchone(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetchall(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

class TalentRegister:
    def __init__(self, name, password, email, phone, resume):
        self.name = name
        self.password = password
        self.email = email
        self.phone = phone
        self.resume = resume

    def register(self):
        hashed_password = bcrypt.hashpw(self.password.encode('utf-8'), bcrypt.gensalt())
        with Database('KoraQuest.db') as db:
            if db.fetchone('SELECT * FROM Talent WHERE email = ?', (self.email,)):
                return False
            return db.execute('''
                INSERT INTO Talent (name, password, email, phone, resume) VALUES (?, ?, ?, ?, ?)
            ''', (self.name, hashed_password, self.email, self.phone, self.resume))

class Organization:
    def __init__(self, org_names, org_password, org_email, org_phone):
        self.org_names = org_names
        self.org_password = org_password
        self.org_email = org_email
        self.org_phone = org_phone

    def register(self):
        hashed_password = bcrypt.hashpw(self.org_password.encode('utf-8'), bcrypt.gensalt())
        with Database('KoraQuest.db') as db:
            if db.fetchone('SELECT * FROM Organization WHERE org_email = ? OR org_names = ?', (self.org_email, self.org_names)):
                return False
            return db.execute('''
                INSERT INTO Organization (org_names, org_password, org_email) VALUES (?, ?, ?)
            ''', (self.org_names, hashed_password, self.org_email))

class Jobs:
    def __init__(self, org_email, job_title, job_description, job_location, job_type, is_remote, org_names):
        self.org_email = org_email
        self.job_title = job_title
        self.job_description = job_description
        self.job_location = job_location
        self.job_type = job_type
        self.is_remote = is_remote
        self.org_names = org_names

    def post(self):
        with Database('KoraQuest.db') as db:
            return db.execute('''
                INSERT INTO Jobs (org_email, job_title, job_description, job_location, job_type, is_remote, org_names) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.org_email, self.job_title, self.job_description, self.job_location, self.job_type, self.is_remote, self.org_names))

def create_tables():
    with Database('KoraQuest.db') as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS Talent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL,
                resume TEXT NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS Organization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_names TEXT NOT NULL UNIQUE,
                org_password TEXT NOT NULL,
                org_email TEXT NOT NULL UNIQUE
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS Jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_email TEXT NOT NULL,
                job_title TEXT NOT NULL,
                job_description TEXT NOT NULL,
                job_location TEXT NOT NULL,
                job_type TEXT NOT NULL,
                is_remote BOOLEAN NOT NULL,
                org_names TEXT NOT NULL,
                source TEXT NOT NULL,  -- 'created' or 'fetched'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                external_job_id TEXT,  -- For tracking external job IDs
                job_url TEXT,          -- Original job posting URL if fetched
                FOREIGN KEY (org_email) REFERENCES Organization (org_email)
            )
        ''')

def create_database():
    try:
        conn = sqlite3.connect('KoraQuest.db')
        cursor = conn.cursor()

        # Update Jobs table with new fields
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_email TEXT NOT NULL,
            job_title TEXT NOT NULL,
            job_description TEXT NOT NULL,
            job_location TEXT NOT NULL,
            job_type TEXT NOT NULL,
            is_remote BOOLEAN NOT NULL,
            org_names TEXT NOT NULL,
            source TEXT NOT NULL,  -- 'created' or 'fetched'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            external_job_id TEXT,  -- For tracking external job IDs
            job_url TEXT,          -- Original job posting URL if fetched
            FOREIGN KEY (org_email) REFERENCES Organization (org_email)
        )
        ''')

        conn.commit()
        print("Database tables updated successfully!")

    except sqlite3.Error as e:
        print(f"Error updating database: {e}")
    finally:
        if conn:
            conn.close()

@app.route('/search/jobs', methods=['GET'])
def search_jobs():
    search_query = request.args.get('q', '').strip()
    job_type = request.args.get('type', '').strip()
    location = request.args.get('location', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    try:
        # First, fetch from external API
        external_jobs = fetch_external_jobs(search_query, job_type, location)
        
        # Store the fetched jobs
        if external_jobs:
            store_fetched_jobs(external_jobs)
        
        # Then proceed with database search as before
        with Database('KoraQuest.db') as db:
            # Build the base query
            query = "SELECT * FROM Jobs WHERE 1=1"
            params = []
            
            # Add search conditions
            if search_query:
                query += " AND (job_title LIKE ? OR job_description LIKE ?)"
                search_term = f"%{search_query}%"
                params.extend([search_term, search_term])
            
            if job_type:
                query += " AND job_type = ?"
                params.append(job_type)
                
            if location:
                query += " AND job_location LIKE ?"
                params.append(f"%{location}%")
            
            # Add ordering and pagination
            query += " ORDER BY created_at DESC, id DESC"  # Fallback to id if created_at is null
            query += " LIMIT ? OFFSET ?"
            params.extend([per_page, (page - 1) * per_page])
            
            # Execute the search
            jobs = db.fetchall(query, tuple(params))
            
            # Get total count for pagination
            count_query = query.split(' LIMIT')[0].replace('SELECT *', 'SELECT COUNT(*)')
            total_count = db.fetchone(count_query, tuple(params[:-2]))[0]
            
            # Format the results
            formatted_jobs = []
            for job in jobs:
                job_dict = {
                    'id': job[0],
                    'org_email': job[1],
                    'job_title': job[2],
                    'job_description': job[3],
                    'job_location': job[4],
                    'job_type': job[5],
                    'is_remote': bool(job[6]),
                    'org_names': job[7],
                    'source': job[8] if len(job) > 8 else 'created',
                    'created_at': job[9] if len(job) > 9 else None,
                    'external_job_id': job[10] if len(job) > 10 else None,
                    'job_url': job[11] if len(job) > 11 else None
                }
                formatted_jobs.append(job_dict)
            
            return jsonify({
                'jobs': formatted_jobs,
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            }), 200
            
    except Exception as e:
        print(f"Error searching jobs: {e}")
        return jsonify({'error': 'Failed to search jobs'}), 500

def fetch_external_jobs(query, job_type, location):
    """Fetch jobs from external API and format them properly"""
    try:
        # Make request to your external API
        # Process the response
        # Return formatted jobs data
        pass
    except Exception as e:
        print(f"Error fetching external jobs: {e}")
        return None

# Function to store fetched jobs
def store_fetched_jobs(jobs_data):
    """Store fetched jobs in the Jobs table."""
    try:
        with Database('KoraQuest.db') as db:
            for job in jobs_data:
                # Check if job already exists
                existing_job = db.fetchone('''
                    SELECT id FROM Jobs 
                    WHERE external_job_id = ? OR 
                          (job_title = ? AND org_names = ? AND job_location = ?)
                ''', (
                    job.get('external_job_id'),
                    job.get('job_title'),
                    job.get('org_names'),
                    job.get('job_location')
                ))

                if not existing_job:
                    db.execute('''
                        INSERT INTO Jobs (
                            org_email, job_title, job_description, job_location,
                            job_type, is_remote, org_names, source, external_job_id, job_url
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        job.get('org_email', 'external@company.com'),
                        job.get('job_title'),
                        job.get('job_description'),
                        job.get('job_location'),
                        job.get('job_type'),
                        1 if job.get('is_remote', False) else 0,  # Convert boolean to INTEGER
                        job.get('org_names'),
                        'fetched',
                        job.get('external_job_id'),
                        job.get('job_url')
                    ))
        return True
    except Exception as e:
        print(f"Error storing fetched jobs: {e}")
        return False

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)