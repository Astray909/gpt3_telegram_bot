import os
import discord
import requests
import json
import random

API_KEY = input("Enter API key: ")
MODEL = "text-davinci-003"
BOT_TOKEN = input("Enter bot token: ")

conversation_history = []

def clear_conversation_history():
    global conversation_history
    conversation_history = []

def openAI(prompt):
    # Make the request to the OpenAI API
    response = requests.post(
        "https://api.openai.com/v1/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "prompt": prompt, "temperature": 0.4, "max_tokens": 300},
        timeout=100,
    )

    result = response.json()
    print(result)
    final_result = "".join(choice["text"] for choice in result["choices"])
    return final_result

def generate_gpt_turbo(prompt):
    if prompt is None:
        raise ValueError("Prompt is not set.")

    conversation_history.append({"role": "user", "content": prompt})
    
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    messages.extend(conversation_history)

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": "gpt-3.5-turbo", "messages": messages, "temperature": 0.5, "max_tokens": 300},
        timeout=100,
    )

    if response.status_code == 200:
        response_json = json.loads(response.text)
        reply = response_json['choices'][0]['message']['content']
        conversation_history.append({"role": "assistant", "content": reply})
        return reply
    else:
        print(f'Request failed with status code {response.status_code}: {response.text}')

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
    if msg.startswith('$gpt_generate'):
        msg_headless = msg.replace('$gpt_generate', '')
        await message.channel.send(f"{message.author.mention}" + generate_gpt_turbo(msg_headless))
    elif msg.startswith('$davinci_generate'):
        msg_headless = msg.replace('$davinci_generate', '')
        await message.channel.send(f"{message.author.mention}" + openAI(msg_headless))
    elif msg.startswith('$gpt_img'):
        msg_headless = msg.replace('$gpt_img', '')
        await message.channel.send(f"{message.author.mention}" + openAImage(msg_headless))
    elif msg.startswith('$clear_history'):
        clear_conversation_history()
        await message.channel.send("Conversation history cleared.")

client.run(BOT_TOKEN)
