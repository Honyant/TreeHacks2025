from openai import OpenAI


def query_perplexity(client: OpenAI, query: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence assistant and you need to "
                "engage in a helpful, detailed, polite conversation with a user. Please give concise answers."
            ),
        },
        {"role": "user", "content": query},
    ]
    print(f"[Perplexity API] Query: {query}")
    response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages,
    )
    print(f"[Perplexity API] Response: {response.choices[0]}")
    return response.choices[0].message.content


def send_email(to: str, subject: str, body: str) -> str:
    print(f"[Email Simulation] To: {to}, Subject: {subject}\nBody: {body}")
    return "Email sent."


def video_analysis(video_url: str) -> str:
    print(
        "[Video Analysis Simulation] Steps: Download video, extract frames, analyze frames, summarize results."
    )
    return "Video analysis simulated."
