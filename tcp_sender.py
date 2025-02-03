import asyncio
import json

class TCPSender:
    def __init__(self, host: str, port: int, callback):
        self.host = host
        self.port = port
        self.callback = callback
        self.reader = None
        self.writer = None
        self.connected = False
        self.connection_lock = asyncio.Lock()

    async def connect(self):
        async with self.connection_lock:
            if self.connected:
                return
            for i in range(1, 20):
                try:
                    self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
                    self.connected = True
                    print(f"Connected to VRCFT at {self.host}:{self.port}")
                    return
                except (ConnectionRefusedError, OSError) as e:
                    print(f"Connection attempt {i} failed. Retrying in {5*i} seconds...")
                    await asyncio.sleep(5 * i)
            print("Failed to connect after multiple attempts.")
            self.callback()

    async def send(self, data):
        if not self.connected:
            await self.connect()
            if not self.connected:
                return False
        try:
            self.writer.write(data)
            await self.writer.drain()
            return True
        except Exception as e:
            print(f"Error sending data: {e}")
            self.connected = False
            try:
                await self.connect()
                if self.connected:
                    self.writer.write(data)
                    await self.writer.drain()
                    return True
            except Exception as e:
                print(f"Reconnection failed: {e}")
                self.callback()
                return False

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()