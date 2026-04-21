import streamlit as st
from app.main import custom_reply
from app.logger import generate_session_id
import requests
import re

st.set_page_config(page_title="Q&A Chatbot", layout="centered")

# Header
st.title("📄 RAG Assistant")
st.caption("Ask questions from your indexed documents")

st.subheader("Upload Document")

uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"])

if uploaded_file is not None:
    if st.button("Upload to System"):
        with st.spinner("Uploading..."):

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "application/pdf"
                )
            }

            try:
                response = requests.post(
                    "http://127.0.0.1:8000/upload",
                    files=files,
                    data={"user_id": st.session_state.user_id}
                )

                if response.status_code == 200 and "error" not in response.text:
                    
                    #  SET CURRENT DOCUMENT (IMPORTANT)
                    user_id = st.session_state.user_id

                    raw_name = uploaded_file.name.rsplit(".", 1)[0]
                    file_name = re.sub(r'[^a-zA-Z0-9_-]', '_', raw_name)

                    st.session_state.current_doc = f"{user_id}_{file_name}"

                    st.success(f"✅ {uploaded_file.name} uploaded & processing started!")
                    st.info("⏳ Wait a few seconds before asking questions (indexing in background).")

                else:
                    st.error(f"❌ Upload failed: {response.text}")

            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
            
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = generate_session_id()

if "user_id" not in st.session_state:
    st.session_state.user_id = generate_session_id()

if "current_doc" not in st.session_state:
    st.session_state.current_doc = None

if st.session_state.current_doc:
   st.success(f"📄 Active Document: {st.session_state.current_doc}")
else:
    st.warning("⚠️ No document selected. Upload a PDF first.")

# Display chat 
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box 
user_input = st.chat_input("Type your question...")

if user_input:

     # 🚫 BLOCK if no document uploaded
    if not st.session_state.current_doc:
        st.warning("⚠️ Please upload a document first.")
        st.stop()

    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # Debug info
    print("SESSION USER ID:", st.session_state.user_id)
    print("SESSION ID:", st.session_state.session_id)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            success, answer = custom_reply(
                None,
                [{"content": user_input}],
                None,
                {
                 "session_id": st.session_state.session_id,
                 "source": st.session_state.current_doc,
                 "user_id": st.session_state.user_id
                }
            )
            st.markdown(answer)

    # Save response
    st.session_state.messages.append({"role": "assistant", "content": answer})

# Clear chat button
if st.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Footer
st.markdown("---")
st.caption("Powered by AutoGen + Azure AI Search + Gemini")