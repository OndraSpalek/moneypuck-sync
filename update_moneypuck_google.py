import pandas as pd
import requests
import io

def generate_report():
    print("Stahuji data z MoneyPucku...")
    
    # Příklad stahování dat z MoneyPucku (upravte si URL/logiku podle toho, jak stahujete data vy)
    # Příklad pro stahování aktuálních hokejových statistik:
    url = "https://moneypuck.com/moneypuck/playerData/downloads/SKATER_table.csv"
    
    response = requests.get(url)
    if response.status_code == 200:
        # Zpracování přes pandas
        df = pd.read_csv(io.StringIO(response.text))
        
        # Zde proveďte své úpravy dat (filtrování na aktuální sezónu 2026 atd.)
        # ...
        
        # Uložení jako lokální Excel soubor do kořene repozitáře
        output_file = "report_google.xlsx"
        df.to_excel(output_file, index=False)
        print(f"Soubor {output_file} byl úspěšně vygenerován a uložen.")
    else:
        print(f"Chyba při stahování dat z MoneyPucku: {response.status_code}")
        exit(1)

if __name__ == '__main__':
    generate_report()
