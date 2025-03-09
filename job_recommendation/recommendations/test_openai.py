import os
from transformers import pipeline

# Set up Hugging Face API token (you can also set it in your environment variables)
api_token = "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"  # Replace with your API token
os.environ["HF_HOME"] = api_token  # Set the token



# Load a pre-trained model for text generation or classification
generator = pipeline("text-generation", model="gpt2")

prompt = "hello how are you "
result = generator(prompt, max_length=100)
print(result)
