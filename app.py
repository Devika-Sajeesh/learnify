import streamlit as st
import pymysql
import hashlib
import webbrowser
import time
import groq
import os
from datetime import datetime

# --- Page Configuration (MUST BE FIRST STREAMLIT COMMAND) ---
st.set_page_config(
    page_title="Learnify", 
    page_icon="📚",
    layout="wide"
)


# --- Initialize Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False

def display_header():
    """Display the application header with logo and title"""
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("images/logo.jpg", width=100) 
    with col2:
        st.title("Learnify")
    st.write("Learn at your pace, on your own terms")

# --- Database Initialization ---
def initialize_database():
    """Initialize tables if they don't exist"""
    try:
        connection = pymysql.connect(
            host=st.secrets["DB_HOST"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"],
            autocommit=True
        )

        with connection.cursor() as cursor:
            # Do NOT create a database — Railway gives one
            tables = [
                """CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(64) NOT NULL,
                    gpa DECIMAL(3,2),
                    branch VARCHAR(50),
                    sem VARCHAR(20),
                    subin TEXT,
                    subnin TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )""",
                """CREATE TABLE IF NOT EXISTS questions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    question_text TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )""",
                """CREATE TABLE IF NOT EXISTS answers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question_id INT NOT NULL,
                    user_id INT NOT NULL,
                    answer_text TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (question_id) REFERENCES questions(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )""",
                """CREATE TABLE IF NOT EXISTS wellness (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    mood VARCHAR(20) NOT NULL,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )"""
            ]

            for table in tables:
                cursor.execute(table)

        st.session_state.db_initialized = True
        return True

    except Exception as e:
        st.error(f"Database initialization failed: {str(e)}")
        return False
    finally:
        if 'connection' in locals() and connection:
            connection.close()


# --- Database Connection ---
def get_db_connection():
    """Create and return a database connection with retry logic"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            connection = pymysql.connect(
                host=st.secrets["DB_HOST"],
                port=int(st.secrets["DB_PORT"]),
                user=st.secrets["DB_USER"],
                password=st.secrets["DB_PASSWORD"],
                database=st.secrets["DB_NAME"],
                ssl={"ssl": {"ca": "/etc/ssl/cert.pem"}},
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10  # Increased from 5
            )
            # Test the connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return connection
        except pymysql.Error as e:
            st.warning(f"Connection attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                st.error(f"""Failed to connect after {max_retries} attempts. Please check:
                    - Database server status
                    - Connection credentials
                    - Network connectivity""")
                return None
            time.sleep(retry_delay)
def check_railway_connection():
    """Special checks for Railway.app deployments"""
    if "rlwy.net" in st.secrets["DB_HOST"]:
        st.info("Checking Railway.app database connection...")
        
        # Verify port is correctly set
        if not st.secrets["DB_PORT"].isdigit():
            st.error("DB_PORT must be a number")
            return False
            
        # Verify all required credentials exist
        required_keys = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_PORT"]
        for key in required_keys:
            if key not in st.secrets or not st.secrets[key]:
                st.error(f"Missing database credential: {key}")
                return False
                
        return True
    return True

# --- Security Functions ---
def hash_password(password):
    """Hash password using SHA-256 with salt"""
    salt = st.secrets["PASSWORD_SALT"]
    return hashlib.sha256((password + salt).encode()).hexdigest()

# --- Authentication Functions ---
def sign_up():
    """Handle new user registration with proper GPA validation"""
    st.title("Sign Up")
    with st.form("signup_form"):
        username = st.text_input("Username:")
        password = st.text_input("Password:", type="password")
        confirm_password = st.text_input("Confirm Password:", type="password")
        gpa = st.number_input("Current SGPA:", 
                             min_value=0.0, 
                             max_value=10.0, 
                             step=0.01,
                             format="%.2f")
        branch = st.text_input("Branch:")
        sem = st.text_input("Semester:")
        subin = st.text_input("Subjects you are good at:")
        subnin = st.text_input("Subjects you struggle at:")

        
        if st.form_submit_button("Sign Up"):
            if password != confirm_password:
                st.error("Passwords do not match!")
                return
                
            db = get_db_connection()
            if db:
                try:
                    with db.cursor() as cursor:
                        # Check if username exists
                        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                        if cursor.fetchone():
                            st.error("Username already exists!")
                            return
                            
                        # Create new user
                        hashed_password = hash_password(password)
                        query = """
                            INSERT INTO users 
                            (username, password, gpa, branch, sem, subin,subnin) 
                            VALUES (%s, %s, %s, %s, %s, %s,%s)
                        """
                        cursor.execute(query, (
                            username, hashed_password, float(gpa), 
                            branch, sem, subin,subnin
                        ))
                        db.commit()
                        st.success("Account created successfully!")
                        st.session_state.logged_in = True
                        st.session_state.username = username
                except pymysql.Error as e:
                    st.error(f"Registration failed: {e}")
                finally:
                    db.close()

def sign_in():
    """Handle user login"""
    st.title("Sign In")
    with st.form("login_form"):
        username = st.text_input("Username:")
        password = st.text_input("Password:", type="password")
        
        if st.form_submit_button("Sign In"):
            db = get_db_connection()
            if db:
                try:
                    with db.cursor() as cursor:
                        hashed_password = hash_password(password)
                        cursor.execute(
                            "SELECT id FROM users WHERE username = %s AND password = %s", 
                            (username, hashed_password)
                        )
                        if cursor.fetchone():
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.success("Login successful!")
                        else:
                            st.error("Invalid credentials!")
                except pymysql.Error as e:
                    st.error(f"Login failed: {e}")
                finally:
                    db.close()

def logout():
    """Handle user logout"""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.success("Logged out successfully!")

# --- AI Chatbot Functions ---
def get_ai_response(query):
    """Get response from Groq AI"""
    try:
        client = groq.Client(api_key=st.secrets["GROQ_API_KEY"])
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": query}],
            model="llama3-70b-8192",
            temperature=0.7,
            max_tokens=1024
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"AI service error: {e}")
        return "I'm having trouble connecting to the AI service. Please try again later."

def chatbot_ui():
    """Interactive AI chatbot interface"""
    st.title("AI Student Support Chatbot")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Accept user input
    if prompt := st.chat_input("How can I help you today?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get and display AI response
        with st.spinner("Thinking..."):
            response = get_ai_response(prompt)
            
        with st.chat_message("assistant"):
            st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

# --- Wellness Features ---
def meditation_timer():
    """Guided meditation timer"""
    st.title("Meditation Timer")
    
    col1, col2 = st.columns(2)
    with col1:
        duration = st.slider("Duration (minutes)", 1, 30, 10)
        if st.button("Start Meditation"):
            st.session_state.meditation_start = time.time()
            st.session_state.meditation_duration = duration * 60
            st.success(f"Meditation started for {duration} minutes")
    
    if "meditation_start" in st.session_state:
        elapsed = time.time() - st.session_state.meditation_start
        remaining = max(0, st.session_state.meditation_duration - elapsed)
        
        if remaining > 0:
            minutes, seconds = divmod(int(remaining), 60)
            st.write(f"Time remaining: {minutes:02d}:{seconds:02d}")
            st.progress(1 - (remaining / st.session_state.meditation_duration))
        else:
            st.balloons()
            st.success("Meditation session complete!")
            del st.session_state.meditation_start
            del st.session_state.meditation_duration

def stress_management_tips():
    """Display personalized stress management tips"""
    st.title("Stress Management Tips")
    tips = get_ai_response("Provide 5 concise stress management tips for students")
    st.markdown(tips)

def mood_tracker(username):
    """Track and analyze user mood"""
    st.title("Mood Tracker")
    
    with st.form("mood_form"):
        mood = st.selectbox("How are you feeling today?", 
                           ["😊 Happy", "😢 Sad", "😫 Stressed", 
                            "😌 Calm", "⚡ Energetic", "😴 Tired"])
        notes = st.text_area("Notes (optional):")
        
        if st.form_submit_button("Log Mood"):
            db = get_db_connection()
            if db:
                try:
                    with db.cursor() as cursor:
                        cursor.execute(
                            """INSERT INTO wellness 
                            (user_id, mood, notes, created_at) 
                            VALUES (
                                (SELECT id FROM users WHERE username = %s), 
                                %s, %s, %s
                            )""",
                            (username, mood.split()[1], notes, datetime.now())
                        )
                        db.commit()
                        st.success("Mood logged successfully!")
                        
                        # Get mood improvement suggestions
                        response = get_ai_response(
                            f"I'm feeling {mood} today. Suggest 3 activities to improve my mood"
                        )
                        st.markdown("**Suggestions for you:**")
                        st.markdown(response)
                except pymysql.Error as e:
                    st.error(f"Failed to log mood: {e}")
                finally:
                    db.close()

def breathing_exercises():
    """Guide through breathing exercises"""
    st.title("Breathing Exercises")
    
    st.write("""
    Follow this 4-4-6 breathing pattern:
    1. Inhale deeply for 4 seconds
    2. Hold your breath for 4 seconds
    3. Exhale slowly for 6 seconds
    """)
    
    if st.button("Start Breathing Exercise"):
        for i in range(3):  # 3 cycles
            with st.empty():
                st.write("🌬️ Inhale...")
                time.sleep(4)
                st.write("⏳ Hold...")
                time.sleep(4)
                st.write("💨 Exhale...")
                time.sleep(6)
        st.success("Exercise complete! Feel more relaxed?")

# --- Educational Resources ---
def get_subject_resources():
    """Return structured subject resources"""
    return {
        "Physics": {
            "Syllabus": "https://ktu.edu.in/academics/details/hardcoded-btech",
            "Videos": "https://www.youtube.com/@franklinslectureskerala",
            "Books": "University Physics by Young and Freedman"
        },
        # Add other subjects similarly...
    }

def display_subject_resources(subject, resource_type):
    """Display resources for selected subject"""
    resources = get_subject_resources()
    
    if subject in resources and resource_type in resources[subject]:
        if resource_type == "Videos":
            st.video(resources[subject][resource_type])
        else:
            st.markdown(f"[Open {resource_type}]({resources[subject][resource_type]})")
    else:
        st.warning("Resources not available for this selection")

# --- Community Features ---
def community_forum(username):
    """Interactive community Q&A forum"""
    st.title("Community Forum")
    
    tab1, tab2, tab3 = st.tabs(["Ask Question", "Browse Questions", "My Questions"])
    
    db = get_db_connection()
    if not db:
        return
        
    try:
        with db.cursor() as cursor:
            # Post new question
            with tab1:
                with st.form("question_form"):
                    question = st.text_area("Your question:")
                    if st.form_submit_button("Post Question"):
                        if question.strip():
                            cursor.execute(
                                """INSERT INTO questions 
                                (user_id, question_text, created_at) 
                                VALUES (
                                    (SELECT id FROM users WHERE username = %s), 
                                    %s, %s
                                )""",
                                (username, question, datetime.now())
                            )
                            db.commit()
                            st.success("Question posted!")
                        else:
                            st.warning("Please enter a question")
            
            # Browse all questions
            with tab2:
                cursor.execute("""
                    SELECT q.id, q.question_text, u.username, q.created_at 
                    FROM questions q JOIN users u ON q.user_id = u.id 
                    ORDER BY q.created_at DESC
                """)
                questions = cursor.fetchall()
                
                if questions:
                    for q in questions:
                        with st.expander(f"Q: {q['question_text']} (by {q['username']})"):
                            st.caption(f"Posted on {q['created_at'].strftime('%Y-%m-%d %H:%M')}")
                            
                            # Display answers
                            cursor.execute("""
                                SELECT a.answer_text, u.username, a.created_at 
                                FROM answers a JOIN users u ON a.user_id = u.id 
                                WHERE a.question_id = %s 
                                ORDER BY a.created_at
                            """, (q['id'],))
                            answers = cursor.fetchall()
                            
                            if answers:
                                st.write("**Answers:**")
                                for ans in answers:
                                    st.markdown(f"**{ans['username']}:** {ans['answer_text']}")
                                    st.caption(f"Answered on {ans['created_at'].strftime('%Y-%m-%d %H:%M')}")
                            else:
                                st.info("No answers yet")
                            
                            # Answer form
                            with st.form(f"answer_form_{q['id']}"):
                                answer = st.text_area("Your answer:")
                                if st.form_submit_button("Post Answer"):
                                    if answer.strip():
                                        cursor.execute(
                                            """INSERT INTO answers 
                                            (question_id, user_id, answer_text, created_at) 
                                            VALUES (%s, 
                                                (SELECT id FROM users WHERE username = %s), 
                                                %s, %s
                                            )""",
                                            (q['id'], username, answer, datetime.now())
                                        )
                                        db.commit()
                                        st.rerun()
                                    else:
                                        st.warning("Please enter an answer")
                else:
                    st.info("No questions yet")
            
            # User's own questions
            with tab3:
                cursor.execute("""
                    SELECT q.id, q.question_text, q.created_at 
                    FROM questions q JOIN users u ON q.user_id = u.id 
                    WHERE u.username = %s 
                    ORDER BY q.created_at DESC
                """, (username,))
                user_questions = cursor.fetchall()
                
                if user_questions:
                    for q in user_questions:
                        with st.expander(f"Q: {q['question_text']}"):
                            st.caption(f"Posted on {q['created_at'].strftime('%Y-%m-%d %H:%M')}")
                            
                            cursor.execute("""
                                SELECT a.answer_text, u.username, a.created_at 
                                FROM answers a JOIN users u ON a.user_id = u.id 
                                WHERE a.question_id = %s 
                                ORDER BY a.created_at
                            """, (q['id'],))
                            answers = cursor.fetchall()
                            
                            if answers:
                                st.write("**Answers:**")
                                for ans in answers:
                                    st.markdown(f"**{ans['username']}:** {ans['answer_text']}")
                                    st.caption(f"Answered on {ans['created_at'].strftime('%Y-%m-%d %H:%M')}")
                            else:
                                st.info("No answers yet")
                else:
                    st.info("You haven't asked any questions yet")
    except pymysql.Error as e:
        st.error(f"Database error: {e}")
    finally:
        db.close()

# --- Profile Management ---
def view_profile(username):
    """Display and manage user profile"""
    st.title(f"Welcome {username}")
    
    # Add logout button to sidebar
    with st.sidebar:
        st.title("Menu")
        if st.button("Logout"):
            logout()
            st.rerun()
        
        menu_choice = st.radio("Navigation", [
            "Dashboard", 
            "Subjects", 
            "Community", 
            "Wellness Center",
            "AI Tutor"
        ])
    
    db = get_db_connection()
    if not db:
        return
        
    try:
        with db.cursor() as cursor:
            # Get user profile
            cursor.execute("""
                SELECT username, gpa, branch, sem, subin, subnin
                FROM users WHERE username = %s
            """, (username,))
            profile = cursor.fetchone()
            
            if menu_choice == "Dashboard":
                st.header("Your Learning Dashboard")
                
                if profile:
                    # Display personalized study plan
                    prompt = f"""
                    Create a personalized study plan for:
                    - Name: {profile['username']}
                    - SGPA: {profile['gpa']}
                    - Stream: {profile['branch']}
                    - Semester: {profile['sem']}
                    - Subjects I am good at: {profile['subin']}
                    - Subjects I struggle with: {profile['subnin']}
                    """
                    response = get_ai_response(prompt)
                    st.markdown(response)
                
                # Display recent activity
                st.subheader("Your Recent Activity")
                cursor.execute("""
                    SELECT 'question' as type, question_text as text, created_at 
                    FROM questions WHERE user_id = (SELECT id FROM users WHERE username = %s)
                    UNION
                    SELECT 'answer' as type, answer_text as text, created_at 
                    FROM answers WHERE user_id = (SELECT id FROM users WHERE username = %s)
                    ORDER BY created_at DESC LIMIT 5
                """, (username, username))
                activities = cursor.fetchall()
                
                if activities:
                    for act in activities:
                        st.caption(f"{act['created_at'].strftime('%Y-%m-%d')} - Posted {act['type']}")
                        st.write(act['text'])
                else:
                    st.info("No recent activity yet")
            
            elif menu_choice == "Subjects":
                st.header("Subject Resources")
                
                col1, col2 = st.columns(2)
                with col1:
                    subject = st.selectbox("Select Subject", list(get_subject_resources().keys()))
                with col2:
                    resource_type = st.selectbox("Resource Type", ["Syllabus", "Videos", "Books"])
                
                if st.button("Get Resources"):
                    display_subject_resources(subject, resource_type)
            
            elif menu_choice == "Community":
                community_forum(username)
            
            elif menu_choice == "Wellness Center":
                st.header("Mental Health & Wellness")
                
                wellness_option = st.selectbox("Choose a wellness activity", [
                    "Meditation Timer",
                    "Stress Management",
                    "Mood Tracker",
                    "Breathing Exercises"
                ])
                
                if wellness_option == "Meditation Timer":
                    meditation_timer()
                elif wellness_option == "Stress Management":
                    stress_management_tips()
                elif wellness_option == "Mood Tracker":
                    mood_tracker(username)
                elif wellness_option == "Breathing Exercises":
                    breathing_exercises()
            
            elif menu_choice == "AI Tutor":
                chatbot_ui()
                
    except pymysql.Error as e:
        st.error(f"Database error: {e}")
    finally:
        db.close()

# --- Main Application ---
def main():
    """Main application controller"""
    display_header()
    
    # First check Railway-specific requirements
    if not check_railway_connection():
        st.stop()  # Don't proceed if checks fail
    
    # Then proceed with initialization
    if not st.session_state.db_initialized:
        with st.spinner("Initializing database. Please wait..."):
            if initialize_database():
                st.session_state.db_initialized = True
                st.success("Database ready!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("""
                Critical: Failed to initialize database. 
                Possible causes:
                1. Database server is not running
                2. Incorrect credentials in secrets
                3. Network firewall blocking connection
                4. Railway service needs to be restarted
                """)
                st.stop()
    
    # Main application logic
    if st.session_state.logged_in:
        view_profile(st.session_state.username)
    else:
        auth_option = st.radio("Choose an option", ["Sign In", "Sign Up"])
        if auth_option == "Sign In":
            sign_in()
        else:
            sign_up()

if __name__ == "__main__":
    main()
