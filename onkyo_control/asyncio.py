from serial_protocol.asyncio import AsyncIOEventMachineProtocol

from .commands import get_event_for


protocol_factory = AsyncIOEventMachineProtocol.factory(get_event_for, b'\x1a')
