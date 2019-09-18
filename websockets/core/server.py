from aiohttp import web, WSCloseCode
from .views import *
from . import settings

import asyncio
import json
import aioredis
import logging
import random

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(process)d - %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')  # noqa
console.setFormatter(formatter)
logger.addHandler(console)

class WSApplication(web.Application):
    WS_MESSAGE_REQUIRED_KEYS = ['uuid', ]
    def __init__(self, *args, **kwargs):
        super(WSApplication, self).__init__(loop= asyncio.get_event_loop() ,*args, **kwargs)
        self.tasks = []
        self.websockets = {}
        self.logger = logger
        
        self.on_shutdown.append(self._on_shutdown_handler)
        self.loop.run_until_complete(self._setup())

    async def _setup(self):
        self.router.add_get('/ws', WebSocketView)
        self.redis_subscriber = await aioredis.create_redis(
            address=(settings.REDIS_HOST, settings.REDIS_PORT),
            loop= self.loop,
        )
        
        self.tasks.append(
            self.loop.create_task(
                self.subscribe_to_channel(settings.WORKER_RESPONSE_TOPIC)
            )
        )
    
    async def _on_shutdown_handler(self, app):
        for task in self.tasks:
            task.cancel()
            await task
        
        for ws in self.websockets:
            await ws.close(code=WSCloseCode.GOING_AWAY, message='Server shutdown')
    
        if self.redis_subscriber and not self.redis_subscriber.closed:
            self.redis_subscriber.close()
            await self.redis_subscriber.wait_closed()
    
    async def subscribe_to_channel(self, topic):
        self.logger.info('Subscribe to channel: %s', topic)
        try:
            channel, _ = await self.redis_subscriber.subscribe(topic)
            
            while await channel.wait_message():
                try:
                    raw_msg = await channel.get()
                    msg = json.loads(raw_msg.decode('utf-8'))
                    
                    #do something with ms here
                except Exception as ex:
                    self.logger.error('Exception while processing redis msg: %s', ex)
        except asyncio.CancelledError as ex:
            self.logger.error('CancelledError exception received. Unsubscribe from: %s', topic)
            await self.redis_subscriber.unsubscribe(topic)

    async def publish_message_to_worker(self, ws, msg):
        if not all(msg.get(key) for key in self.WS_MESSAGE_REQUIRED_KEYS):
            raise Exception('Missing required keys')
        
        msg_id = msg['uuid']
        publish_topic = random.choice(settings.WORKER_PROCESS_TOPICS)
        
        msg['session_data'] = self.websockets[ws]['session_data']
        self.websockets[ws]['messages_ids'].append(msg_id)
        self.logger.debug('[%s] Publish message with id \'%s\' to topic \'%s\'', id(ws), msg_id, publish_topic)
        await self.redis_publisher.publish_json(publish_topic, msg)
                
    def handle_ws_connect(self, ws, view):
        self.websockets[ws] = {
            'view': view,
            'messages_ids': [],
            'session_data': {
                'user_pk': None
            }
        }
        self.logger.debug('[%s] Websocket was added to websocket list', id(ws))

    def handle_ws_disconnect(self, ws):
        self.websockets.pop(ws, None)
        self.logger.debug('[%s] Websocket was removed from websockets list', id(ws))