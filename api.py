from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import discord
import json
import asyncio
import io
import requests
from config import API_SECRET
from database import *

app = Flask(__name__)
CORS(app)
bot_instance = None

def set_bot_instance(bot):
    global bot_instance
    bot_instance = bot

@app.route('/')
def index():
    return render_template('admin.html')

@app.route('/api/channels', methods=['GET'])
def api_get_channels():
    return jsonify(get_all_channels())

@app.route('/api/channels/<channel_id>', methods=['PUT'])
def api_update_channel(channel_id):
    data = request.json
    set_channel_permission(channel_id, data.get('channel_name', ''), data)
    return jsonify({"success": True})

@app.route('/api/send', methods=['POST'])
def api_send():
    if request.headers.get('X-API-Key') != API_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    channel_id = data.get('channel_id')
    content = data.get('content', '')
    embed_data = data.get('embed', {})
    file_url = data.get('file_url', '')
    
    perm = get_channel_permission(channel_id)
    if not perm or not perm['can_send']:
        return jsonify({"error": "No permission"}), 403
    if not bot_instance:
        return jsonify({"error": "Bot offline"}), 500
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        channel = bot_instance.get_channel(int(channel_id))
        if not channel:
            return jsonify({"error": "Channel not found"}), 404
        
        file_obj = None
        if file_url and perm.get('can_attach', 1):
            try:
                r = requests.get(file_url, timeout=10)
                if r.status_code == 200:
                    fname = file_url.split('/')[-1].split('?')[0] or 'file.bin'
                    file_obj = discord.File(io.BytesIO(r.content), filename=fname[:50])
            except: pass
        
        embed = None
        if embed_data:
            try:
                embed = discord.Embed(
                    title=embed_data.get('title'),
                    description=embed_data.get('description'),
                    color=int(embed_data.get('color', '#5865F2').replace('#',''), 16)
                )
                for f in embed_data.get('fields', []):
                    embed.add_field(name=f.get('name'), value=f.get('value'), inline=f.get('inline', False))
                if embed_data.get('image'):
                    embed.set_image(url=embed_data.get('image'))
                if embed_data.get('footer'):
                    embed.set_footer(text=embed_data.get('footer'))
            except: pass
        
        if file_obj and embed:
            msg = loop.run_until_complete(channel.send(content=content or None, embed=embed, file=file_obj))
        elif file_obj:
            msg = loop.run_until_complete(channel.send(content=content or None, file=file_obj))
        elif embed:
            msg = loop.run_until_complete(channel.send(content=content or None, embed=embed))
        else:
            msg = loop.run_until_complete(channel.send(content or "."))
        
        log_sent_message(str(msg.id), str(channel.id), content, json.dumps(embed_data), file_url)
        loop.close()
        return jsonify({"success": True, "message_id": str(msg.id), "jump_url": msg.jump_url})
    except Exception as e:
        loop.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def api_delete():
    if request.headers.get('X-API-Key') != API_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    channel_id = data.get('channel_id')
    message_id = data.get('message_id')
    perm = get_channel_permission(channel_id)
    if not perm or not perm['can_delete']:
        return jsonify({"error": "No delete permission"}), 403
    if not bot_instance:
        return jsonify({"error": "Bot offline"}), 500
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        channel = bot_instance.get_channel(int(channel_id))
        msg = loop.run_until_complete(channel.fetch_message(int(message_id)))
        loop.run_until_complete(msg.delete())
        delete_sent_message_log(message_id)
        loop.close()
        return jsonify({"success": True})
    except Exception as e:
        loop.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/pin', methods=['POST'])
def api_pin():
    if request.headers.get('X-API-Key') != API_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    channel_id = data.get('channel_id')
    message_id = data.get('message_id')
    if not bot_instance:
        return jsonify({"error": "Bot offline"}), 500
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        channel = bot_instance.get_channel(int(channel_id))
        msg = loop.run_until_complete(channel.fetch_message(int(message_id)))
        loop.run_until_complete(msg.pin())
        loop.close()
        return jsonify({"success": True})
    except Exception as e:
        loop.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/products', methods=['GET'])
def api_get_products():
    return jsonify(get_products())

@app.route('/api/products', methods=['POST'])
def api_add_product():
    if request.headers.get('X-API-Key') != API_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    add_product(data['name'], data.get('category',''), data.get('price',''), data.get('validity',''), 
                data.get('features',''), data.get('image_url',''), data.get('channel_id',''))
    return jsonify({"success": True})

@app.route('/api/products/<int:pid>', methods=['DELETE'])
def api_delete_product(pid):
    if request.headers.get('X-API-Key') != API_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    delete_product(pid)
    return jsonify({"success": True})

@app.route('/api/templates', methods=['GET'])
def api_get_templates():
    return jsonify(get_templates())

@app.route('/api/templates', methods=['POST'])
def api_save_template():
    if request.headers.get('X-API-Key') != API_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    save_template(data['name'], data['content'])
    return jsonify({"success": True})

@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    channel_id = request.args.get('channel_id')
    return jsonify(get_sent_messages(channel_id))
