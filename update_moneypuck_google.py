import os
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Konfigurace
CSV_URL = (
    "https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv"
)
FOLDER_ID = "1SpmP3HK5tsJAw0eUvSqj4rM-bzBwmca6"
OUTPUT_FILENAME = "report_google.xlsx"
CREDENTIALS_FILE = "credentials.json"


def main():
  print("Stahuji kompletní CSV soubor z MoneyPuck...")
  df_full = pd.read_csv(CSV_URL)

  # Načtení SQL filtru ze souboru report.sql, pokud existuje
  sql_query = (
      "SELECT * FROM all_teams WHERE (season = 2025 OR season = '2025') AND"
      " (playoffGame = 0 OR playoffGame = '0') AND LOWER(situation) = 'all'"
  )
  if os.path.exists("report.sql"):
    with open("report.sql", "r", encoding="utf-8") as f:
      sql_query = f.read()
    print("Načten lokální soubor report.sql")

  print("Filtruji data (sezóna 2025, základní část, situation='all')...")

  # Čistý pandas filtr odpovídající vašemu SQL dotazu
  df_filtered = df_full[
      (df_full["season"].astype(str) == "2025")
      & (df_full["playoffGame"].astype(str) == "0")
      & (df_full["situation"].str.lower() == "all")
  ].copy()

  print(f"Filtr vrátil {len(df_filtered)} řádků pro všech 32 týmů.")

  # Rozdělení na Away a Home záložky
  if "home_or_away" in df_filtered.columns:
    df_away = df_filtered[df_filtered["home_or_away"].str.upper() == "AWAY"]
    df_home = df_filtered[df_filtered["home_or_away"].str.upper() == "HOME"]
  elif "isHome" in df_filtered.columns:
    df_away = df_filtered[df_filtered["isHome"] == 0]
    df_home = df_filtered[df_filtered["isHome"] == 1]
  else:
    half = len(df_filtered) // 2
    df_away = df_filtered.iloc[:half]
    df_home = df_filtered.iloc[half:]

  # Generování Excelu se dvěma listy
  print(f"Generuji Excel {OUTPUT_FILENAME}...")
  with pd.ExcelWriter(OUTPUT_FILENAME, engine="openpyxl") as writer:
    df_away.to_excel(writer, sheet_name="Away", index=False)
    df_home.to_excel(writer, sheet_name="Home", index=False)

  print("Odesílám soubor na Google Disk...")
  SCOPES = ["https://www.googleapis.com/auth/drive"]
  creds = service_account.Credentials.from_service_account_file(
      CREDENTIALS_FILE, scopes=SCOPES
  )
  service = build("drive", "v3", credentials=creds)

  # Smazání starého souboru na Disku, pokud existuje
  query = f"'{FOLDER_ID}' in parents and name='{OUTPUT_FILENAME}' and trashed=false"
  results = service.files().list(q=query, fields="files(id, name)").execute()
  for item in results.get("files", []):
    service.files().delete(fileId=item["id"]).execute()
    print(f"Starý soubor smazán z Disku.")

  # Nahrání nového souboru
  file_metadata = {"name": OUTPUT_FILENAME, "parents": [FOLDER_ID]}
  media = MediaFileUpload(
      OUTPUT_FILENAME,
      mimetype=(
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ),
      resumable=True,
  )
  file = (
      service.files()
      .create(body=file_metadata, media_body=media, fields="id")
      .execute()
  )
  print(f"Hotovo! Soubor úspěšně nahrán na Disk s ID: {file.get('id')}")


if __name__ == "__main__":
  main()