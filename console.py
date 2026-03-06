#!/usr/bin/env python3
"""
Consola local - Aly Apapachar
Para testing sin WhatsApp/Twilio.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(current_dir, '.env'))

from orchestrator import ApapacharOrchestrator


def main():
    print("=" * 60)
    print("🤖 ALY APAPACHAR - Consola Local")
    print("   Manual A+P (ICBF) - Equimundo")
    print("=" * 60)
    print("Escribe 'salir' para terminar.\n")

    try:
        orc = ApapacharOrchestrator()
    except Exception as e:
        print(f"❌ Error inicializando: {e}")
        return

    while True:
        try:
            user_input = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 ¡Hasta luego!")
            break

        if not user_input:
            continue
        if user_input.lower() in ('salir', 'exit', 'quit'):
            print("👋 ¡Hasta luego!")
            break

        result = orc.process_query(user_input)

        print(f"\n[{result.get('intent','?')} | {result.get('language','?')}]")
        print(f"Aly: {result['answer']}")

        if result.get('sources'):
            print(f"\n📚 Fuentes: {len(result['sources'])} chunk(s) del Manual A+P")

        print()


if __name__ == "__main__":
    main()
