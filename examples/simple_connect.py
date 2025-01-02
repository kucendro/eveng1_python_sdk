"""
Simple connection example
"""

import asyncio
from g1sdk.connector import G1Connector

async def main():
    glasses = G1Connector()
    await glasses.connect()
    # Basic connection example 