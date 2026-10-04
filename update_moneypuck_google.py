import pandas as pd
import requests
import io

def update_moneypuck():
    print("Stahuji data z MoneyPucku...")
    
    # Správná adresa pro kariérní/game-by-game data
    url = "https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        content_type = response.headers.get("content-type", "").lower()
        if "html" in content_type or response.text.strip().startswith("<"):
            print("Chyba: Server vrátil HTML stránku místo CSV dat.")
            exit(1)
            
        # Načtení dat do Pandasu
        df = pd.read_csv(io.StringIO(response.text))
        
        # Uložení jako Excel soubor do kořene repozitáře
        output_file = "report_google.xlsx"
        df.to_excel(output_file, index=False)
        print(f"Soubor {output_file} byl úspěšně vygenerován (řádků: {len(df)}).")
    else:
        print(f"Chyba při stahování dat z MoneyPucku: HTTP status {response.status_code}")
        exit(1)

if __name__ == '__main__':
    update_moneypuck()
