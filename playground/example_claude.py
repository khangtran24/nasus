import os
from anthropic import Anthropic

os.environ["CLAUDE_CODE_OAUTH_TOKEN "] = "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"
client = Anthropic(auth_token=os.environ["CLAUDE_CODE_OAUTH_TOKEN "])
message = client.messages.create(
    max_tokens=1024,
    messages=[{
        "content": "Hello, world",
        "role": "user",
    }],
    model="claude-sonnet-4-5",
)
print(message.id)

