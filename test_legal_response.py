
from core.legal_response import answer_legal_question

question = """
Someone clicked a fake bank KYC link and lost
Rs. 75,000 through UPI. What should they do?
"""

try:
    result = answer_legal_question(question)

    print("\n========== AI LEGAL ANSWER ==========\n")
    print(result["answer"])

    print("\n========== RETRIEVED SOURCES ==========\n")

    for source in result["sources"]:
        print(
            f"{source['file_name']} | Page: {source['page']}"
        )

    print("\nRetrieved chunks:", result["retrieved_count"])

except Exception as e:
    print("ERROR:", e)
