from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

SYSTEM_TEMPLATE = """You are Blake Samaha, a dedicated professional with a comprehensive resume and portfolio. Your resume clearly states that your full name is Blake Samaha, along with other important details about your professional background. As a helpful AI assistant, you must always respond in the persona of Blake Samaha and use the resume context provided to answer the user's questions. When asked about your name or personal details, always respond with 'My name is Blake Samaha' along with any additional relevant information from your resume. If the provided context does not include enough details, state that you have limited information rather than inventing answers."""

HUMAN_TEMPLATE = "{message}"

system_message_prompt = SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE)
human_message_prompt = HumanMessagePromptTemplate.from_template(HUMAN_TEMPLATE)

chat_prompt = ChatPromptTemplate.from_messages([
    system_message_prompt,
    human_message_prompt
])

def get_chat_prompt(context: str, message: str):
    """Generate a chat prompt with the given context and user message."""
    # Use fallback resume context if context is empty or not useful
    if not context or "No relevant context found" in context:
        context = ("Blake Samaha Resume Information:\n"
                   "Full Name: Blake Samaha\n"
                   "Current Position: [Your Current Position]\n"
                   "Background: A dedicated professional with extensive experience and a strong portfolio.\n"
                   "Education: [Your Education Details]\n"
                   "Skills: [Your Key Skills]")
    return chat_prompt.format_messages(
        context=context,
        message=message
    )
