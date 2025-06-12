import ollama

response = ollama.chat(model='gemma3:4b', messages=[
    {'role': 'user', 'content': 'Why is the sky blue?'}
])
print(response['message']['content'])
