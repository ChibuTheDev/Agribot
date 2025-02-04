import streamlit as st
from dotenv import load_dotenv
import json
from chat import get_chat_response
from  weather_utils import get_5day_forecast


load_dotenv()

def response_generator(prompt, history):
    response, updated_history = get_chat_response(prompt, history)
    return response, updated_history 

## 5 day forecast was here


st.title("Agri-Bot")

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

        **Bonus**: I can also provide a 5-day weather forecast if you ask nicely! 🌦️
    ''')



if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"])

if prompt := st.chat_input("Ask me anything about Agriculture!"):
    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if ("5 day forecast in" in prompt.lower()) or ("5-day forecast" in prompt.lower()) or ("5 day weather" in prompt.lower()) or ("breakdown the weather" in prompt.lower()):
            try:
                location = prompt.lower().split("in")[-1].strip() if "in" in prompt.lower() else prompt.lower().replace("5 day forecast", "").replace("5-day forecast", "").replace("5 day weather", "").replace("breakdown the weather", "").strip()
                forecasts = get_5day_forecast(location)
                if isinstance(forecasts, str): #Error message
                    st.markdown(forecasts)
                    st.session_state.messages.append({"role": "assistant", "parts": forecasts})
                else:
                    st.markdown(forecasts)  # Display the table
                    st.session_state.messages.append({"role": "assistant", "parts": forecasts})
                    if "breakdown the weather" in prompt.lower():  #  Allowing gemini to make use of the fetcheddata
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





print(st.session_state)