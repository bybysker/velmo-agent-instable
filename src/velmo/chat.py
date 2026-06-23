"""Boucle de chat en ligne de commande adossée au modèle Azure AI Inference."""

from __future__ import annotations

from dotenv import load_dotenv

from .agent import VelmoAgent
from .llm import get_llm


def main() -> None:
    load_dotenv()
    agent = VelmoAgent(llm=get_llm())
    print("Assistant Velmo prêt. Posez votre question (Ctrl+C pour quitter).")
    while True:
        try:                                         
            user_input = input("\nVous : ").strip()
            if not user_input:
                continue
            reply = agent.handle(user_input)
            print(f"\nVelmo : {reply.message}")
        except KeyboardInterrupt:
            print("\nÀ bientôt !")
            break


if __name__ == "__main__":
    main()
