import requests
import json
import os
import threading
import time

API_KEY = input("Enter API key: ")
MODEL = "text-davinci-003"
BOT_TOKEN = input("Enter bot token: ")

conversation_history = []

def clear_conversation_history():
    global conversation_history
    conversation_history = []

def generate_gpt_turbo(prompt):
    if prompt is None:
        raise ValueError("Prompt is not set.")

    conversation_history.append({"role": "user", "content": prompt})
    
    messages = [{"role": "system", "content": "You are a cheerful and quirky assistant."}]
    messages.extend(conversation_history)

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": "gpt-3.5-turbo", "messages": messages, "temperature": 0.5, "max_tokens": 300},
        timeout=30,
    )

    if response.status_code == 200:
        response_json = json.loads(response.text)
        reply = response_json['choices'][0]['message']['content']
        conversation_history.append({"role": "assistant", "content": reply})
        return reply
    else:
        print(f'Request failed with status code {response.status_code}: {response.text}')

def openAImage(prompt):
    resp = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"prompt": prompt, "n": 1, "size": "1024x1024"},
        timeout=10,
    )
    response = json.loads(resp.text)
    return response["data"][0]["url"]

CHATBOT_HANDLE = input("Enter bot handle: ")

def telegram_bot_sendtext(bot_message, chat_id, msg_id):
    data = {"chat_id": chat_id, "text": bot_message, "reply_to_message_id": msg_id}
    response = requests.post(
        "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage",
        json=data,
        timeout=5,
    )
    return response.json()

def telegram_bot_sendimage(image_url, group_id, msg_id):
    data = {"chat_id": group_id, "photo": image_url, "reply_to_message_id": msg_id}
    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendPhoto"

    response = requests.post(url, data=data, timeout=5)
    return response.json()

def Chatbot():
    cwd = os.getcwd()
    filename = cwd + "/chatgpt.txt"
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("1")
    else:
        print("File Exists")

    with open(filename) as f:
        last_update = f.read()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update}"
    response = requests.get(url, timeout=5)
    data = json.loads(response.content)
    print(data)

    for result in data["result"]:
        try:
            if float(result["update_id"]) > float(last_update):
                if not result["message"]["from"]["is_bot"]:
                    last_update = str(int(result["update_id"]))

                    msg_id = str(int(result["message"]["message_id"]))
                    chat_id = str(result["message"]["chat"]["id"])

                    if "/clear_history" in result["message"]["text"]:
                        clear_conversation_history()
                        bot_response = "Conversation history cleared."
                        print(telegram_bot_sendtext(bot_response, chat_id, msg_id))

                    else:
                        if "/img" in result["message"]["text"]:
                            prompt = result["message"]["text"].replace("/img", "")
                            bot_response = openAImage(prompt)
                            print(telegram_bot_sendimage(bot_response, chat_id, msg_id))

                        if "/gpt_chat" in result["message"]["text"]:
                            prompt = result["message"]["text"].replace("/gpt_chat", "")
                            bot_response = generate_gpt_turbo(prompt)
                            print(telegram_bot_sendtext(bot_response, chat_id, msg_id))

                        if "reply_to_message" in result["message"]:
                            if result["message"]["reply_to_message"]["from"]["is_bot"]:
                                prompt = result["message"]["text"]
                                bot_response = generate_gpt_turbo(prompt)
                                print(telegram_bot_sendtext(bot_response, chat_id, msg_id)) 

        except Exception as e:
            print(e)

    with open(filename, "w") as f:
        f.write(last_update)

    return "done"

def main():
    timertime = 5
    Chatbot()
    threading.Timer(timertime, main).start()

if __name__ == "__main__":
    while True:
        try:
            main()
            break  # Exit the loop after successful execution
        except Exception as e:
            print(f"Bot crashed with error: {e}. Restarting...")
            time.sleep(5)  # Wait for 5 seconds before restarting
