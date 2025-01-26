from flask import Flask, request, Response, stream_with_context
import requests
import json
import uuid
import time
import os

app = Flask(__name__)

def get_token():
    try:
        uuid_val = os.getenv('UUID')
        if not uuid_val:
            uuid_val = str(uuid.uuid4())
        print(f"Using UUID: {uuid_val}")
        
        response = requests.post(
            'https://getmerlin-main-server.vercel.app/generate',
            json={'uuid': uuid_val},
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Token Response Status: {response.status_code}")
        print(f"Token Response Text: {response.text}")
        
        if response.status_code == 200:
            return response.json()['idToken']
        return None
    except Exception as e:
        print(f"Error getting token: {str(e)}")
        return None

def create_merlin_request(openai_req):
    messages = openai_req['messages']
    context_messages = [
        f"{msg['role']}: {msg['content']}" 
        for msg in messages[:-1]
    ]
    
    return {
        "attachments": [],
        "chatId": str(uuid.uuid1()),
        "language": "AUTO",
        "message": {
            "content": messages[-1]['content'],
            "context": "\n".join(context_messages),
            "childId": str(uuid.uuid4()),
            "id": str(uuid.uuid4()),
            "parentId": "root"
        },
        "mode": "UNIFIED_CHAT",
        "model": openai_req.get('model', 'claude-3-haiku'),
        "metadata": {
            "largeContext": False,
            "merlinMagic": False,
            "proFinderMode": False,
            "webAccess": False
        }
    }

def process_merlin_response(response_text):
    try:
        merlin_resp = json.loads(response_text[6:]) 
        content = merlin_resp['data']['content']
        if isinstance(content, str):
            print(f"Original content: {content}")
            content = content.encode('latin1').decode('utf-8')
            print(f"Decoded content: {content}")
            return content
        return content
    except:
        return ""

def process_non_stream_response(response):
    try:
        full_content = ""
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                content = process_merlin_response(line)
                if content and content != " ":
                    full_content += content
        
        if not full_content:
            return Response("Empty response from server", status=500)
        
        return {
            "id": str(uuid.uuid4()),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "claude-3-haiku",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": full_content
                },
                "finish_reason": "stop",
                "index": 0
            }]
        }
    except Exception as e:
        print(f"Error processing response: {str(e)}")
        return Response("Failed to process response", status=500)

@app.route('/', methods=['GET'])
def home():
    return {"status": "GetMerlin2Api Service Running...", "message": "MoLoveSze..."}

@app.route('/v1/chat/completions', methods=['POST'])
def chat():
    try:
        auth_token = os.getenv('AUTH_TOKEN')
        if auth_token:
            request_token = request.headers.get('Authorization', '')
            if request_token != f"Bearer {auth_token}":
                return Response("Unauthorized", status=401)

        token = get_token()
        if not token:
            return Response("Failed to get token", status=500)

        openai_req = request.json
        merlin_req = create_merlin_request(openai_req)
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {token}",
            "x-merlin-version": "web-merlin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "host": "arcane.getmerlin.in"
        }

        response = requests.post(
            "https://arcane.getmerlin.in/v1/thread/unified",
            json=merlin_req,
            headers=headers,
            stream=True
        )
        
        if response.status_code != 200:
            return Response(f"Merlin API error: {response.text}", status=response.status_code)

        if not openai_req.get('stream', False):
            return process_non_stream_response(response)

        def generate():
            try:
                buffer = ""
                for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                    if chunk:
                        buffer += chunk
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            if line.startswith('data: '):
                                try:
                                    content = process_merlin_response(line)
                                    if content:
                                        print(f"Streaming content: {content}")
                                        openai_resp = {
                                            "id": str(uuid.uuid4()),
                                            "object": "chat.completion.chunk",
                                            "created": int(time.time()),
                                            "model": openai_req.get('model', 'claude-3-haiku'),
                                            "choices": [{
                                                "delta": {
                                                    "content": content
                                                },
                                                "index": 0,
                                                "finish_reason": None
                                            }]
                                        }
                                        yield f"data: {json.dumps(openai_resp, ensure_ascii=False)}\n\n"
                                except Exception as e:
                                    print(f"Error processing chunk: {str(e)}")
                                    continue
                
                final_resp = {
                    "choices": [{
                        "delta": {"content": ""},
                        "index": 0,
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(final_resp)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                print(f"Error in generate: {str(e)}")
                return

        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream'
        )
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return Response(f"Internal server error: {str(e)}", status=500)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8802))
    app.run(host='0.0.0.0', port=port, debug=True)