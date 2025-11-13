from ai.models.review import Review

from ai.open_ai_client import OpenAIClient
from server import MODEL


def parse_review(args):
    completion = OpenAIClient.new().beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": args.review,
            }
        ],
        response_format=Review,
    )
    print(completion.choices[0].message.parsed)
