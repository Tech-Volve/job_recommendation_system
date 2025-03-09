import sqlite3
from sqlite3 import Error
import bcrypt
import re
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import base64
import io
import PyPDF2
from PyPDF2 import PdfReader
import requests
import uuid
import time
import json

app = Flask(__name__)
app.secret_key = 'avellin'
CORS(app, supports_credentials=True)

# Simpler session configuration
app.config['SESSION_TYPE'] = 'filesystem'

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def execute(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def fetchone(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

# Initialize database and tables at startup
def init_db():
    print("Initializing database...")
    try:
        with Database('KoraQuest.db') as db:
            # Create Talent table
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
            
            # Create Organization table
            db.execute('''
            CREATE TABLE IF NOT EXISTS Organization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_names TEXT NOT NULL UNIQUE,
                org_password TEXT NOT NULL,
                org_email TEXT NOT NULL UNIQUE
            )
            ''')
            
            # Create Jobs table with corrected column names
            db.execute('''
            DROP TABLE IF EXISTS Jobs;
            ''')
            
            db.execute('''
            CREATE TABLE IF NOT EXISTS Jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_email TEXT,
                job_title TEXT NOT NULL,
                job_description TEXT,
                job_location TEXT,
                job_type TEXT,
                is_remote INTEGER,
                org_name TEXT,  -- Changed from org_names to org_name
                source TEXT DEFAULT 'created',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                external_job_id TEXT UNIQUE,
                job_url TEXT
            )
            ''')
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")

# Call initialization
init_db()

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
    
    print(f"\nProcessing local job search request:")
    print(f"Title: {job_title}")
    print(f"Location: {job_location}")
    print(f"Job Type: {job_type}")
    
    try:
        # First, fetch from external API and store immediately
        print("Fetching jobs from external API...")
        external_jobs = fetch_external_jobs(job_title, job_type, job_location)
        
        if external_jobs:
            print(f"Found {len(external_jobs)} jobs from external API")
            # Store the fetched jobs FIRST
            stored_count = store_fetched_jobs(external_jobs)
            print(f"Stored {stored_count} new jobs in database")
        else:
            print("No new jobs found from external API")
            
        # Now search in database with better matching
        with Database('KoraQuest.db') as db:
            query = """
                SELECT * FROM Jobs 
                WHERE 1=1 
                AND (
                    LOWER(job_title) LIKE LOWER(?) 
                    OR LOWER(job_description) LIKE LOWER(?)
                )
            """
            search_term = f"%{job_title}%"
            params = [search_term, search_term]
            
            if job_type:
                query += " AND LOWER(job_type) LIKE LOWER(?)"
                params.append(f"%{job_type}%")
                
            if job_location:
                query += " AND LOWER(job_location) LIKE LOWER(?)"
                params.append(f"%{job_location}%")
            
            if is_remote:
                query += " AND is_remote = 1"
            
            # Add ordering by created_at
            query += " ORDER BY created_at DESC"
            
            # Execute the search
            jobs = db.fetchall(query, tuple(params))
            print(f"Found {len(jobs)} matching jobs in database")
            
            # Format the results
            jobs_list = []
            for job in jobs:
                job_dict = {
                    'id': job[0],
                    'org_email': job[1],
                    'job_title': job[2],
                    'job_description': job[3],
                    'job_location': job[4],
                    'job_type': job[5],
                    'is_remote': bool(job[6]),
                    'org_name': job[7],
                    'source': job[8] if len(job) > 8 else 'created',
                    'created_at': job[9] if len(job) > 9 else None,
                    'external_job_id': job[10] if len(job) > 10 else None,
                    'job_url': job[11] if len(job) > 11 else None
                }
                jobs_list.append(job_dict)
            
            return jsonify(jobs_list), 200
            
    except Exception as e:
        print(f"Error searching jobs: {e}")
        return jsonify({'error': 'Failed to search jobs'}), 500

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

def store_fetched_jobs(jobs):
    """Store jobs fetched from external API in the database"""
    stored_count = 0
    print(f"\n=== Storing Jobs in Database ===")
    print(f"Attempting to store {len(jobs)} jobs from external API")
    
    with Database('KoraQuest.db') as db:
        # First, let's verify the database connection
        try:
            test_query = "SELECT COUNT(*) FROM Jobs"
            count = db.fetchone(test_query)[0]
            print(f"Current number of jobs in database: {count}")
        except Exception as e:
            print(f"Error checking database: {e}")
            return 0

        for job in jobs:
            try:
                # Generate a unique ID if none exists
                external_id = job.get('external_job_id') or job.get('id') or str(uuid.uuid4())
                
                print(f"\nProcessing job: {job.get('title')} at {job.get('company')}")
                # Check if job already exists
                existing_job = db.fetchone(
                    """
                    SELECT id FROM Jobs 
                    WHERE external_job_id = ? 
                    OR (
                        LOWER(job_title) = LOWER(?) 
                        AND LOWER(job_location) = LOWER(?)
                        AND org_name = ?
                    )
                    """, 
                    (
                        external_id,
                        job.get('title', ''),
                        job.get('location', ''),
                        job.get('company', '')
                    )
                )
                
                if existing_job:
                    print(f"Job already exists in database with ID: {existing_job[0]}")
                else:
                    print("Job is new, inserting into database...")
                    db.execute('''
                    INSERT INTO Jobs (
                        job_title, job_description, job_location, job_type,
                        is_remote, org_name, source, external_job_id, job_url,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        job.get('title', ''),
                        job.get('description', ''),
                        job.get('location', ''),
                        job.get('job_type', 'Full Time'),
                        1 if job.get('is_remote') else 0,
                        job.get('company', ''),
                        'external_api',
                        external_id,
                        job.get('job_url', '')
                    ))
                    stored_count += 1
                    print(f"Successfully stored job in database")
            except Exception as e:
                print(f"Error storing job: {e}")
                print(f"Job data that caused error: {job}")
                continue
    
    print(f"\nFinal Results:")
    print(f"Successfully stored {stored_count} new jobs in database")
    
    # Verify final count
    with Database('KoraQuest.db') as db:
        try:
            final_count = db.fetchone("SELECT COUNT(*) FROM Jobs")[0]
            print(f"Total jobs now in database: {final_count}")
        except Exception as e:
            print(f"Error getting final count: {e}")
    
    return stored_count

@app.route('/search/jobs', methods=['GET'])
def search_jobs():
    search_query = request.args.get('q', '').strip()
    job_type = request.args.get('type', '').strip()
    location = request.args.get('location', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    print(f"\nProcessing job search request:")
    print(f"Query: {search_query}")
    print(f"Location: {location}")
    print(f"Job Type: {job_type}")
    
    try:
        # First, fetch from external API and store immediately
        print("Fetching jobs from external API...")
        external_jobs = fetch_external_jobs(search_query, job_type, location)
        
        if external_jobs:
            print(f"Found {len(external_jobs)} jobs from external API")
            # Store the fetched jobs FIRST
            stored_count = store_fetched_jobs(external_jobs)
            print(f"Stored {stored_count} new jobs in database")
        else:
            print("No new jobs found from external API")
        
        # Now search in database including the newly stored jobs
        with Database('KoraQuest.db') as db:
            # Build the base query with better search conditions
            query = """
                SELECT * FROM Jobs 
                WHERE 1=1 
                AND (
                    LOWER(job_title) LIKE LOWER(?) 
                    OR LOWER(job_description) LIKE LOWER(?)
                )
            """
            search_term = f"%{search_query}%"
            params = [search_term, search_term]
            
            if job_type:
                query += " AND LOWER(job_type) = LOWER(?)"
                params.append(job_type)
                
            if location:
                query += " AND LOWER(job_location) LIKE LOWER(?)"
                params.append(f"%{location}%")
            
            # Get total count first
            count_query = "SELECT COUNT(*) FROM (" + query + ")"
            total_count = db.fetchone(count_query, tuple(params))[0]
            print(f"Total matching jobs in database: {total_count}")
            
            # Add ordering and pagination
            query += " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
            params.extend([per_page, (page - 1) * per_page])
            
            # Execute the search
            jobs = db.fetchall(query, tuple(params))
            print(f"Returning {len(jobs)} jobs for current page")
            
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
                    'org_name': job[7],
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
        print("\n=== Fetching External Jobs ===")
        print(f"Search Query: {query}")
        print(f"Job Type: {job_type}")
        print(f"Location: {location}")
        
        # Prepare request data
        request_data = {
            'search_term': query or 'software',
            'location': location or 'mumbai',
            'results_wanted': 10,  # Reduced to improve response time
            'site_name': [
                'indeed',
                'linkedin'  # Reduced sites to improve reliability
            ],
            'distance': 25,  # Reduced distance to improve response time
            'job_type': job_type.lower().replace(' ', '') if job_type else 'fulltime',
            'is_remote': False,
            'linkedin_fetch_description': True,
            'hours_old': 168  # Last 7 days
        }

        print("Making API request with data:", request_data)
        
        # Make request to external API with retries
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    'https://jobs-search-api.p.rapidapi.com/getjobs',
                    headers={
                        'x-rapidapi-key': '8ec0ed2528mshdbc246edfb4c888p1d4a42jsn6450870c3cc0',
                        'x-rapidapi-host': 'jobs-search-api.p.rapidapi.com',
                        'Content-Type': 'application/json'
                    },
                    json=request_data,
                    timeout=15  # Reduced timeout
                )
                
                print(f"API Response Status: {response.status_code}")
                
                if response.status_code == 429:
                    print("Rate limit exceeded. Waiting before retry...")
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                
                if not response.ok:
                    print(f"API request failed with status {response.status_code}")
                    print(f"Response content: {response.text}")
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                
                try:
                    response_data = response.json()
                    if not response_data or 'jobs' not in response_data:
                        print("No jobs found in API response")
                        return None
                    
                    # Format jobs for our database
                    formatted_jobs = []
                    for job in response_data['jobs']:
                        try:
                            # Skip jobs without required fields
                            if not job.get('title') or not job.get('company'):
                                continue
                                
                            formatted_job = {
                                'title': job.get('title', '').strip(),
                                'description': job.get('description', '').strip(),
                                'location': job.get('location', '').strip(),
                                'company': job.get('company', '').strip(),
                                'job_type': job.get('job_type', 'Full Time').strip(),
                                'is_remote': bool(job.get('is_remote', False)),
                                'external_job_id': job.get('job_id') or str(uuid.uuid4()),
                                'job_url': job.get('url') or job.get('job_url', ''),
                                'source': 'external_api'
                            }
                            
                            formatted_jobs.append(formatted_job)
                            print(f"Formatted job: {formatted_job['title']} at {formatted_job['company']}")
                            
                        except Exception as e:
                            print(f"Error formatting job: {e}")
                            continue
                    
                    print(f"Successfully formatted {len(formatted_jobs)} jobs")
                    return formatted_jobs
                    
                except json.JSONDecodeError as e:
                    print(f"Failed to parse response as JSON: {e}")
                    print(f"Raw response content: {response.text}")
                    time.sleep(retry_delay * (attempt + 1))
                    continue

            except requests.exceptions.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                return None

        print("All retry attempts failed")
        return None

    except Exception as e:
        print(f"Error fetching external jobs: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True)