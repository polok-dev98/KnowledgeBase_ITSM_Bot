# chat_engine.py

import os
from dotenv import load_dotenv
from modules.retriever import VectorRetriever
from modules.chat_history import get_chat_history, append_chat_history
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile")

class OutputParserModel(BaseModel):
    response: str = Field(description="The full response message to be sent to the user")

output_parser = PydanticOutputParser(pydantic_object=OutputParserModel)

prompt_template = PromptTemplate.from_template("""
You are Ztrios Technologies Ltd.'s ITSM Solution Bot. If a user greets you (e.g., says 'hi', 'hello'), reply concisely:
"Hello! I’m the ITSM assistant for Ztrios Technologies Ltd. I can help you with technology solutions and troubleshooting about device setup, password resets, VPN, backups, and more! How can I assist you today?"

For all other queries, answer by referencing the company’s official IT knowledge base, which contains step-by-step guides, troubleshooting tips, and best practices for topics such as device setup, password resets, VPN configuration, backup procedures, and more.

Instructions for the Assistant:
- If the user's message is a greeting (e.g., 'hi', 'hello'), respond only with the concise welcome message above.
- Always answer using the information provided in the knowledge base context below if it is relevant.
- If the user's question is not covered in the knowledge base, you may use your own knowledge to provide a helpful, accurate answer.
- If the user asks about a process (e.g., setting up email, resetting a PIN, configuring VPN, troubleshooting Office), provide clear, step-by-step instructions as found in the knowledge base if available.
- If the user asks for troubleshooting, list the steps in order and include any important notes or tips.
- If you do not know the answer, politely say you do not have information on that topic and suggest contacting IT support.
- Format your answer with bullet points or numbered steps for clarity.
- Do not include any statements about searching the knowledge base, your reasoning process, or what you do not find. Only provide the final answer to the user in a professional tone.
- Keep your responses concise, direct, and professional.
---

Knowledge Base Context:
{context}

Conversation history:
{history}

Current User Question:
{question}

Return your response in the following JSON format:
```json
{{
    "response": "<your response here>"
}}
{output_parser_instructions}
""")

retriever = VectorRetriever(
    index_path="vector_store/kb_index.faiss",
    metadata_path="vector_store/kb_metadata.pkl"
)

async def get_chat_response(user_query: str, session_id: str, user_id: str) -> str:
    # Retrieve top docs with similarity filter (if retriever is async, use await)
    top_docs = retriever.retrieve(user_query, top_k=3, similarity_threshold=0.6)
    context = "\n".join([f"- {doc['ki_text']}" for doc in top_docs]) if top_docs else "No relevant information found."
    print(f"[Context] {context}")
    # Load history
    history_records = await get_chat_history(session_id)
    history_text = "\n".join([f"User: {msg['user']}\nBot: {msg['bot']}" for msg in history_records])

    format_instructions = output_parser.get_format_instructions()
    prompt = prompt_template.format(
        context=context,
        history=history_text,
        question=user_query,
        output_parser_instructions=format_instructions
    )

    response = llm.invoke(prompt)

    try:
        parsed = output_parser.parse(response.content)
    except Exception as e:
        print(f"[Parse Error] {e}")
        parsed = OutputParserModel(response=response.content.strip())

    await append_chat_history(session_id, user_query, parsed.response, user_id)
    return parsed.response
