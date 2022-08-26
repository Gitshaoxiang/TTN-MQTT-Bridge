# python 3.6

import random
import time
from tkinter.tix import Tree

from paho.mqtt import client as mqtt_client
import json

emqx_client_handle = None
ttn_client_handle = None

emqx_client_config = {
    'broker': 'broker.emqx.io',
    'port': 1883,
    'user': "xxxxxxxxxxx",
    'password': "xxxxxxxxxxx",
    'client_id': f'python-mqtt-{random.randint(0, 1000)}'
}

ttn_client_config = {
    'broker': 'eu1.cloud.thethings.network',
    'port': 1883,
    'user': "xxxxxxxxxxx",
    'password': "xxxxxxxxxxx",
    'client_id': f'python-mqtt-{random.randint(0, 1000)}'
}


def create_mqtt_connect(client_config):
    def on_connect(client, userdata, flags, rc):
        print('---------- '+client_config['broker']+' ----------')
        if rc == 0:
            print("Connected!")
        else:
            print("Failed to connect, return code %d\n", rc)
    client = mqtt_client.Client(client_config['client_id'])
    client.on_connect = on_connect
    client.username_pw_set(client_config['user'], client_config['password'])
    client.connect(client_config['broker'], client_config['port'])
    return client


def subscribe(client_handle, topic, callback):
    client_handle.subscribe(topic)
    client_handle.on_message = callback


def publish(client_handle, topic, payload):
    result = client_handle.publish(topic, payload, 2)
    status = result[0]
    if status == 0:
        print("Send OK")
    else:
        print("Send Failed")

def emqx_message_handler(client, userdata, msg):
    global ttn_client_handle
    global emqx_client_handle
    print(msg)
    print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
    try:
        data = json.loads(msg.payload.decode())
        device_id = data['device_id']
        led_status = data['led_status']
        topic = 'v3/000000000000@ttn/devices/' + device_id + '/down/push'
        payload = {
            "downlinks": [
                {
                    "f_port": 15,
                    "frm_payload": led_status,
                    "priority": "NORMAL",
                    "confirmed": True
                }
            ]
        }
        publish(ttn_client_handle, topic, json.dumps(payload))
    except:
        pass

def ttn_message_handler(client, userdata, msg):
    global ttn_client_handle
    global emqx_client_handle
    print(msg)
    print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
    try:
        data = json.loads(msg.payload.decode())
        device_id = data['end_device_ids']['device_id']
        env_status = data['uplink_message']['frm_payload']
        topic = 'v3/web/lorawan/up'
        payload = {
            "env": env_status,
            "device_id": device_id
        }
        publish(emqx_client_handle, topic, json.dumps(payload))
    except:
        pass


def run():
    global emqx_client_handle
    global ttn_client_handle

    emqx_client_handle = create_mqtt_connect(emqx_client_config)
    ttn_client_handle = create_mqtt_connect(ttn_client_config)

    emqx_client_handle.loop_start()
    ttn_client_handle.loop_start()

    subscribe(emqx_client_handle,
        "v3/web/lorawan/down"
    , emqx_message_handler)
    subscribe(
        ttn_client_handle,
        "v3/000000000000@ttn/devices/#",
        ttn_message_handler
    )

    while 1:
        pass

if __name__ == '__main__':
    run()
