import autogen

from google import genai
# from openai import AzureOpenAI
from app.azure_search import retrieve_chunks
from app.logger import log_interaction, generate_question_id
from app.config import GOOGLE_API_KEY

# Gemini client
client = genai.Client(api_key=GOOGLE_API_KEY)


#  Custom Gemini function
def ask_gemini(prompt):
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt
    )
    return response.text

# prompt guard function to detect potential prompt injection attempts
def detect_prompt_injection(query):
    patterns = [
        "ignore previous instructions",
        "act as",
        "bypass",
        "system prompt",
        "jailbreak",
        "secrets",
        "confidential",
        "private",
        "hidden",
        "malicious",
        "exploit",
        "vulnerability"
    ]
    return any(p in query.lower() for p in patterns)


# Assistant Agent
assistant = autogen.AssistantAgent(
    name="Assistant",
    llm_config=False,
    system_message="You are a helpful AI assistant."
)

# Verifier Agent
verifier = autogen.AssistantAgent(
    name="Verifier",
    llm_config=False,
    system_message="""
    You are a strict verification agent.

    You will receive:
    - Context
    - Answer

    Your task:
    - Check if answer is fully supported by the context
    - Do NOT assume anything outside context

    Output ONLY one of:
    ✔ ANSWER VERIFIED
    ❌ HALLUCINATION DETECTED
    """
)

# Retriever Agent
retriever = autogen.AssistantAgent(
    name="Retriever",
    llm_config=False,
    system_message="""
    You are a retrieval agent.

    Your job:
    - Receive a user query
    - Retrieve relevant context from knowledge base
    - Return ONLY the retrieved text
    """
)

# Rewriter Agent
rewriter = autogen.AssistantAgent(
    name="Rewriter",
    llm_config=False,
    system_message="""
    You are a rewriting agent.

    Your job:
    - Clean the answer
    - Remove names, emails, institutions, and personal info
    - Remove unnecessary repetitions
    - Make the answer clear, structured, and professional
    """
)

#  Override reply behavior
def custom_reply(recipient, messages, sender, config):
    
    user_query = messages[-1]["content"]

    question_id = generate_question_id()
    session_id = config.get("session_id", "unknown_session")
    source = config.get("source")
    user_id = config.get("user_id")
    print("[Active Source]:", source)
    prompt_injection_flag = detect_prompt_injection(user_query)

    if prompt_injection_flag:
        final_answer = "⚠️ Unsafe query detected. Request blocked."

        print("\n[Prompt Injection Detected]")

        log_interaction({
            "question_id": question_id,
            "session_id": session_id,
            "query": user_query,
            "response": final_answer,
            "hallucination": False,
            "toxicity": False,
            "prompt_injection": True
        })

        return True, final_answer

    print("\n[User Query]:", user_query)

    #  Handle vague/short queries
    if len(user_query.split()) < 3:
        final_answer = "Please ask a more specific question related to the documents."

        log_interaction({
            "question_id": question_id,
            "session_id": session_id,
            "query": user_query,
            "response": final_answer,
            "hallucination": False,
            "toxicity": False,
            "prompt_injection": False
        })

        return True, final_answer

    # Step 1: Retriever Agent 
    success, context = retriever_reply(
        retriever,
        [{"content": user_query, "source": source, "user_id": user_id}],
        assistant,
        {}
    )

    print("\n[Retrieved Context]:\n", context)

    if not context.strip():
        print("⚠️ No context found — skipping Gemini")
        return True, "⚠️ No relevant data found in this document."

    # Step 2: Generate answer
    prompt = f"""
    Answer the question based ONLY on the context below.

    Context:
    {context}

    Question:
    {user_query}
    """

    answer = ask_gemini(prompt)
    print("\n[Generated Answer]:\n", answer)

    # Step 3: Verifier Agent
    verification_prompt = f"""
    Context:
    {context}

    Answer:
    {answer}

    Check if the answer is supported by the context.
    Reply ONLY:
    - ANSWER VERIFIED
    - HALLUCINATION DETECTED
    """

    success, verification_result = verifier_reply(
        verifier,
        [{"content": verification_prompt}],
        assistant,
        {}
    )

    print("\n[Verification Result]:", verification_result)

    # Step 4: Final decision
    if "HALLUCINATION" in verification_result.upper().strip():
        final_answer = "⚠️ The answer may not be reliable based on retrieved context."
    else:
        # Step 5: Rewriter Agent
        rewrite_prompt = f"""
        Clean and improve the following answer and answer the question in points form according to the information provided only.

        Remove:
        - Names
        - Emails
        - Institutions
        - Repetitions

        Make it clear and professional.

        Answer:
        {answer}
        """

        success, final_answer = rewriter_reply(
            rewriter,
            [{"content": rewrite_prompt}],
            assistant,
            {}
        )

    print("\n[Final Answer]:\n", final_answer)

    hallucination_flag = "HALLUCINATION" in verification_result.upper()

    log_interaction({
    "question_id": question_id,
    "session_id": session_id,
    "query": user_query,
    "response": final_answer,
    "hallucination": hallucination_flag,
    "toxicity": False,
    "prompt_injection": False
    })

    return True, final_answer

def verifier_reply(recipient, messages, sender, config):
    prompt = messages[-1]["content"]
    result = ask_gemini(prompt)
    return True, result

def retriever_reply(recipient, messages, sender, config):
    query = messages[-1]["content"]
    source = messages[-1].get("source")
    user_id = messages[-1].get("user_id")

    print("\n[Retriever Received Query]:", query)
    print("[Retriever Source]:", source)
    
    context = retrieve_chunks(query, source, user_id)

    print("\n[Retriever Output]:\n", context)

    return True, context

def rewriter_reply(recipient, messages, sender, config):
    prompt = messages[-1]["content"]
    result = ask_gemini(prompt)
    return True, result

assistant.register_reply(
    autogen.Agent,
    custom_reply,
    config={}
)

verifier.register_reply(
    autogen.Agent,
    verifier_reply,
    config={}
)

retriever.register_reply(
    autogen.Agent,
    retriever_reply,
    config={}
)

rewriter.register_reply(
    autogen.Agent,
    rewriter_reply,
    config={}
)
