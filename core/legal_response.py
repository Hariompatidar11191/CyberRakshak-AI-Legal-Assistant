
from core.cloudflare_llm import generate_response
from core.emergency_detector import detect_emergency
from core.query_router import needs_retrieval

from core.rag_engine import (
    retrieve_legal_information,
    get_legal_sources
)


SYSTEM_PROMPT = """
You are an AI Cybercrime Legal Assistant specializing
in Indian cybercrime and banking fraud.

Your responsibilities:

1. Understand the user's cybercrime complaint.
2. Retrieve and use the supplied legal context.
3. Explain relevant laws in simple language.
4. Provide practical steps the victim can take.
5. Support Hindi and English.
6. Mention legal provisions only when supported
   by reliable context or clearly identified as needing verification.
7. Never invent legal sections, case laws, or punishments.
8. Clearly distinguish historical information from current rules.
9. If context is insufficient, say so.
10. Do not claim to be a licensed lawyer.

LANGUAGE RULES:
- Follow the response language requested by the user.
- If the user asks in Hindi, respond in Hindi.
- If the user asks in English, respond in English.
- Do not refuse to answer in Hindi.

CRITICAL FINANCIAL FRAUD ACCURACY RULES:

- India's national cyber financial fraud helpline is 1930.
- NEVER identify 1966 as the cybercrime or UPI fraud helpline.
- Direct financial cyber fraud victims to:
  1930
  https://cybercrime.gov.in

- Tell victims to immediately contact their bank
  through its official channel and report the transaction.

- Recommend raising a dispute through the relevant
  UPI application or payment provider.

- Preserve transaction IDs, UTR, screenshots,
  bank statements and complaint acknowledgements.

- Do not guarantee recovery or a refund.
- Do not claim that an FIR is always required
  before reporting financial cyber fraud.
- Do not invent helpline numbers, bank contacts,
  deadlines or legal provisions.

- Prioritize immediate safety and reporting steps
  over lengthy legal explanations.

Always provide source filenames and page numbers
when retrieved sources are available.

Give structured, clear, empathetic answers.
"""


def answer_legal_question(
    question,
    chat_history=None,
    original_question=None
):

    # Use original user message for intent detection
    user_question = original_question or question

    # Detect possible financial cyber fraud
    is_emergency = detect_emergency(user_question)

    emergency_instruction = ""

    if is_emergency:
        emergency_instruction = """
IMPORTANT: POSSIBLE FINANCIAL CYBER FRAUD DETECTED.

Prioritize these immediate actions:

1. Call India's national cyber financial fraud helpline 1930.
2. Report the incident at https://cybercrime.gov.in.
3. Immediately contact the bank through its official
   customer support channel.
4. Report the unauthorized transaction to the UPI
   application or payment provider, if applicable.
5. Preserve transaction IDs, UTR numbers, screenshots,
   SMS messages and bank statements.

Do not guarantee recovery of money.
Do not invent reporting deadlines or legal provisions.
Do not delay immediate reporting while researching laws.
"""

    # Retrieve legal documents when needed
    if needs_retrieval(user_question):

        documents, context = retrieve_legal_information(
            question,
            top_k=3
        )

        context = context[:9000]

    else:
        documents, context = [], ""

    # Extract legal sources
    sources = get_legal_sources(documents)

    # Build LLM messages
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # Add recent conversation history
    if chat_history:
        messages.extend(chat_history[-6:])

    # Construct user prompt
    user_prompt = f"""
USER QUESTION:
{question}

EMERGENCY DETECTION:
{"Possible financial cyber fraud detected." if is_emergency else "No financial fraud emergency keyword detected."}

EMERGENCY INSTRUCTIONS:
{emergency_instruction if emergency_instruction else "No additional emergency instructions."}

RETRIEVED LEGAL CONTEXT:
{context if context else "No relevant legal documents found."}

INSTRUCTIONS:

1. Answer the user's actual question.
2. Use retrieved legal context where relevant.
3. Separate general safety guidance from legal conclusions.
4. Do not fabricate legal provisions or citations.
5. For greetings such as hello, hi or namaste,
   respond directly without discussing legal provisions.
6. For financial fraud, prioritize immediate reporting.
7. Use the official helpline number 1930.
8. Do not rely on outdated or unverified information
   from historical documents.
9. If context does not support an answer,
   clearly explain the limitation.
10. Respond in the language requested by the user.
"""

    messages.append({
        "role": "user",
        "content": user_prompt
    })

    # Generate response
    answer = generate_response(
        messages,
        temperature=0.2,
        max_tokens=500
    )

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_count": len(documents),
        "is_emergency": is_emergency
    }
