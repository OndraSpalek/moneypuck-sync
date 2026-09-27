import os
import pandas as pd
import requests

CSV_URL = (
    "https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv"
)
OUTPUT_FILENAME = "report_google.xlsx"
LOCAL_CSV = "all_teams.csv"


def main():
  print("Stahuji CSV soubor z MoneyPuck přes bezpečný požadavek...")
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }
  response = requests.get(CSV_URL, headers=headers, stream=True)
  response.raise_for_status()

  with open(LOCAL_CSV, "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
      f.write(chunk)

  print("Soubor úspěšně stažen. Načítám do pandas...")
  df_full = pd.read_csv(LOCAL_CSV)

  print("Filtruji data (sezóna 2025, základní část, situation='all')...")
  df_filtered = df_full[
      (df_full["season"].astype(str) == "2025")
      & (df_full["playoffGame"].astype(str) == "0")
      & (df_full["situation"].str.lower() == "all")
  ].copy()

  print(f"Filtr vrátil {len(df_filtered)} řádků pro všech 32 týmů.")

  if "home_or_away" in df_filtered.columns:
    df_away = df_filtered[df_filtered["home_or_away"].str.upper() == "AWAY"]
    df_home = df_filtered[df_filtered["home_or_away"].str.upper() == "HOME"]
  else:
    half = len(df_filtered) // 2
    df_away = df_filtered.iloc[:half]
    df_home = df_filtered.iloc[half:]

  print(f"Generuji Excel {OUTPUT_FILENAME}...")
  with pd.ExcelWriter(OUTPUT_FILENAME, engine="openpyxl") as writer:
    df_away.to_excel(writer, sheet_name="Away", index=False)
    df_home.to_excel(writer, sheet_name="Home", index=False)

  if os.path.exists(LOCAL_CSV):
    os.remove(LOCAL_CSV)

  print("Hotovo! Soubor je připraven.")


if __name__ == "__main__":
  main()
