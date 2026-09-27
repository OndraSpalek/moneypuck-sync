import os
import pandas as pd
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CSV_URL = (
    "https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv"
)
FOLDER_ID = "1SpmP3HK5tsJAw0eUvSqj4rM-bzBwmca6"
OUTPUT_FILENAME = "report_google.xlsx"
LOCAL_CSV = "all_teams.csv"


def main():
  print("Stahuji CSV soubor z MoneyPuck...")
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

  df_full = pd.read_csv(LOCAL_CSV)

  # Filtr pro sezónu 2025
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

  with pd.ExcelWriter(OUTPUT_FILENAME, engine="openpyxl") as writer:
    df_away.to_excel(writer, sheet_name="Away", index=False)
    df_home.to_excel(writer, sheet_name="Home", index=False)

  print("Odesílám soubor na Google Disk pomocí OAuth tokenu...")

  # Autentizace přes proměnné prostředí z GitHub Secrets
  creds = Credentials(
      token=None,
      refresh_token=os.environ.get("GOOGLE_REFRESH_TOKEN"),
      client_id=os.environ.get("GOOGLE_CLIENT_ID"),
      client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
      token_uri="https://oauth2.googleapis.com/token",
  )

  if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())

  service = build("drive", "v3", credentials=creds)

  # Smazání starého souboru a nahrání nového
  query = f"'{FOLDER_ID}' in parents and name='{OUTPUT_FILENAME}' and trashed=false"
  results = service.files().list(q=query, fields="files(id, name)").execute()
  for item in results.get("files", []):
    service.files().delete(fileId=item["id"]).execute()

  file_metadata = {"name": OUTPUT_FILENAME, "parents": [FOLDER_ID]}
  media = MediaFileUpload(
      OUTPUT_FILENAME,
      mimetype=(
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ),
      resumable=True,
  )
  service.files().create(
      body=file_metadata, media_body=media, fields="id"
  ).execute()
  print("Hotovo! Soubor úspěšně nahrán na Disk.")

  if os.path.exists(LOCAL_CSV):
    os.remove(LOCAL_CSV)


if __name__ == "__main__":
  main()
