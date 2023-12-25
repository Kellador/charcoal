from __future__ import annotations  # PEP563

import asyncio
import logging
import random
import struct

log = logging.getLogger(f'spiffy-mc.{__name__}')


LOGIN = 3
COMMAND = 2
RESPONSE = 0
AUTH_FAIL = -1


class RCONPacket:
    def __init__(self, payload: str, r_type: int = COMMAND, r_id: int | None = None):
        self.payload = payload
        self.r_type = r_type
        if r_id is None:
            self.r_id = random.randint(16, 214742069)
        else:
            self.r_id = r_id

    def encode(self) -> bytes:
        _r_id = struct.pack('<i', self.r_id)
        _type = struct.pack('<i', self.r_type)
        _payload = self.payload.encode('utf8')
        _pad = b'\x00\x00'

        data = _r_id + _type + _payload + _pad

        return struct.pack('<i', len(data)) + data

    @classmethod
    def decode(cls, data: bytes) -> RCONPacket:
        _r_id = struct.unpack('<i', data[:4])[0]
        _type = struct.unpack('<i', data[4:8])[0]

        if _r_id == AUTH_FAIL:
            raise AuthFailure

        _payload = data[8:-2].decode('utf8')

        return cls(_payload, _type, _r_id)


async def establish_connection(server: str) -> bool:
        rcon_info = await self._get_rcon_info(server)
        if rcon_info is None:
            return False

        login_packet = RCONPacket(payload=rcon_info['rcon.password'], r_type=LOGIN)

        reader, writer = await asyncio.open_connection(
            host='127.0.0.1', port=rcon_info['rcon.port']
        )

        writer.write(login_packet.encode())
        await writer.drain()

        response_length = struct.unpack('<i', (await reader.read(4)))[0]

        try:
            data = await reader.readexactly(response_length)
        except asyncio.IncompleteReadError:
            log.warning(f'{server} RCON: recieved incomplete login response!')
            raise RconAuthFailure(server, 'incomplete login response')

        try:
            response = RCONPacket.decode(data)
        except AuthFailure:
            log.warning(f'{server} RCON: auth failure')
            raise RconAuthFailure(server, 'authentication rejected')
        else:
            ack = response.r_id == login_packet.r_id
            if ack:
                if server in self.connections:
                    old_con = self.connections[server][1]
                    old_con.close()
                    await old_con.wait_closed()

                self.connections[server] = (reader, writer)
            return ack

async def send_command(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, command: str
) -> str | None:
    command_packet = RCONPacket(payload=command)

    writer.write(command_packet.encode())
    await writer.drain()

    response_length = struct.unpack('<i', (await reader.read(4)))[0]

    try:
        data = await reader.readexactly(response_length)
    except asyncio.IncompleteReadError as part:
        log.warning('RCON: recieved incomplete command response')
        log.warning('This shouldn\'t happen, I think?')
        return None

    try:
        response = RCONPacket.decode(data)
    except AuthFailure:
        raise

    ack = response.r_id == command_packet.r_id
    if ack and response.r_type == RESPONSE:
        return response.payload
    else:
        return None