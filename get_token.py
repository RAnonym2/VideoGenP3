from logic_youtube import get_authenticated_service

if __name__ == "__main__":
    print("--- 1. LÉPÉS: Böngésző indítása ---")
    print("Kérlek jelentkezz be azzal a Google fiókkal, ahol a csatorna van!")
    
    # Ez a függvény (amit már megírtunk a logic_youtube-ban) végzi a varázslatot
    get_authenticated_service()
    
    print("\n✅ SIKER! A 'token.pickle' fájl létrejött a mappában.")
    print("Most már törölheted ezt a 'get_token.py' fájlt.")