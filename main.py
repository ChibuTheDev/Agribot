import streamlit as st
import sqlite3
from passlib.hash import sha256_crypt
from chat import get_chat_response
from weather_utils import get_5day_forecast

# Database setup (SQLite)
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Create users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        location TEXT
    )
''')

# makeing a table for messages
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
''')

conn.commit()
conn.close()

def is_weather_query(prompt):
    weather_keywords = ["weather", "forecast", "temperature", "rain", "sun", "cloud", "humidity"]
    return any(keyword in prompt.lower() for keyword in weather_keywords)

def save_message(user_id, role, message):
    """Save a chat message to the database."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (user_id, role, message) VALUES (?, ?, ?)", (user_id, role, message))
    conn.commit()
    conn.close()

def load_past_messages(user_id):
    """Retrieve past chat messages from the database."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role, message FROM messages WHERE user_id = ? ORDER BY timestamp", (user_id,))
    messages = cursor.fetchall()
    conn.close()
    
    return [{"role": row[0], "parts": row[1]} for row in messages]

# --- Streamlit App ---
st.title("🌱Agri-Bot")
st.write("Your personal farming assistant🚜")

# --- Authentication ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if st.session_state.user_id is None:  # User not logged in
    authentication_tabs = st.tabs(["Sign Up", "Log In"])

    with authentication_tabs[0]:  # Sign Up
        st.subheader("Sign Up")
        new_username = st.text_input("Username", key="signup_username")
        new_password = st.text_input("Password", type="password", key="signup_password")
        new_location = st.text_input("Location (state)", key="signup_location")

        if st.button("Sign Up"):
            if not new_username or not new_password or not new_location:
                st.error("All fields are required.")
            else:
                try:
                    hashed_password = sha256_crypt.hash(new_password)
                    conn = sqlite3.connect('users.db')
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, password, location) VALUES (?, ?, ?)", (new_username, hashed_password, new_location))
                    conn.commit()
                    conn.close()
                    st.success("Sign up successful! Please log in.")
                except sqlite3.IntegrityError:
                    st.error("Username already exists. Please choose a different username.")

    with authentication_tabs[1]:  # Log In
        st.subheader("Log In")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Log In"):
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, password, location FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            conn.close()

            if user and sha256_crypt.verify(password, user[1]):
                st.session_state.user_id = user[0]
                st.session_state.user_location = user[2]
                st.session_state.username = username
                st.session_state.messages = load_past_messages(user[0])  # Loading past messages
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

else:  # User is logged in
    st.sidebar.write(f"Welcome, {st.session_state.username}!")
    if st.sidebar.button("Log Out"):
        st.session_state.user_id = None
        st.session_state.user_location = None
        st.session_state.username = None
        st.session_state.logout = True

    if "logout" in st.session_state and st.session_state.logout:
        del st.session_state.logout
        st.session_state.messages = []  # Clear messages on logout
        st.rerun()

    # --- Chat and Weather ---
    with st.expander("About Agribot"):
        st.write('''
            Hi there! My name is **Agribot**, and I'm here to help you with all things farming! 🌱

            Here's what I can do for you:
            - **Crop Recommendations and Management**: Get advice on the best crops to grow and how to manage them.
            - **Farm Budget Planning**: Help you calculate expenses and plan your farm budget.
            - **Pest and Disease Control**: Tips to protect your crops from pests and diseases.
            - **Soil Health Tips**: Improve your soil for better yields.
            - **Livestock Management**: Guidance on raising healthy livestock.
            - **Sustainable Farming Practices**: Learn eco-friendly farming methods.

            Feel free to ask me anything about agriculture, and I'll do my best to assist you. 😊

            I can also provide a 5-day weather forecast if you ask nicely! 😉
        ''')

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # showing past messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["parts"])

    # Chat Input
    if prompt := st.chat_input("Ask me anything about Agriculture!"):
        st.session_state.messages.append({"role": "user", "parts": prompt})
        save_message(st.session_state.user_id, "user", prompt)  # Saves user message

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if is_weather_query(prompt):
                try:
                    location = st.session_state.user_location
                    if not location:
                        response = "Location not set. Please update your profile."
                    else:
                        response = get_5day_forecast(location)
                except Exception as e:
                    response = f"An error occurred: {e}"
            else:
                try:
                    response, _ = get_chat_response(prompt, st.session_state.messages)
                except Exception as e:
                    response = f"An error occurred: {e}"

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "parts": response})
            save_message(st.session_state.user_id, "assistant", response)  # Save bot response
