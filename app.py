import streamlit as st
import pymysql
import hashlib
import webbrowser
import streamlit as st  # module to create UI
import time
import groq
import os

st.set_page_config(page_title="Learnify", page_icon="📚")

col1, col2 = st.columns([1, 3])
with col1:
    st.image("logo.jpg", width=100) 
with col2:
    st.title("Learnify")
st.write("Learn at your pace, on your own terms")


# AI setup
os.environ["GROQ_API_KEY"] = "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"  
client = groq.Client()

# Connect to MySQL database
db = pymysql.connect(
    host="localhost",  
    user="root",       
    password="Sye@5444",  
    database="gradingsystem"
)
cursor = db.cursor()

# Hash password
def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

# Chatbot setup
def ai_chatbot(query):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": query,
            }
        ],
        model="llama-3.3-70b-versatile",  
    )
    return chat_completion.choices[0].message.content

# Signup
def sign_up():
    """Sign up a new user"""
    st.title("Sign Up")
    username = st.text_input("Enter your username: ")
    password = st.text_input("Enter your password: ", type="password")
    grade = st.text_input("Enter your current grade: ")
    branch = st.text_input("Enter your branch: ")
    sem = st.text_input("Enter your semester: ")
    subin = st.text_input("Enter the subjects you are interested in: ")

    if st.button("Sign Up"):
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            st.error("Username already exists! Please try a different one.")
        else:
            hashed_password = hash_password(password)
            query = "INSERT INTO users (username, password, grade,branch,sem,subin) VALUES (%s, %s, %s,%s,%s,%s)"
            cursor.execute(query, (username, hashed_password, grade,branch,sem,subin))
            db.commit()
            st.success("Sign-up successful!")
            st.session_state.logged_in = True
            st.session_state.username = username

# Signin
def sign_in():
    """Sign in an existing user"""
    st.title("Sign In")
    username = st.text_input("Enter your username: ")
    password = st.text_input("Enter your password: ", type="password")

    if st.button("Sign In"):
        hashed_password = hash_password(password)
        cursor.execute("SELECT id FROM users WHERE username = %s AND password = %s", (username, hashed_password))
        user = cursor.fetchone()
        if user:
            st.session_state.logged_in = True
            st.session_state.username = username
            view_profile(username)
        else:
            st.error("Invalid username or password!")

def chatbot_ui():
    """Streamlit UI for the chatbot"""
    st.title("AI Student Support Chatbot")
    
    user_input = st.text_input("Tell me about your interests and goals, and I will guide you:")
    
    if user_input:  
        if user_input.lower() == "exit":
            st.write("Goodbye! Feel free to come back anytime.")
        else:
            # Get the chatbot's response
            response = ai_chatbot(user_input)
            st.write(f"**BumbleBee** {response}")

# Comes under mental health and wellness
# Meditation timer
def meditation_timer():
    """Meditation timer for relaxation"""
    st.title("Meditation Timer")
    duration = st.number_input("Set meditation duration (minutes):", min_value=1, max_value=60, value=10)
    if st.button("Start Meditation"):
        st.write(f"Meditation started for {duration} minutes. Relax and focus on your breathing.")
        time.sleep(duration * 60)  
        st.success("Meditation session complete! Great job!")

# Comes under mental health and wellness
# Stress management tips
def stress_management_tips():
    """Display stress management tips"""
    st.title("Stress Management Tips")
    tips = [
        "Take deep breaths for 5 minutes.",
        "Go for a walk in nature.",
        "Write down your thoughts in a journal.",
        "Listen to calming music.",
        "Practice gratitude by listing 3 things you're thankful for."
    ]
    st.write("Here are some tips to manage stress:")
    for tip in tips:
        st.write(f"-- {tip}")

def mood_tracker(username):
    """Track user's mood"""
    st.title("Mood Tracker")
    mood = st.selectbox("How are you feeling today?", ["Happy", "Sad", "Stressed", "Calm", "Energetic", "Tired"])
    notes = st.text_area("Add any notes (optional):")
    if st.button("Log Mood"):
        cursor.execute("INSERT INTO wellness (user_id, mood, notes) VALUES ((SELECT id FROM users WHERE username = %s), %s, %s)",
                       (username, mood, notes))
        db.commit()
        st.success("Mood logged successfully!")
        mood_1=f"i am {mood} today suggest ideas to make a good mood if my mood is not healthy"
        response = ai_chatbot(mood_1)
        st.write(f"**BumbleBee**: {response}")

#Guide users through breathing exercises
def breathing_exercises():
    st.title("Breathing Exercises")
    st.write("1. Breathe in for 4 seconds.")
    st.write("2. Hold your breath for 4 seconds.")
    st.write("3. Breathe out for 6 seconds.")
    st.write("Repeat for 5 cycles.")

#"""Display the profile of the logged-in user"""
def view_profile(username):
    
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    
    if user:
        st.title(f"Welcome {username}")
        st.sidebar.title("Menu")
        choice = ["Intro", "Subjects", "Community", "Mental Health & Wellness","AI ChatBot for Career Guidance"]
        menu_choice = st.sidebar.radio("Contents", choice)
        if menu_choice == "Intro":
            a = str(user[0])
            b = str(user[2])
            c = str(user[5])
            d = int(user[6])
            e = str(user[7])
            grade = f"my name is {a} i am studying btech in {c} semester {d} my grade is {b} and my interested subjects are {e} please make a profile and suggest a study plan"
            response = ai_chatbot(grade)
            st.write(f"**BumbleBee** {response}")
 

        elif menu_choice == "Subjects":
            subject_choice = st.selectbox("Choose a subject", ["Physics", "Chemistry", "Math", "Engineering Graphics", 
                                                              "Basic Electrical and Electronics", "Algorithmic Thinking with Python", 
                                                             "C Programming", "Analog Circuits"])
            resources_choice = st.selectbox("Select a resource", ["Syllabus", "Previous Year Question Papers", "Referral Publications", "Referral Videos"])
            valid_subjects = [
                "Physics", "Chemistry", "Math", "Engineering Graphics", 
                "Basic Electrical and Electronics", "Algorithmic Thinking with Python", 
                "C Programming", "Analog Circuits"
            ]
            if st.button("Get Resources"):
                st.write(f"Here are resources for {subject_choice} ({resources_choice})")
                if resources_choice == "Referral Videos":
                    if subject_choice == "Physics":
                        webbrowser.open("https://www.youtube.com/@franklinslectureskerala")
                    elif subject_choice == "Chemistry":
                        webbrowser.open("https://cutt.ly/LeM2plT5")
                    elif subject_choice == "Math":
                        webbrowser.open("https://www.youtube.com/@RVSMathsAcademy")
                    elif subject_choice == "Engineering Graphics":
                        webbrowser.open("https://www.youtube.com/@GraphicsZONE-zl5jf")
                    elif subject_choice == "Basic Electrical and Electronics":
                        webbrowser.open("https://youtube.com/playlist?list=PLOLbwR_vA1YirWM99kI_MqAPSlPnJLs4F&feature=shared")
                    elif subject_choice == "Algorithmic Thinking with Python":
                        webbrowser.open("https://opentextbc.ca/h5ppsychology/chapter/problem-solving/  https://onlinecourses.nptel.ac.in/noc21_cs32/preview")
                    elif subject_choice == "C Programming":
                        webbrowser.open("https://youtu.be/87SH2Cn0s9A?feature=shared")
                    elif subject_choice == "Analog Circuits":
                        webbrowser.open("https://youtube.com/playlist?list=PLc7Gz02Znph-c2-ssFpRrzYwbzplXfXUT&feature=shared")
                    else:
                        st.write("No video resources available")
                elif resources_choice == "Syllabus":
                    if subject_choice in valid_subjects:
                        webbrowser.open("https://ktu.edu.in/academics/details/hardcoded-btech")
                elif resources_choice == "Previous Year Question Papers":
                    if subject_choice in valid_subjects:
                        webbrowser.open("https://ktu.edu.in/academics/semestermodelpapers/hardcoded-btech")
                elif resources_choice == "Referral Publications":
                    if subject_choice == "Physics":
                        webbrowser.open("https://www.youtube.com/@franklinslectureskerala")
                    elif subject_choice == "Chemistry":
                        webbrowser.open("https://cutt.ly/LeM2plT5")
                    elif subject_choice == "Math":
                        webbrowser.open("https://www.youtube.com/@RVSMathsAcademy")
                    elif subject_choice == "Engineering Graphics":
                        webbrowser.open("https://www.youtube.com/@GraphicsZONE-zl5jf")
                    elif subject_choice == "Basic Electrical and Electronics":
                        webbrowser.open("https://youtube.com/playlist?list=PLOLbwR_vA1YirWM99kI_MqAPSlPnJLs4F&feature=shared")
                    elif subject_choice == "Algorithmic Thinking with Python":
                        webbrowser.open("https://opentextbc.ca/h5ppsychology/chapter/problem-solving/  https://onlinecourses.nptel.ac.in/noc21_cs32/preview")
                    elif subject_choice == "C Programming":
                        webbrowser.open("https://youtu.be/87SH2Cn0s9A?feature=shared")
                    elif subject_choice == "Analog Circuits":
                        webbrowser.open("https://youtube.com/playlist?list=PLc7Gz02Znph-c2-ssFpRrzYwbzplXfXUT&feature=shared")
                    else:
                        st.write("No video resources available")

        elif menu_choice == "Community":
            community_choice = st.selectbox("What would you like to do?", ["Post a Question", "View Questions", "Answer a Question"])

            if community_choice == "Post a Question":
                question_text = st.text_area("Enter your question:")
                if st.button("Post Question"):
                    cursor.execute("INSERT INTO questions (user_id, question_text) VALUES ((SELECT id FROM users WHERE username = %s), %s)", 
                                   (username, question_text))
                    db.commit()
                    st.success("Your question has been posted!")

            elif community_choice == "View Questions":
                cursor.execute("SELECT q.id, q.question_text, u.username FROM questions q JOIN users u ON q.user_id = u.id")
                questions = cursor.fetchall()
                if questions:
                    for question in questions:
                        st.write(f"Question by {question[2]}: {question[1]}")
                        view_answers(question[0])

            elif community_choice == "Answer a Question":
                question_id = st.number_input("Enter the question ID you want to answer:", min_value=1)
                answer_text = st.text_area("Enter your answer:")
                if st.button("Post Answer"):
                    cursor.execute("INSERT INTO answers (question_id, user_id, answer_text) VALUES (%s, (SELECT id FROM users WHERE username = %s), %s)", 
                                   (question_id, username, answer_text))
                    db.commit()
                    st.success("Your answer has been posted!")

        elif menu_choice == "Mental Health & Wellness":
            wellness_choice = st.selectbox("Choose an option", ["Meditation Timer", "Stress Management Tips", "Mood Tracker", "Breathing Exercises"])
            if wellness_choice == "Meditation Timer":
                meditation_timer()
            elif wellness_choice == "Stress Management Tips":
                stress_management_tips()
            elif wellness_choice == "Mood Tracker":
                mood_tracker(username)
            elif wellness_choice == "Breathing Exercises":
                breathing_exercises()
        elif menu_choice == "AI ChatBot for Career Guidance":
            chatbot_ui()

def view_answers(question_id):
    """View answers for a specific question"""
    cursor.execute("SELECT a.answer_text, u.username FROM answers a JOIN users u ON a.user_id = u.id WHERE a.question_id = %s", 
                   (question_id,))
    answers = cursor.fetchall()
    for answer, uname in answers:
        st.write(f"Answered by {uname}: {answer}")

# Main Menu
def main():
    # Check if the user is already logged in
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    #login info 
    if st.session_state.logged_in:
        view_profile(st.session_state.username)
    else:
        # Only show sign up and sign in if the user is not logged in
        choice = st.selectbox("Choose an action", ["Sign Up", "Sign In"])

        if choice == "Sign Up":
            sign_up()
        elif choice == "Sign In":
            sign_in()

if __name__ == "__main__":
    main()

# Close the database connection
cursor.close()
db.close()

