# Importing required packages
import streamlit as st
import openai
import uuid
import time
import pandas as pd
import io
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Your chosen model
MODEL = "gpt-4-1106-preview"

# Function for the chatbot's initial response
def start_chat():
    initial_prompt = "Hello, can you help me?"
    # Sending the initial message as if it's from the user
    message_data = {
        "thread_id": st.session_state.thread.id,
        "role": "user",
        "content": initial_prompt
    }
    response = client.beta.threads.messages.create(**message_data)

    # Debugging: Print the entire response
    st.write("API Response:", response)

    # Append the response to the messages list
    if 'data' in response and isinstance(response.data, list):
        st.session_state.messages.extend(response.data)
    else:
        st.error("Failed to receive a valid response from the chatbot.")

    st.write("Message sent to the chatbot:", initial_prompt)  # Debugging information

    
# Initialize session state variables
if "first_visit" not in st.session_state:
    st.session_state.first_visit = True

if st.session_state.first_visit:
    with st.chat_message('assistant'):
        st.markdown("Hello, please tell me your name, first and last, and the period you have Mr. Ward's English class.")
    st.session_state.first_visit = False
    
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "run" not in st.session_state:
    st.session_state.run = {"status": None}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "retry_error" not in st.session_state:
    st.session_state.retry_error = 0

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "run" not in st.session_state:
    st.session_state.run = {"status": None}

# Ensure messages is always a list
if "messages" not in st.session_state or not isinstance(st.session_state.messages, list):
    st.session_state.messages = []

# Set up the page
st.set_page_config(page_title="Sarcastic Vocab Wizard")
st.sidebar.title("Sarcastic Vocab Wizard")
st.sidebar.divider()  

# Initialize OpenAI assistant
if "assistant" not in st.session_state:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    st.session_state.assistant = openai.beta.assistants.retrieve(st.secrets["OPENAI_ASSISTANT"])
    st.session_state.thread = client.beta.threads.create(
        metadata={'session_id': st.session_state.session_id}
    )

# Add a button to start the chat
st.button("Reset", type="primary")
if st.button('Start Chatbot'):
    start_chat()

# [Rest of your existing code for displaying messages and handling user inputs]

# Display chat messages
elif hasattr(st.session_state.run, 'status') and st.session_state.run.status == "completed":
    st.session_state.messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread.id
    )
    for message in reversed(st.session_state.messages.data):
        if message.role in ["user", "assistant"]:
            with st.chat_message(message.role):
                for content_part in message.content:
                    message_text = content_part.text.value
                    st.markdown(message_text)

# Chat input and message creation with file ID
if prompt := st.chat_input("How can I help you?"):
    with st.chat_message('user'):
        st.write(prompt)

    message_data = {
        "thread_id": st.session_state.thread.id,
        "role": "user",
        "content": prompt
    }

    # Include file ID in the request if available
    if "file_id" in st.session_state:
        message_data["file_ids"] = [st.session_state.file_id]

    st.session_state.messages = client.beta.threads.messages.create(**message_data)

    st.session_state.run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread.id,
        assistant_id=st.session_state.assistant.id,
    )
    if st.session_state.retry_error < 3:
        time.sleep(1)
        st.rerun()

# Handle run status
if hasattr(st.session_state.run, 'status'):
    if st.session_state.run.status == "running":
        with st.chat_message('assistant'):
            st.write("Thinking ......")
        if st.session_state.retry_error < 3:
            time.sleep(1)
            st.rerun()

    elif st.session_state.run.status == "failed":
        st.session_state.retry_error += 1
        with st.chat_message('assistant'):
            if st.session_state.retry_error < 3:
                st.write("Run failed, retrying ......")
                time.sleep(3)
                st.rerun()
            else:
                st.error("FAILED: The OpenAI API is currently processing too many requests. Please try again later ......")

    elif st.session_state.run.status != "completed":
        st.session_state.run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread.id,
            run_id=st.session_state.run.id,
        )
        if st.session_state.retry_error < 3:
            time.sleep(3)
            st.rerun()
