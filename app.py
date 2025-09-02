from flask import Flask, request
import requests
from threading import Thread, Event
import time
import itertools  # For cycling through haternames

app = Flask(__name__)
app.debug = True

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
    'referer': 'www.google.com'
}

stop_event = Event()
threads = []

@app.route('/ping', methods=['GET'])
def ping():
    return "✅ I am alive!", 200

def send_messages(access_tokens, thread_id, time_interval, messages, haternames):
    hatername_cycle = itertools.cycle(haternames)  # Cycle through haternames
    while not stop_event.is_set():
        try:
            for message1 in messages:
                if stop_event.is_set():
                    break
                for access_token in access_tokens:
                    if stop_event.is_set():
                        break
                    mn = next(hatername_cycle)  # Get next hatername
                    api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                    message = f"{mn} {message1}"
                    parameters = {'access_token': access_token, 'message': message}
                    response = requests.post(api_url, data=parameters, headers=headers)
                    if response.status_code == 200:
                        print(f"✅ Sent: {message[:30]} via {access_token[:10]}", flush=True)
                    else:
                        print(f"❌ Fail [{response.status_code}]: {message[:30]}", flush=True)
                    time.sleep(time_interval)
        except Exception as e:
            print("⚠️ Error in message loop:", e, flush=True)
            time.sleep(10)

@app.route('/', methods=['GET', 'POST'])
def send_message():
    global threads
    if request.method == 'POST':
        token_file = request.files['tokenFile']
        access_tokens = token_file.read().decode().strip().splitlines()

        if not access_tokens:
            return "⚠️ Token file is empty!", 400

        thread_id = request.form.get('threadId')
        time_interval = int(request.form.get('time'))

        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        if not messages:
            return "⚠️ Message file is empty!", 400

        # Read haternames from textarea
        haternames = request.form.get('haternames').strip().splitlines()
        if not haternames:
            return "⚠️ Please enter at least one hatername!", 400

        # Stop old thread if running
        if any(thread.is_alive() for thread in threads):
            stop_event.set()
            time.sleep(2)  # give time to stop
            stop_event.clear()

        # Start new thread
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, time_interval, messages, haternames))
        thread.start()
        threads = [thread]

    return '''HTML UI CODE SAME AS BEFORE'''


@app.route('/stop', methods=['POST'])
def stop():
    global threads
    if any(thread.is_alive() for thread in threads):
        stop_event.set()
        return "🛑 Sending stopped!", 200
    return "⚠️ No active sending process!", 200
