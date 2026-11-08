
from core.cloudflare_llm import generate_response

messages = [
    {
        "role": "system",
        "content": "You are a helpful AI assistant specializing in Indian cybercrime."
    },
    {
        "role": "user",
        "content": "Explain what a victim should do immediately after UPI fraud in India. Answer in simple English."
    }
]

try:
    answer = generate_response(messages)
    print("\nCLOUDFLARE LLM RESPONSE:\n")
    print(answer)

except Exception as e:
    print("ERROR:", e)
