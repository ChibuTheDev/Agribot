import streamlit as st
from dotenv import load_dotenv
from chat import get_chat_response
from weather_utils import get_5day_forecast


load_dotenv()

# Function to generate responses
def response_generator(prompt, history):
    response, updated_history = get_chat_response(prompt, history)
    return response, updated_history

# Function to check if the query is weather-related
def is_weather_query(prompt):
    """
    Check if the user is asking for weather information.
    """
    weather_keywords = ["weather", "forecast", "temperature", "rain", "sun", "cloud", "humidity"]
    return any(keyword in prompt.lower() for keyword in weather_keywords)

# Function to extract location from the query
def extract_location(prompt):
    """
    Extract the location from the user's query.
    """
 
    location_indicators = ["in", "for", "at", "near", "around"]
    
    # Split the prompt into words
    words = prompt.lower().split()
    
    # Find the location indicator and extract the location
    for i, word in enumerate(words):
        if word in location_indicators and i + 1 < len(words):
            return " ".join(words[i + 1:]).strip()
    
    # If no indicator is found, assume the last word is the location
    return words[-1].strip() if words else None


st.title("🌱Agri-Bot")
st.write("Your personal farming assistant🚜")

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

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"])

# Handle user input
if prompt := st.chat_input("Ask me anything about Agriculture!"):
    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if is_weather_query(prompt):  # Check if it's a weather-related query
            try:
                # Extract location from the prompt
                location = extract_location(prompt)
                if not location:
                    st.markdown("Please specify a location.")
                    st.session_state.messages.append({"role": "assistant", "parts": "Please specify a location."})
                else:
                    forecasts = get_5day_forecast(location)
                    if isinstance(forecasts, str):  # Error message
                        st.markdown(forecasts)
                        st.session_state.messages.append({"role": "assistant", "parts": forecasts})
                    else:
                        st.markdown(forecasts)
                        st.session_state.messages.append({"role": "assistant", "parts": forecasts})
                        if "breakdown" in prompt.lower():  # Allow Gemini to explain the weather data
                            gemini_prompt = f"Here is the 5-day weather forecast for {location}:\n\n{forecasts}\n\nCan you provide a detailed explanation of this weather data, including what each column represents and any notable trends or observations?"
                            gemini_response, _ = get_chat_response(gemini_prompt, st.session_state.messages)
                            st.markdown(gemini_response)
                            st.session_state.messages.append({"role": "assistant", "parts": gemini_response})
            except IndexError:
                st.markdown("Please specify a location.")
                st.session_state.messages.append({"role": "assistant", "parts": "Please specify a location."})
        else:
            response, updated_history = response_generator(prompt, st.session_state.messages)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "parts": response})