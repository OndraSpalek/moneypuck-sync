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
        
        # FILTR: Ponecháme pouze sezónu/rok 2026, abychom nepřesáhli 100 MB limit GitHubu
        if 'season' in df.columns:
            df = df[df['season'] == 2026]
            print(f"Data byla úspěšně filtrována na rok 2026. Počet řádků: {len(df)}")
        else:
            print("Varování: Sloupec 'season' nebyl v datech nalezen.")

        # Uložení jako Excel soubor do kořene repozitáře
        output_file = "report_google.xlsx"
        df.to_excel(output_file, index=False)
        print(f"Soubor {output_file} byl úspěšně vygenerován a zmenšen (řádků: {len(df)}).")
    else:
        print(f"Chyba při stahování dat z MoneyPucku: HTTP status {response.status_code}")
        exit(1)

if __name__ == '__main__':
    update_moneypuck()
