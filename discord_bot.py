import discord
import requests
import json
from PyPDF2 import PdfReader
import io
import time

last_request_time = None

API_KEY = input("Enter API key: ")
MODEL = "text-davinci-003"
BOT_TOKEN = input("Enter bot token: ")
MAX_TOKEN = int(input("Enter max token: "))

conversation_histories = {}

def clear_conversation_history(user_id):
    global conversation_histories
    conversation_histories[user_id] = []

def openAI(prompt):
    # Make the request to the OpenAI API
    response = requests.post(
        "https://api.openai.com/v1/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "prompt": prompt, "temperature": 0.4, "max_tokens": MAX_TOKEN},
        timeout=100,
    )

    result = response.json()
    print(result)
    final_result = "".join(choice["text"] for choice in result["choices"])
    return final_result

def read_pdf(file):
    pdf = PdfReader(file)
    pages = []
    for page in range(len(pdf.pages)):
        pages.append(pdf.pages[page].extract_text())
    return pages

def summarize_with_gpt3(text):
    prompt = f"My task is to summarize the following text:\n\n{text}\n\nSummary:"

    response = requests.post(
        "https://api.openai.com/v1/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "prompt": prompt, "temperature": 0.2, "max_tokens": MAX_TOKEN},
        timeout=100,
    )

    result = response.json()
    final_result = "".join(choice["text"] for choice in result["choices"])
    return final_result

def generate_gpt_turbo(prompt, user_id, gpt_model):
    if gpt_model == 3:
        chosen_model = "gpt-3.5-turbo"
    elif gpt_model == 4:
        chosen_model = "gpt-4"
    if prompt is None:
        raise ValueError("Prompt is not set.")

    if user_id not in conversation_histories:
        conversation_histories[user_id] = []

    conversation_histories[user_id].append({"role": "user", "content": prompt})
    
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    messages.extend(conversation_histories[user_id])
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"model": "gpt-3.5-turbo", "messages": messages, "temperature": 0.5, "max_tokens": MAX_TOKEN},
            timeout=60,
        )

        if response.status_code == 200:
            response_json = json.loads(response.text)
            reply = response_json['choices'][0]['message']['content']
            conversation_histories[user_id].append({"role": "assistant", "content": reply})
            return reply
        else:
            print(f'Request failed with status code {response.status_code}: {response.text}')

    except requests.exceptions.Timeout:
        return "timeout, please try again in 30 seconds."


def openAImage(prompt):
    # Make the request to the OpenAI API
    resp = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"prompt": prompt, "n": 1, "size": "1024x1024"},
        timeout=10,
    )
    response = json.loads(resp.text)
    return response["data"][0]["url"]


intents = discord.Intents().all()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("successful login as {0.user}".format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    msg = message.content
    user_id = message.author.id
    if msg.startswith('$gpt_generate'):
        msg_headless = msg.replace('$gpt_generate', '')
        await message.channel.send(f"{message.author.mention}\n" + generate_gpt_turbo(msg_headless, user_id, 3))
    elif msg.startswith('$gpt4_generate'):
        global last_request_time

        # Check if a request has been made in the last minute
        if last_request_time is not None and time.time() - last_request_time < 20:
            await message.channel.send("Rate limit exceeded. Please wait for a minute before making another request.")

        # Update the time of the last request
        last_request_time = time.time()

        msg_headless = msg.replace('$gpt4_generate', '')
        await message.channel.send(f"{message.author.mention}\n" + generate_gpt_turbo(msg_headless, user_id, 4))
    elif message.content.startswith('$gpt_pdf') and message.attachments:
        if message.attachments[0]:
            file = await message.attachments[0].read(use_cached=False)
            pages = read_pdf(io.BytesIO(file))
            print(pages)
            summaries = []
            await message.channel.send(f"{message.author.mention}\nSummary Beginning:\n")
            for page in pages:
                if page.strip():  # Ensure the page is not just whitespace
                    summary = summarize_with_gpt3(page)
                    summaries.append(summary)
                    await message.channel.send(f"{message.author.mention}" + summary)
            with open("summary.txt", "w") as f:
                f.write("\n".join(summaries))
            await message.channel.send(f"{message.author.mention}\nSummary Finished\n")
            await message.channel.send(file=discord.File("summary.txt"))
        else:
            await message.channel.send(f"{message.author.mention}\nPlease Include Attachment and try again.\n")
    elif msg.startswith('$davinci_generate'):
        msg_headless = msg.replace('$davinci_generate', '')
        await message.channel.send(f"{message.author.mention}" + openAI(msg_headless))
    elif msg.startswith('$gpt_img'):
        msg_headless = msg.replace('$gpt_img', '')
        await message.channel.send(f"{message.author.mention}" + openAImage(msg_headless))
    elif msg.startswith('$clear_history'):
        clear_conversation_history(user_id)
        await message.channel.send("Conversation history cleared.")

client.run(BOT_TOKEN)
