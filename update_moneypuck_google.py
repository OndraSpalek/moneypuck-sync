import io
import os
import re
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from requests import get

# Konfigurace
CSV_URL = (
    "https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv"
)
FOLDER_ID = "1SpmP3HK5tsJAw0eUvSqj4rM-bzBwmca6"
OUTPUT_FILENAME = "report_google.xlsx"
CREDENTIALS_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def authenticate_google_drive():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def main():
    print("Stahuji kompletní CSV soubor z MoneyPuck...")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
    }

    response = get(CSV_URL, headers=headers)

    if response.status_code != 200:
        print(
            "Chyba při stahování dat. Server vrátil HTTP kód:"
            f" {response.status_code}"
        )
        return

    df_full = pd.read_csv(io.StringIO(response.text))
    print("Data byla úspěšně stažena a načtena!")

    # Načtení SQL filtru ze souboru report.sql
    sql_query = ""
    if os.path.exists("report.sql"):
        with open("report.sql", "r", encoding="utf-8") as f:
            sql_query = f.read()
        print("Načten lokální soubor report.sql")
    else:
        sql_query = (
            "SELECT * FROM all_teams WHERE season = 2026 AND playoffGame = 0"
            " AND situation = 'all'"
        )

    # Automatické detekování sezóny z report.sql
    season_match = re.search(
        r"season\s*=\s*['\"]?(\d+)['\"]?", sql_query, re.IGNORECASE
    )
    target_season = season_match.group(1) if season_match else "2026"

    print(
        f"Filtruji data pro sezónu {target_season} (základní část,"
        " situation='all')..."
    )

    # Filtr používá sezónu z vašeho SQL souboru
    df_filtered = df_full[
        (df_full["season"].astype(str) == target_season)
        & (df_full["playoffGame"].astype(str) == "0")
        & (df_full["situation"].str.lower() == "all")
    ].copy()

    print(f"Filtr vrátil {len(df_filtered)} řádků.")

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

    print("Připojuji se k Google Disku...")
    service = authenticate_google_drive()

    # Smazání starého souboru na Disku, pokud existuje
    query = f"'{FOLDER_ID}' in parents and name='{OUTPUT_FILENAME}' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    for item in results.get("files", []):
        service.files().delete(fileId=item["id"]).execute()
        print("Starý soubor smazán z Disku.")

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
