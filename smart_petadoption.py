#!/usr/bin/env python3
"""
Smart Pet Adoption Shelter - Complete Fixed Version
"""

import sys
import sqlite3
import hashlib
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Fix Windows Unicode encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Database setup
DB_NAME = 'pets.db'

def init_database():
    """Initialize SQLite database with required tables and sample data"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            user_type TEXT NOT NULL CHECK(user_type IN ('admin', 'adopter')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create animals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS animals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            breed TEXT NOT NULL,
            color TEXT NOT NULL,
            age_months INTEGER NOT NULL,
            gender TEXT NOT NULL CHECK(gender IN ('Male', 'Female')),
            vaccinated INTEGER NOT NULL CHECK(vaccinated IN (0, 1)),
            activity_level TEXT NOT NULL CHECK(activity_level IN ('Low', 'Medium', 'High')),
            weight_kg REAL NOT NULL,
            description TEXT,
            profile_photo_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create adoption_applications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adoption_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adopter_id INTEGER NOT NULL,
            animal_id INTEGER NOT NULL,
            adopter_name TEXT NOT NULL,
            pet_name TEXT NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (adopter_id) REFERENCES users(id),
            FOREIGN KEY (animal_id) REFERENCES animals(id)
        )
    ''')
    
    # Insert default admin user
    admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash, user_type)
        VALUES (?, ?, ?, ?)
    ''', ('admin', 'admin@shelter.com', admin_password, 'admin'))
    
    # Insert sample adopter user
    adopter_password = hashlib.sha256('user123'.encode()).hexdigest()
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash, user_type)
        VALUES (?, ?, ?, ?)
    ''', ('user', 'user@example.com', adopter_password, 'adopter'))
    
    # Check if animals already exist
    cursor.execute('SELECT COUNT(*) FROM animals')
    if cursor.fetchone()[0] == 0:
        # Insert sample pets - 7 Dogs and 5 Cats
        sample_pets = [
            # 7 Dogs of different breeds
            ('Max', 'Dog', 'Golden Retriever', 'Golden', 24, 'Male', 1, 'High', 30.5, 
             'Friendly and energetic golden retriever who loves to play fetch!', 
             'https://images.unsplash.com/photo-1633722715463-d30f4f325e24?w=400'),
            ('Charlie', 'Dog', 'Labrador', 'Black', 36, 'Male', 1, 'High', 32.0, 
             'Loyal and intelligent lab, great with families and children.', 
             'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400'),
            ('Rocky', 'Dog', 'German Shepherd', 'Brown', 48, 'Male', 1, 'High', 38.5, 
             'Protective and loyal German Shepherd, needs experienced owner.', 
             'https://images.unsplash.com/photo-1568572933382-74d440642117?w=400'),
            ('Daisy', 'Dog', 'Beagle', 'Tricolor', 15, 'Female', 1, 'Medium', 12.0, 
             'Sweet beagle puppy with lots of energy and curiosity.', 
             'https://images.unsplash.com/photo-1505628346881-b72b27e84530?w=400'),
            ('Buddy', 'Dog', 'Poodle', 'White', 20, 'Male', 1, 'Medium', 15.0, 
             'Smart and hypoallergenic poodle, perfect for families with allergies.', 
             'https://images.unsplash.com/photo-1616940844649-535215ae4eb1?w=400'),
            ('Duke', 'Dog', 'Bulldog', 'Brindle', 28, 'Male', 1, 'Low', 25.0, 
             'Laid-back bulldog with a sweet temperament, great for apartments.', 
             'https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=400'),
            ('Cooper', 'Dog', 'Husky', 'Gray & White', 30, 'Male', 1, 'High', 28.0, 
             'Energetic Siberian Husky with striking blue eyes, loves cold weather and running.', 
             'https://images.unsplash.com/photo-1605568427561-40dd23c2acea?w=400'),
            
            # 5 Cats of different breeds
            ('Luna', 'Cat', 'Siamese', 'Cream', 18, 'Female', 1, 'Medium', 4.2, 
             'Elegant Siamese cat with beautiful blue eyes and a gentle personality.', 
             'https://images.unsplash.com/photo-1513360371669-4adf3dd7dff8?w=400'),
            ('Bella', 'Cat', 'Persian', 'White', 12, 'Female', 1, 'Low', 3.8, 
             'Calm and affectionate Persian cat, perfect for quiet homes.', 
             'https://images.unsplash.com/photo-1595433707802-6b2626ef1c91?w=400'),
            ('Whiskers', 'Cat', 'Maine Coon', 'Orange', 30, 'Male', 1, 'Medium', 6.5, 
             'Large and fluffy Maine Coon with a playful personality.', 
             'https://images.unsplash.com/photo-1574158622682-e40e69881006?w=400'),
            ('Shadow', 'Cat', 'British Shorthair', 'Gray', 24, 'Male', 1, 'Low', 5.5, 
             'Calm and independent British Shorthair, great for apartments.', 
             'https://images.unsplash.com/photo-1596854407944-bf87f6fdd49e?w=400'),
            ('Cleo', 'Cat', 'Bengal', 'Spotted', 14, 'Female', 1, 'High', 4.5, 
             'Active and playful Bengal cat with beautiful spotted coat.', 
             'https://images.unsplash.com/photo-1606214174585-fe31582dc6ee?w=400')
        ]
        
        cursor.executemany('''
            INSERT INTO animals (name, species, breed, color, age_months, gender, 
                               vaccinated, activity_level, weight_kg, description, profile_photo_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_pets)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

# API Handler Functions
def handle_login(data):
    username = data.get('username')
    password = data.get('password')
    user_type = data.get('user_type')
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, user_type FROM users WHERE username = ? AND password_hash = ? AND user_type = ?', 
                   (username, password_hash, user_type))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {'success': True, 'user': {'id': user[0], 'username': user[1], 'email': user[2], 'user_type': user[3]}}
    return {'success': False, 'message': 'Invalid credentials'}

def handle_register(data):
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, email, password_hash, user_type) VALUES (?, ?, ?, 'adopter')", 
                       (username, email, password_hash))
        conn.commit()
        conn.close()
        return {'success': True}
    except sqlite3.IntegrityError:
        return {'success': False, 'message': 'Username or email already exists'}

def handle_get_pets():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, species, breed, color, age_months, gender, vaccinated, activity_level, weight_kg, description, profile_photo_url FROM animals')
    pets = []
    for row in cursor.fetchall():
        pets.append({'id': row[0], 'name': row[1], 'species': row[2], 'breed': row[3], 'color': row[4], 
                    'age_months': row[5], 'gender': row[6], 'vaccinated': bool(row[7]), 'activity_level': row[8], 
                    'weight_kg': row[9], 'description': row[10], 'profile_photo_url': row[11]})
    conn.close()
    return {'success': True, 'pets': pets}

def handle_add_pet(data):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO animals (name, species, breed, color, age_months, gender, vaccinated, activity_level, weight_kg, description, profile_photo_url)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (data['name'], data['species'], data['breed'], data['color'], int(data['age_months']), data['gender'], 
                       int(data['vaccinated']), data['activity_level'], float(data['weight_kg']), data['description'], data['profile_photo_url']))
        conn.commit()
        conn.close()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'message': str(e)}

def handle_get_requests():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, adopter_name, pet_name, applied_at, status FROM adoption_applications ORDER BY applied_at DESC')
    requests = []
    for row in cursor.fetchall():
        requests.append({'id': row[0], 'adopter_name': row[1], 'pet_name': row[2], 'applied_at': row[3], 'status': row[4]})
    conn.close()
    return {'success': True, 'requests': requests}

def handle_adopt_pet(data):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO adoption_applications (adopter_id, animal_id, adopter_name, pet_name) VALUES (?, ?, ?, ?)',
                      (data['adopter_id'], data['animal_id'], data['adopter_name'], data['pet_name']))
        conn.commit()
        conn.close()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'message': str(e)}

def handle_compatibility_check(data):
    pet_id = data.get('pet_id')
    has_yard = data.get('has_yard') == 'yes'
    has_children = data.get('has_children') == 'yes'
    has_other_pets = data.get('has_other_pets') == 'yes'
    experience_level = data.get('experience_level')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT species, activity_level, age_months FROM animals WHERE id = ?', (pet_id,))
    pet = cursor.fetchone()
    conn.close()
    if not pet:
        return {'success': False, 'message': 'Pet not found'}
    species, activity_level, age_months = pet
    score = 100
    reasons = []
    if activity_level == 'High' and not has_yard:
        score -= 20
        reasons.append("High-energy pets benefit from having a yard")
    elif activity_level == 'High' and has_yard:
        reasons.append("Great match! This pet will love your yard")
    if experience_level == 'Beginner' and activity_level == 'High':
        score -= 15
        reasons.append("High-energy pets may be challenging for beginners")
    elif experience_level == 'Experienced':
        score += 10
        reasons.append("Your experience is perfect for any pet")
    if has_children and age_months < 12:
        score -= 10
        reasons.append("Young pets may need extra supervision around children")
    elif has_children:
        reasons.append("This pet's age is good for families with children")
    if has_other_pets:
        if species == 'Dog':
            reasons.append("Dogs usually adapt well to other pets")
        else:
            score -= 5
            reasons.append("Cats may need gradual introduction to other pets")
    score = max(0, min(100, score))
    if score >= 80:
        message = "Excellent match! This pet would be perfect for you."
    elif score >= 60:
        message = "Good match! This pet would fit well in your home."
    elif score >= 40:
        message = "Fair match. Consider the factors below carefully."
    else:
        message = "This pet may not be the best fit, but adoption is always possible with proper preparation."
    return {'success': True, 'compatibility_percentage': score, 'message': message, 'reasons': reasons}

# Embedded HTML Frontend
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Smart Pet Adoption Shelter</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
<style>
body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh}
.landing-container{display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px}
.landing-card{background:white;border-radius:20px;padding:60px 40px;box-shadow:0 20px 60px rgba(0,0,0,0.3);text-align:center;max-width:600px;width:100%}
.landing-title{font-size:2.5rem;font-weight:bold;color:#333;margin-bottom:20px}
.role-btn{width:100%;padding:25px;font-size:1.3rem;font-weight:600;border-radius:15px;border:none;margin:15px 0;transition:all 0.3s;display:flex;align-items:center;justify-content:center;gap:15px;cursor:pointer}
.admin-btn{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white}
.adopter-btn{background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white}
.auth-container{max-width:450px;margin:50px auto;padding:20px}
.auth-card{background:white;border-radius:20px;padding:40px;box-shadow:0 20px 60px rgba(0,0,0,0.3)}
.dashboard-container{background:#f8f9fa;min-height:100vh}
.navbar-custom{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:15px 0}
.pet-card{background:white;border-radius:15px;overflow:hidden;box-shadow:0 4px 15px rgba(0,0,0,0.1);transition:all 0.3s;height:100%}
.pet-card:hover{transform:translateY(-10px);box-shadow:0 8px 25px rgba(0,0,0,0.2)}
.pet-card-img{width:100%;height:250px;object-fit:cover}
.pet-card-body{padding:20px}
.btn-primary-custom{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border:none;padding:10px 25px;border-radius:10px;font-weight:600;color:white}
.hidden{display:none!important}
.nav-link{cursor:pointer}
.filter-section{background:white;padding:25px;border-radius:15px;margin-bottom:30px}
.modal-backdrop{background-color:rgba(0,0,0,0.5)}
</style>
</head>
<body>
<div id="landingPage" class="landing-container">
<div class="landing-card">
<h1 class="landing-title">🐾 Smart Pet Adoption</h1>
<p class="landing-subtitle">Find your perfect companion or manage your shelter</p>
<button class="role-btn admin-btn" onclick="showAdminAuth()"><i class="bi bi-shield-check"></i><span>Admin (Shelter Owner)</span></button>
<button class="role-btn adopter-btn" onclick="showAdopterChoice()"><i class="bi bi-heart"></i><span>Adopt (Client/Buyer)</span></button>
</div>
</div>
<div id="adminAuthPage" class="auth-container hidden">
<div class="auth-card">
<h2 class="text-center mb-4">Admin Login</h2>
<form id="adminLoginForm">
<div class="mb-3"><label>Username</label><input type="text" class="form-control" id="adminUsername" required></div>
<div class="mb-3"><label>Password</label><input type="password" class="form-control" id="adminPassword" required></div>
<button type="submit" class="btn btn-primary-custom w-100">Login</button>
<button type="button" class="btn btn-link w-100" onclick="showLanding()">Back</button>
</form>
</div>
</div>
<div id="adopterChoicePage" class="auth-container hidden">
<div class="auth-card">
<h2 class="text-center mb-4">Welcome!</h2>
<button class="btn btn-primary-custom w-100 mb-3" onclick="showAdopterSignIn()">Sign In</button>
<button class="btn btn-outline-primary w-100 mb-3" onclick="showAdopterSignUp()">Sign Up</button>
<button type="button" class="btn btn-link w-100" onclick="showLanding()">Back</button>
</div>
</div>
<div id="adopterSignInPage" class="auth-container hidden">
<div class="auth-card">
<h2 class="text-center mb-4">Sign In</h2>
<form id="adopterSignInForm">
<div class="mb-3"><label>Username</label><input type="text" class="form-control" id="signInUsername" required></div>
<div class="mb-3"><label>Password</label><input type="password" class="form-control" id="signInPassword" required></div>
<button type="submit" class="btn btn-primary-custom w-100">Sign In</button>
<button type="button" class="btn btn-link w-100" onclick="showAdopterChoice()">Back</button>
</form>
</div>
</div>
<div id="adopterSignUpPage" class="auth-container hidden">
<div class="auth-card">
<h2 class="text-center mb-4">Sign Up</h2>
<form id="adopterSignUpForm">
<div class="mb-3"><label>Username</label><input type="text" class="form-control" id="signUpUsername" required></div>
<div class="mb-3"><label>Email</label><input type="email" class="form-control" id="signUpEmail" required></div>
<div class="mb-3"><label>Password</label><input type="password" class="form-control" id="signUpPassword" required></div>
<button type="submit" class="btn btn-primary-custom w-100">Sign Up</button>
<button type="button" class="btn btn-link w-100" onclick="showAdopterChoice()">Back</button>
</form>
</div>
</div>
<div id="adminDashboard" class="dashboard-container hidden">
<nav class="navbar navbar-custom navbar-dark">
<div class="container-fluid">
<span class="navbar-brand mb-0 h1">🐾 Admin Dashboard</span>
<button class="btn btn-light" onclick="logout()">Logout</button>
</div>
</nav>
<div class="container-fluid py-4">
<ul class="nav nav-tabs mb-3">
<li class="nav-item"><a class="nav-link active" data-tab="pets" onclick="switchAdminTab('pets')">Pets</a></li>
<li class="nav-item"><a class="nav-link" data-tab="addPet" onclick="switchAdminTab('addPet')">Add Pet</a></li>
<li class="nav-item"><a class="nav-link" data-tab="requests" onclick="switchAdminTab('requests')">Requests</a></li>
</ul>
<div id="adminPetsTab"><div id="adminPetGrid" class="row g-4"></div></div>
<div id="adminAddPetTab" class="hidden">
<div class="bg-white p-4 rounded">
<h3>Add New Pet</h3>
<form id="addPetForm">
<div class="row">
<div class="col-md-6 mb-3"><label>Name</label><input type="text" class="form-control" name="name" required></div>
<div class="col-md-6 mb-3"><label>Species</label><select class="form-select" name="species" required><option value="">Select...</option><option value="Dog">Dog</option><option value="Cat">Cat</option></select></div>
<div class="col-md-6 mb-3"><label>Breed</label><input type="text" class="form-control" name="breed" required></div>
<div class="col-md-6 mb-3"><label>Color</label><input type="text" class="form-control" name="color" required></div>
<div class="col-md-6 mb-3"><label>Age (months)</label><input type="number" class="form-control" name="age_months" min="1" required></div>
<div class="col-md-6 mb-3"><label>Gender</label><select class="form-select" name="gender" required><option value="">Select...</option><option value="Male">Male</option><option value="Female">Female</option></select></div>
<div class="col-md-6 mb-3"><label>Vaccinated</label><select class="form-select" name="vaccinated" required><option value="">Select...</option><option value="1">Yes</option><option value="0">No</option></select></div>
<div class="col-md-6 mb-3"><label>Activity Level</label><select class="form-select" name="activity_level" required><option value="">Select...</option><option value="Low">Low</option><option value="Medium">Medium</option><option value="High">High</option></select></div>
<div class="col-md-6 mb-3"><label>Weight (kg)</label><input type="number" class="form-control" name="weight_kg" step="0.1" min="0.1" required></div>
<div class="col-md-6 mb-3"><label>Photo URL</label><input type="url" class="form-control" name="profile_photo_url" required></div>
<div class="col-12 mb-3"><label>Description</label><textarea class="form-control" name="description" rows="3" required></textarea></div>
</div>
<button type="submit" class="btn btn-primary-custom">Add Pet</button>
</form>
</div>
</div>
<div id="adminRequestsTab" class="hidden">
<div class="bg-white rounded p-3">
<table class="table">
<thead><tr><th>ID</th><th>Adopter</th><th>Pet</th><th>Date</th><th>Status</th></tr></thead>
<tbody id="requestsTableBody"></tbody>
</table>
</div>
</div>
</div>
</div>
<div id="adopterDashboard" class="dashboard-container hidden">
<nav class="navbar navbar-custom navbar-dark">
<div class="container-fluid">
<span class="navbar-brand mb-0 h1">🐾 Find Your Perfect Pet</span>
<button class="btn btn-light" onclick="logout()">Logout</button>
</div>
</nav>
<div class="container-fluid py-4">
<!-- Debug Tools -->
<div class="alert alert-info alert-dismissible fade show" role="alert">
<strong>Welcome!</strong> Browse our available pets below. Use filters to find your perfect match.
<button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>

<div class="filter-section">
<h5>Filter Pets</h5>
<div class="row g-3">
<div class="col-md-2"><label>Species</label><select class="form-select" id="filterSpecies" onchange="applyFilters()"><option value="">All</option><option value="Dog">Dog</option><option value="Cat">Cat</option></select></div>
<div class="col-md-2"><label>Breed</label><input type="text" class="form-control" id="filterBreed" onkeyup="applyFilters()" placeholder="Any"></div>
<div class="col-md-2"><label>Color</label><input type="text" class="form-control" id="filterColor" onkeyup="applyFilters()" placeholder="Any"></div>
<div class="col-md-2"><label>Min Age</label><input type="number" class="form-control" id="filterMinAge" onchange="applyFilters()" placeholder="0" min="0"></div>
<div class="col-md-2"><label>Max Age</label><input type="number" class="form-control" id="filterMaxAge" onchange="applyFilters()" placeholder="999" min="1"></div>
<div class="col-md-2"><label>Gender</label><select class="form-select" id="filterGender" onchange="applyFilters()"><option value="">All</option><option value="Male">Male</option><option value="Female">Female</option></select></div>
<div class="col-md-2"><label>Vaccinated</label><select class="form-select" id="filterVaccinated" onchange="applyFilters()"><option value="">All</option><option value="1">Yes</option><option value="0">No</option></select></div>
<div class="col-md-2"><label>Activity</label><select class="form-select" id="filterActivity" onchange="applyFilters()"><option value="">All</option><option value="Low">Low</option><option value="Medium">Medium</option><option value="High">High</option></select></div>
<div class="col-md-2 d-flex align-items-end"><button class="btn btn-secondary w-100" onclick="clearFilters()">Clear Filters</button></div>
</div>
</div>
<div id="adopterPetGrid" class="row g-4"></div>
</div>
</div>

<!-- Pet Detail Modal -->
<div class="modal fade" id="petDetailModal" tabindex="-1" aria-hidden="true">
<div class="modal-dialog modal-lg">
<div class="modal-content">
<div class="modal-header bg-primary text-white">
<h5 class="modal-title" id="petDetailName">Pet Details</h5>
<button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
</div>
<div class="modal-body">
<div class="row">
<div class="col-md-5">
<img id="petDetailImage" class="img-fluid rounded" alt="Pet Image" style="width:100%;height:300px;object-fit:cover">
</div>
<div class="col-md-7">
<div id="petDetailInfo"></div>
<div class="bg-light p-3 rounded mt-3">
<h6>Diet Plan</h6>
<div id="petDetailDiet"></div>
</div>
</div>
</div>
</div>
<div class="modal-footer" id="petDetailFooter">
<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
</div>
</div>
</div>
</div>

<!-- Compatibility Modal -->
<div class="modal fade" id="compatibilityModal" tabindex="-1" aria-hidden="true">
<div class="modal-dialog">
<div class="modal-content">
<div class="modal-header bg-primary text-white">
<h5 class="modal-title">Check Compatibility</h5>
<button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
</div>
<div class="modal-body">
<form id="compatibilityForm">
<div class="mb-3"><label>Do you have a yard?</label><select class="form-select" name="has_yard" required><option value="">Select...</option><option value="yes">Yes</option><option value="no">No</option></select></div>
<div class="mb-3"><label>Do you have children?</label><select class="form-select" name="has_children" required><option value="">Select...</option><option value="yes">Yes</option><option value="no">No</option></select></div>
<div class="mb-3"><label>Do you have other pets?</label><select class="form-select" name="has_other_pets" required><option value="">Select...</option><option value="yes">Yes</option><option value="no">No</option></select></div>
<div class="mb-3"><label>Experience Level</label><select class="form-select" name="experience_level" required><option value="">Select...</option><option value="Beginner">Beginner</option><option value="Intermediate">Intermediate</option><option value="Experienced">Experienced</option></select></div>
<button type="submit" class="btn btn-primary-custom w-100">Check Compatibility</button>
</form>
</div>
</div>
</div>
</div>

<!-- Compatibility Result Modal -->
<div class="modal fade" id="compatibilityResultModal" tabindex="-1" aria-hidden="true">
<div class="modal-dialog">
<div class="modal-content">
<div class="modal-header bg-primary text-white">
<h5 class="modal-title">Compatibility Result</h5>
<button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
</div>
<div class="modal-body">
<div style="font-size:3rem;font-weight:bold;text-align:center;margin:30px 0" id="compatibilityScore"></div>
<div id="compatibilityDetails"></div>
</div>
<div class="modal-footer">
<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
</div>
</div>
</div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
let currentUser = null;
let allPets = [];
let filteredPets = [];
let currentPetForCompatibility = null;

// Initialize Bootstrap modals
let petDetailModal = null;
let compatibilityModal = null;
let compatibilityResultModal = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    petDetailModal = new bootstrap.Modal(document.getElementById('petDetailModal'));
    compatibilityModal = new bootstrap.Modal(document.getElementById('compatibilityModal'));
    compatibilityResultModal = new bootstrap.Modal(document.getElementById('compatibilityResultModal'));
    console.log('Modals initialized successfully');
});

// Navigation functions
function showLanding() { 
    hideAll(); 
    document.getElementById('landingPage').classList.remove('hidden'); 
}
function showAdminAuth() { 
    hideAll(); 
    document.getElementById('adminAuthPage').classList.remove('hidden'); 
}
function showAdopterChoice() { 
    hideAll(); 
    document.getElementById('adopterChoicePage').classList.remove('hidden'); 
}
function showAdopterSignIn() { 
    hideAll(); 
    document.getElementById('adopterSignInPage').classList.remove('hidden'); 
}
function showAdopterSignUp() { 
    hideAll(); 
    document.getElementById('adopterSignUpPage').classList.remove('hidden'); 
}
function hideAll() { 
    document.querySelectorAll('.landing-container, .auth-container, .dashboard-container').forEach(e => e.classList.add('hidden')); 
}
function logout() { 
    currentUser = null; 
    showLanding(); 
}

// Admin tab switching
function switchAdminTab(tab) {
    console.log('Switching to tab:', tab);
    document.querySelectorAll('.nav-link').forEach(e => e.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    
    document.getElementById('adminPetsTab').classList.add('hidden');
    document.getElementById('adminAddPetTab').classList.add('hidden');
    document.getElementById('adminRequestsTab').classList.add('hidden');
    
    if (tab === 'pets') {
        document.getElementById('adminPetsTab').classList.remove('hidden');
        loadPets('admin');
    } else if (tab === 'addPet') {
        document.getElementById('adminAddPetTab').classList.remove('hidden');
    } else if (tab === 'requests') {
        document.getElementById('adminRequestsTab').classList.remove('hidden');
        loadRequests();
    }
}

// Form event listeners
document.getElementById('adminLoginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = document.getElementById('adminUsername').value;
    const password = document.getElementById('adminPassword').value;
    
    console.log('Admin login attempt:', username);
    
    const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, user_type: 'admin' })
    });
    
    const data = await response.json();
    console.log('Admin login response:', data);
    
    if (data.success) {
        currentUser = data.user;
        hideAll();
        document.getElementById('adminDashboard').classList.remove('hidden');
        loadPets('admin');
    } else {
        alert(data.message || 'Login failed');
    }
});

document.getElementById('adopterSignInForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = document.getElementById('signInUsername').value;
    const password = document.getElementById('signInPassword').value;
    
    console.log('Adopter login attempt:', username);
    
    const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, user_type: 'adopter' })
    });
    
    const data = await response.json();
    console.log('Adopter login response:', data);
    
    if (data.success) {
        currentUser = data.user;
        hideAll();
        document.getElementById('adopterDashboard').classList.remove('hidden');
        // Small delay to ensure DOM is ready
        setTimeout(() => {
            loadPets('adopter');
        }, 100);
    } else {
        alert(data.message || 'Login failed');
    }
});

document.getElementById('adopterSignUpForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = document.getElementById('signUpUsername').value;
    const email = document.getElementById('signUpEmail').value;
    const password = document.getElementById('signUpPassword').value;
    
    console.log('Adopter signup attempt:', username, email);
    
    const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
    });
    
    const data = await response.json();
    console.log('Adopter signup response:', data);
    
    if (data.success) {
        alert('Registration successful! Please sign in.');
        showAdopterSignIn();
    } else {
        alert(data.message || 'Registration failed');
    }
});

document.getElementById('addPetForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    console.log('Adding pet:', data);
    
    const response = await fetch('/api/pets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    
    const result = await response.json();
    console.log('Add pet response:', result);
    
    if (result.success) {
        alert('Pet added successfully!');
        e.target.reset();
        switchAdminTab('pets');
    } else {
        alert(result.message || 'Failed to add pet');
    }
});

// Pet management functions
async function loadPets(type) {
    console.log('Loading pets for:', type);
    
    try {
        const response = await fetch('/api/pets');
        console.log('API response status:', response.status);
        
        const data = await response.json();
        console.log('Pets data received:', data);
        
        if (data.success) {
            allPets = data.pets || [];
            filteredPets = [...allPets];
            console.log(`Loaded ${allPets.length} pets`);
            displayPets(type);
        } else {
            console.error('Failed to load pets:', data.message);
            alert('Failed to load pets: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error loading pets:', error);
        alert('Error loading pets. Check console for details.');
    }
}

function displayPets(type) {
    console.log('Displaying pets for:', type, 'Count:', filteredPets.length);
    
    const grid = type === 'admin' 
        ? document.getElementById('adminPetGrid') 
        : document.getElementById('adopterPetGrid');
    
    if (!grid) {
        console.error('Grid element not found for type:', type);
        return;
    }
    
    grid.innerHTML = '';
    
    if (filteredPets.length === 0) {
        grid.innerHTML = `
            <div class="col-12 text-center">
                <div class="alert alert-info">
                    <h5>No pets found</h5>
                    <p>Try adjusting your filters or check back later for new arrivals.</p>
                </div>
            </div>`;
        return;
    }
    
    filteredPets.forEach(pet => {
        // Create a safe version of the pet object for onclick
        const safePet = {
            id: pet.id,
            name: pet.name,
            species: pet.species,
            breed: pet.breed,
            color: pet.color,
            age_months: pet.age_months,
            gender: pet.gender,
            vaccinated: pet.vaccinated,
            activity_level: pet.activity_level,
            weight_kg: pet.weight_kg,
            description: pet.description,
            profile_photo_url: pet.profile_photo_url
        };
        
        const cardHtml = `
            <div class="col-md-3">
                <div class="pet-card">
                    <img src="${pet.profile_photo_url}" class="pet-card-img" alt="${pet.name}" 
                         onerror="this.src='https://images.unsplash.com/photo-1560743641-3914f2c45636?w=400'">
                    <div class="pet-card-body">
                        <div style="font-size:1.5rem;font-weight:bold">${pet.name}</div>
                        <div class="mb-2">
                            <span class="badge bg-primary">${pet.species}</span> 
                            <span class="badge bg-info">${pet.breed}</span>
                        </div>
                        <div class="mb-2">
                            <small>${pet.age_months} months | ${pet.gender}</small>
                        </div>
                        <button class="btn btn-sm btn-primary-custom w-100 mb-2" 
                                onclick="showPetDetail(${JSON.stringify(safePet).replace(/"/g, '&quot;')})">
                            View Details
                        </button>
                        ${type === 'adopter' ? `
                            <button class="btn btn-sm btn-success w-100" 
                                    onclick="adoptPet(${pet.id}, '${pet.name.replace(/'/g, "\\'")}')">
                                Adopt
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>`;
        grid.innerHTML += cardHtml;
    });
    
    console.log('Pets displayed successfully');
}

function showPetDetail(pet) {
    console.log('Showing pet details:', pet.name);
    
    // Update modal content
    document.getElementById('petDetailName').textContent = pet.name;
    document.getElementById('petDetailImage').src = pet.profile_photo_url;
    
    // Calculate RER (Resting Energy Requirement)
    const rer = 70 * Math.pow(pet.weight_kg, pet.species === 'Dog' ? 0.75 : 0.67);
    
    document.getElementById('petDetailInfo').innerHTML = `
        <p><strong>Species:</strong> ${pet.species}</p>
        <p><strong>Breed:</strong> ${pet.breed}</p>
        <p><strong>Color:</strong> ${pet.color}</p>
        <p><strong>Age:</strong> ${pet.age_months} months</p>
        <p><strong>Gender:</strong> ${pet.gender}</p>
        <p><strong>Vaccinated:</strong> ${pet.vaccinated ? 'Yes' : 'No'}</p>
        <p><strong>Activity Level:</strong> ${pet.activity_level}</p>
        <p><strong>Weight:</strong> ${pet.weight_kg} kg</p>
        <p><strong>Description:</strong> ${pet.description}</p>
    `;
    
    document.getElementById('petDetailDiet').innerHTML = `
        <p><strong>RER:</strong> ${rer.toFixed(0)} kcal/day</p>
        <p><strong>Daily Energy Requirements:</strong></p>
        <ul>
            <li>Active: ${(1.6 * rer).toFixed(0)} kcal/day</li>
            <li>Neutered Adult: ${(1.2 * rer).toFixed(0)} kcal/day</li>
            <li>Weight Loss: ${(1.0 * rer).toFixed(0)} kcal/day</li>
        </ul>
    `;
    
    // Update footer buttons for adopters
    const footer = document.getElementById('petDetailFooter');
    if (currentUser && currentUser.user_type === 'adopter') {
        footer.innerHTML = `
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            <button class="btn btn-primary-custom" onclick="checkCompatibility(${pet.id})">Check Compatibility</button>
            <button class="btn btn-success" onclick="adoptPet(${pet.id}, '${pet.name.replace(/'/g, "\\'")}')">Adopt Now</button>
        `;
    } else {
        footer.innerHTML = `
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        `;
    }
    
    // Show the modal
    if (petDetailModal) {
        petDetailModal.show();
    } else {
        console.error('Pet detail modal not initialized');
    }
}

function checkCompatibility(petId) {
    console.log('Checking compatibility for pet ID:', petId);
    currentPetForCompatibility = petId;
    
    // Close pet detail modal first
    if (petDetailModal) {
        petDetailModal.hide();
    }
    
    // Show compatibility modal after a short delay
    setTimeout(() => {
        if (compatibilityModal) {
            compatibilityModal.show();
        }
    }, 300);
}

document.getElementById('compatibilityForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    data.pet_id = currentPetForCompatibility;
    
    console.log('Compatibility check data:', data);
    
    const response = await fetch('/api/ai/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    
    const result = await response.json();
    console.log('Compatibility result:', result);
    
    if (result.success) {
        const score = result.compatibility_percentage;
        const colorClass = score >= 80 ? 'text-success' : 
                          score >= 60 ? 'text-primary' : 
                          score >= 40 ? 'text-warning' : 'text-danger';
        
        document.getElementById('compatibilityScore').innerHTML = 
            `<span class="${colorClass}">${score}%</span>`;
        
        document.getElementById('compatibilityDetails').innerHTML = `
            <p><strong>${result.message}</strong></p>
            <h6>Key Factors:</h6>
            <ul class="list-group">
                ${result.reasons.map(reason => `<li class="list-group-item">${reason}</li>`).join('')}
            </ul>
        `;
        
        if (compatibilityModal) {
            compatibilityModal.hide();
        }
        
        setTimeout(() => {
            if (compatibilityResultModal) {
                compatibilityResultModal.show();
            }
        }, 300);
    } else {
        alert(result.message || 'Compatibility check failed');
    }
});

async function adoptPet(petId, petName) {
    if (!currentUser) {
        alert('Please login first');
        return;
    }
    
    console.log('Adoption request:', { petId, petName, user: currentUser });
    
    if (!confirm(`Are you sure you want to adopt ${petName}?`)) {
        return;
    }
    
    const response = await fetch('/api/adopt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            adopter_id: currentUser.id,
            animal_id: petId,
            adopter_name: currentUser.username,
            pet_name: petName
        })
    });
    
    const data = await response.json();
    console.log('Adoption response:', data);
    
    if (data.success) {
        alert(`Adoption request for ${petName} submitted successfully!`);
        if (petDetailModal) {
            petDetailModal.hide();
        }
    } else {
        alert(data.message || 'Adoption request failed');
    }
}

async function loadRequests() {
    console.log('Loading adoption requests');
    
    const response = await fetch('/api/requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}'
    });
    
    const data = await response.json();
    console.log('Requests data:', data);
    
    const tableBody = document.getElementById('requestsTableBody');
    tableBody.innerHTML = '';
    
    if (data.success && data.requests.length > 0) {
        data.requests.forEach(request => {
            const statusClass = request.status === 'approved' ? 'bg-success' : 
                              request.status === 'rejected' ? 'bg-danger' : 'bg-warning';
            
            tableBody.innerHTML += `
                <tr>
                    <td>${request.id}</td>
                    <td>${request.adopter_name}</td>
                    <td>${request.pet_name}</td>
                    <td>${new Date(request.applied_at).toLocaleDateString()}</td>
                    <td><span class="badge ${statusClass}">${request.status}</span></td>
                </tr>
            `;
        });
    } else {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">
                    No adoption requests found
                </td>
            </tr>
        `;
    }
}

// Filter functions
function applyFilters() {
    const speciesFilter = document.getElementById('filterSpecies').value;
    const breedFilter = document.getElementById('filterBreed').value.toLowerCase();
    const colorFilter = document.getElementById('filterColor').value.toLowerCase();
    const minAge = parseInt(document.getElementById('filterMinAge').value) || 0;
    const maxAge = parseInt(document.getElementById('filterMaxAge').value) || 999;
    const genderFilter = document.getElementById('filterGender').value;
    const vaccinatedFilter = document.getElementById('filterVaccinated').value;
    const activityFilter = document.getElementById('filterActivity').value;
    
    console.log('Applying filters:', {
        speciesFilter, breedFilter, colorFilter, minAge, maxAge, 
        genderFilter, vaccinatedFilter, activityFilter
    });
    
    filteredPets = allPets.filter(pet => {
        return (!speciesFilter || pet.species === speciesFilter) &&
               (!breedFilter || pet.breed.toLowerCase().includes(breedFilter)) &&
               (!colorFilter || pet.color.toLowerCase().includes(colorFilter)) &&
               (pet.age_months >= minAge) &&
               (pet.age_months <= maxAge) &&
               (!genderFilter || pet.gender === genderFilter) &&
               (!vaccinatedFilter || pet.vaccinated.toString() === vaccinatedFilter) &&
               (!activityFilter || pet.activity_level === activityFilter);
    });
    
    console.log('Pets after filtering:', filteredPets.length);
    displayPets('adopter');
}

function clearFilters() {
    console.log('Clearing all filters');
    
    document.getElementById('filterSpecies').value = '';
    document.getElementById('filterBreed').value = '';
    document.getElementById('filterColor').value = '';
    document.getElementById('filterMinAge').value = '';
    document.getElementById('filterMaxAge').value = '';
    document.getElementById('filterGender').value = '';
    document.getElementById('filterVaccinated').value = '';
    document.getElementById('filterActivity').value = '';
    
    filteredPets = [...allPets];
    displayPets('adopter');
}

// Initialize
console.log('Smart Pet Adoption Shelter initialized');
</script>
</body>
</html>
"""

# HTTP Request Handler
class PetAdoptionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode('utf-8'))
        elif self.path == '/api/pets':
            response = handle_get_pets()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        response = {}
        
        if self.path == '/api/login':
            response = handle_login(data)
        elif self.path == '/api/register':
            response = handle_register(data)
        elif self.path == '/api/pets':
            response = handle_add_pet(data)
        elif self.path == '/api/requests':
            response = handle_get_requests()
        elif self.path == '/api/adopt':
            response = handle_adopt_pet(data)
        elif self.path == '/api/ai/match':
            response = handle_compatibility_check(data)
        else:
            response = {'success': False, 'message': 'Unknown endpoint'}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

# Main execution
if __name__ == '__main__':
    init_database()
    
    PORT = 8000
    server = HTTPServer(('localhost', PORT), PetAdoptionHandler)
    
    print(f"\n🎉 Smart Pet Adoption Shelter Started Successfully!")
    print(f"📍 Server running at: http://localhost:{PORT}")
    print(f"🔑 Admin Login: username='admin', password='admin123'")
    print(f"👤 Test User Login: username='user', password='user123'")
    print(f"\n🚀 Opening browser...")
    
    import webbrowser
    webbrowser.open(f'http://localhost:{PORT}')
    
    try:
        print(f"\n📡 Server ready! Press Ctrl+C to stop the server.")
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n\n🛑 Server stopped by user")
        server.shutdown()