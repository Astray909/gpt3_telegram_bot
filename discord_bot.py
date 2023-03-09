import os
import discord
import requests
import json
import random

# OpenAI secret Key
API_KEY = input("Enter API key: ")
# Models: text-davinci-003,text-curie-001,text-babbage-001,text-ada-001
MODEL = "text-davinci-003"
# MODEL = "gpt-3.5-turbo"
# Telegram secret access bot token
BOT_TOKEN = input("Enter bot token: ")

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

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": "gpt-3.5-turbo", "prompt": prompt, "temperature": 0.5, "max_tokens": 300},
        timeout=100,
    )

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response and return the generated text
        response_json = json.loads(response.text)
        return response_json['choices'][0]['text']
    else:
        # Handle errors
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

#first event :logging in
@client.event
async def on_ready():
    print("successful login as {0.user}".format(client))
 
 
#second event: sending message
@client.event
async def on_message(message):
    #check who sent the message
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
 
 
#getting the secret token
client.run(BOT_TOKEN)