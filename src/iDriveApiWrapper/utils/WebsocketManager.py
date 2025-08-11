import asyncio
import json
import logging
import threading

import websockets
from typing import Callable, List, Any

from websockets import WebSocketException

from ..Config import APIConfig
from ..Constants import BASE_WSS
from ..exceptions import ForcedLogoutException
from ..models.Enums import EventType
from ..models.WebsocketEvent import WebsocketEvent

logger = logging.getLogger("iDrive")


class WebsocketManager:
    def __init__(self):
        self._ws_thread = None
        self._stop_ws = threading.Event()
        self._callbacks: List[Callable[[Any], None]] = []

    async def _listen_websocket(self) -> None:
        while not self._stop_ws.is_set():
            try:
                async with websockets.connect(BASE_WSS, additional_headers={"Authorization": f"Bearer {APIConfig.token}"}) as ws:
                    logger.info("Websocket connection established!")
                    async for message in ws:
                        self._handle_ws_event(json.loads(message))
            except WebSocketException as e:
                logger.warning(f"⚠️ WebSocket error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    def register_callback(self, callback: Callable[[dict], None]) -> None:
        self._callbacks.append(callback)

    def _dispatch_event(self, event: WebsocketEvent) -> None:
        def run_callback(cb):
            def wrapper():
                cb(event)
            thread = threading.Thread(target=wrapper, daemon=True)
            thread.start()

        for callback in self._callbacks:
            run_callback(callback)

    def _handle_force_logout(self, event: WebsocketEvent):
        if not event.is_encrypted and event.type == EventType.FORCE_LOGOUT:
            self.stop_websocket()
            raise ForcedLogoutException("Forced logout, please re login.")

    def _handle_ws_event(self, data: dict) -> None:
        try:
            event = WebsocketEvent(data)
            self._handle_force_logout(event)
            self._dispatch_event(event)
        except Exception as e:
            logger.exception(f" Error happened during handling of a websocket event\nError: {e}")

    def _run_ws_loop(self) -> None:
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._listen_websocket())

    def start_websocket(self) -> None:
        if self.is_running():
            return
        self._stop_ws.clear()
        self._ws_thread = threading.Thread(target=self._run_ws_loop, daemon=True)
        self._ws_thread.start()

    def run_forever(self):
        self._ws_thread.join()

    def stop_websocket(self) -> None:
        self._stop_ws.set()

    def is_running(self) -> bool:
        return self._ws_thread and self._ws_thread.is_alive()
