from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import secrets
import string
from config import config
from models import db, User, Upload, Tag, Species, SearchQuery, PasswordResetToken


def init_default_data():
    """Initialize default species data"""
    default_species = [
        {
            'common_name': 'Sulphur-crested Cockatoo',
            'scientific_name': 'Cacatua galerita',
            'family': 'Cacatuidae',
            'conservation_status': 'Least Concern'
        },
        {
            'common_name': 'Laughing Kookaburra',
            'scientific_name': 'Dacelo novaeguineae',
            'family': 'Alcedinidae',
            'conservation_status': 'Least Concern'
        },
        {
            'common_name': 'Australian Magpie',
            'scientific_name': 'Gymnorhina tibicen',
            'family': 'Artamidae',
            'conservation_status': 'Least Concern'
        },
        {
            'common_name': 'Rainbow Lorikeet',
            'scientific_name': 'Trichoglossus moluccanus',
            'family': 'Psittaculidae',
            'conservation_status': 'Least Concern'
        },
        {
            'common_name': 'Galah',
            'scientific_name': 'Eolophus roseicapilla',
            'family': 'Cacatuidae',
            'conservation_status': 'Least Concern'
        }
    ]

    for species_data in default_species:
        if not Species.query.filter_by(scientific_name=species_data['scientific_name']).first():
            species = Species(**species_data)
            db.session.add(species)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing default data: {e}")


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Create upload folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Create database tables and initialize data
    with app.app_context():
        db.create_all()
        init_default_data()

    return app


app = create_app('development')


def generate_reset_token():
    """Generate random password reset token"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def validate_password(password):
    """Validate password requirements"""
    import re
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain an uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain a lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain a number"
    return True, "Password meets requirements"


# Helper function to simulate AI species detection
def simulate_species_detection(file_type, filepath):
    """Simulate AI bird species detection"""
    import random

    common_birds = [
        'Cockatoo', 'Kookaburra', 'Magpie', 'Rainbow Lorikeet',
        'Galah', 'Sulphur-crested Cockatoo', 'Australian Raven',
        'Willie Wagtail', 'Fairy Wren', 'Butcherbird'
    ]

    # Simulate detection with random species
    num_species = random.randint(1, 3)
    detected = random.sample(common_birds, num_species)

    confidence = {}
    for species in detected:
        confidence[species] = round(random.uniform(0.7, 0.99), 2)

    return {
        'species': detected,
        'confidence': confidence
    }


@app.route('/')
def index():
    if 'user_id' in session and 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password1 = data.get('password1')
        password2 = data.get('password2')
        email = data.get('email', '')

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username already exists'})

        # Check if passwords match
        if password1 != password2:
            return jsonify({'success': False, 'message': 'Passwords do not match'})

        # Validate password strength
        is_valid, message = validate_password(password1)
        if not is_valid:
            return jsonify({'success': False, 'message': message})

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password1)

        try:
            db.session.add(user)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Registration successful'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Registration failed. Please try again.'})

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'})

    return render_template('login.html')
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    # 检查是单个文件还是多个文件
    if 'file' in request.files:
        # 单个文件上传（兼容原始代码）
        files = [request.files['file']]
    elif 'files' in request.files:
        # 多个文件上传
        files = request.files.getlist('files')
    else:
        return jsonify({'success': False, 'message': 'No files uploaded'})

    location = request.form.get('location', '')
    observation_date = request.form.get('date')
    notes = request.form.get('notes', '')

    uploaded_files = []

    for file in files:
        if file and file.filename and allowed_file(file.filename):
            # Generate secure filename
            original_filename = file.filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{secure_filename(original_filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save file
            file.save(filepath)

            # Determine file type
            file_ext = filename.rsplit('.', 1)[1].lower()
            if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
                file_type = 'image'
            elif file_ext in ['mp4', 'avi', 'mov']:
                file_type = 'video'
            elif file_ext in ['mp3', 'wav', 'm4a']:
                file_type = 'audio'
            else:
                file_type = 'other'

            # Create upload record
            upload = Upload(
                user_id=session['user_id'],
                filename=filename,
                original_filename=original_filename,
                file_path=filepath,
                file_type=file_type,
                file_size=os.path.getsize(filepath),
                location=location,
                observation_date=datetime.strptime(observation_date, '%Y-%m-%d').date() if observation_date else None,
                notes=notes,
                species_detected=[],  # This would be populated by AI detection
                confidence_scores={}
            )

            # Here you would call your AI model to detect species
            # For now, we'll simulate it
            detected_species = simulate_species_detection(file_type, filepath)
            upload.species_detected = detected_species['species']
            upload.confidence_scores = detected_species['confidence']

            # Auto-tag based on detected species
            for species_name in detected_species['species']:
                tag = Tag.query.filter_by(name=species_name, category='species').first()
                if not tag:
                    tag = Tag(name=species_name, category='species')
                    db.session.add(tag)
                upload.tags.append(tag)

            db.session.add(upload)
            uploaded_files.append(upload)

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
            'species': list(set([species for upload in uploaded_files for species in upload.species_detected])),
            'files': [upload.to_dict() for upload in uploaded_files]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Upload failed. Please try again.'})


@app.route('/search', methods=['POST'])
def search_files():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    data = request.get_json()
    species = data.get('species', '')
    media_type = data.get('mediaType', '')
    date_range = data.get('dateRange', '')

    # Build query
    query = Upload.query.filter_by(user_id=session['user_id'])

    # Filter by species
    if species:
        query = query.filter(Upload.species_detected.contains([species]))

    # Filter by media type
    if media_type:
        query = query.filter_by(file_type=media_type)

    # Filter by date range
    if date_range:
        today = datetime.now().date()
        if date_range == 'today':
            query = query.filter(db.func.date(Upload.uploaded_at) == today)
        elif date_range == 'week':
            week_ago = today - timedelta(days=7)
            query = query.filter(Upload.uploaded_at >= week_ago)
        elif date_range == 'month':
            month_ago = today - timedelta(days=30)
            query = query.filter(Upload.uploaded_at >= month_ago)
        elif date_range == 'year':
            year_ago = today - timedelta(days=365)
            query = query.filter(Upload.uploaded_at >= year_ago)

    # Execute query
    results = query.order_by(Upload.uploaded_at.desc()).all()

    # Log search query
    search_log = SearchQuery(
        user_id=session['user_id'],
        query_params={
            'species': species,
            'media_type': media_type,
            'date_range': date_range
        },
        result_count=len(results)
    )
    db.session.add(search_log)
    db.session.commit()

    # Format results
    files_data = []
    for upload in results:
        file_data = {
            'id': upload.id,
            'name': upload.original_filename,
            'type': upload.file_type,
            'species': ', '.join(upload.species_detected) if upload.species_detected else 'Unknown',
            'date': upload.observation_date.strftime('%Y-%m-%d') if upload.observation_date else upload.uploaded_at.strftime('%Y-%m-%d'),
            'location': upload.location or 'Unknown',
            'thumbnail': f'/uploads/{upload.filename}' if upload.file_type == 'image' else None
        }
        files_data.append(file_data)

    return jsonify({
        'success': True,
        'count': len(results),
        'files': files_data
    })


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get user statistics
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    total_uploads = Upload.query.filter_by(user_id=user.id).count()

    # Get unique species count
    all_species = db.session.query(Upload.species_detected) \
        .filter_by(user_id=user.id) \
        .filter(Upload.species_detected != None).all()
    unique_species = set()
    for species_list in all_species:
        if species_list[0]:
            unique_species.update(species_list[0])

    # This month's uploads
    first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_uploads = Upload.query.filter(
        Upload.user_id == user.id,
        Upload.uploaded_at >= first_day_of_month
    ).count()

    # Calculate storage used
    total_size = db.session.query(db.func.sum(Upload.file_size)) \
                     .filter_by(user_id=user.id).scalar() or 0
    storage_gb = round(total_size / (1024 * 1024 * 1024), 2)

    return render_template('dashboard.html',
                           username=session.get('username', user.username),
                           stats={
                               'total_uploads': total_uploads,
                               'species_count': len(unique_species),
                               'monthly_uploads': monthly_uploads,
                               'storage_gb': storage_gb
                           })

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'success': False, 'message': 'Username does not exist'})

        # Generate reset token
        token = generate_reset_token()
        reset_token = PasswordResetToken(
            token=token,
            user_id=user.id,
            expires_at=datetime.now() + timedelta(hours=1)
        )

        db.session.add(reset_token)
        db.session.commit()

        reset_link = f"/reset-password?token={token}"

        return jsonify({
            'success': True,
            'message': 'Reset link has been generated',
            'reset_link': reset_link,
            'note': 'In production, this link would be sent to your email'
        })

    return render_template('forgot_password.html')


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        token = request.args.get('token')
        if not token:
            return render_template('reset_password.html', error='Invalid reset link')

        reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
        if not reset_token:
            return render_template('reset_password.html', error='Invalid reset link')

        if datetime.now() > reset_token.expires_at:
            return render_template('reset_password.html', error='Reset link has expired')

        return render_template('reset_password.html', token=token)

    elif request.method == 'POST':
        data = request.get_json()
        token = data.get('token')
        password1 = data.get('password1')
        password2 = data.get('password2')

        reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
        if not reset_token:
            return jsonify({'success': False, 'message': 'Invalid reset link'})

        if datetime.now() > reset_token.expires_at:
            return jsonify({'success': False, 'message': 'Reset link has expired'})

        if password1 != password2:
            return jsonify({'success': False, 'message': 'Passwords do not match'})

        is_valid, message = validate_password(password1)
        if not is_valid:
            return jsonify({'success': False, 'message': message})

        # Update password
        user = User.query.get(reset_token.user_id)
        user.set_password(password1)
        reset_token.used = True

        db.session.commit()

        return jsonify({'success': True, 'message': 'Password reset successful'})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# API endpoints for dashboard statistics
@app.route('/api/stats')
def get_stats():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})

    user_id = session['user_id']

    # Get various statistics
    stats = {
        'total_uploads': Upload.query.filter_by(user_id=user_id).count(),
        'recent_uploads': []
    }

    # Get recent uploads
    recent = Upload.query.filter_by(user_id=user_id) \
        .order_by(Upload.uploaded_at.desc()) \
        .limit(5).all()

    for upload in recent:
        stats['recent_uploads'].append({
            'filename': upload.original_filename,
            'type': upload.file_type,
            'species': upload.species_detected,
            'uploaded_at': upload.uploaded_at.isoformat()
        })

    return jsonify(stats)


# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)