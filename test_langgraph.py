
from agents.legal_agent import chat_with_legal_agent

thread_id = "cybercrime-test-001"

questions = [
    "I lost Rs. 50000 through UPI fraud.",
    "It happened yesterday.",
    "What should I do now?"
]

for question in questions:

    print("\nUSER:", question)

    answer = chat_with_legal_agent(
        question,
        thread_id
    )

    print("\nASSISTANT:", answer)
