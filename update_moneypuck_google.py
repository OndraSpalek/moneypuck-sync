import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Oprávnění pro správu souborů na disku
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# ID cílové složky 'moneypuck' na Google Disku
FOLDER_ID = '1SpmP3HK5tsJAw0eUvSqj4rM-bzBwmca6'

def get_drive_service():
    creds = None
    # Token uložíme lokálně, aby se skript příště neptal
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Pokud token neexistuje nebo je neplatný/vypršelý
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Obnovení tokenu selhalo: {e}. Spouštím novou autorizaci...")
                creds = None
        
        if not creds:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("Chybí soubor 'credentials.json' z Google Cloud Console!")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # prompt='consent' a access_type='offline' zajistí trvalý refresh_token
            creds = flow.run_local_server(port=0, prompt='consent', access_type='offline')
            
        # Uložení tokenu pro příští spuštění
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def upload_to_drive():
    service = get_drive_service()
    
    file_name = 'report_google.xlsx'
    if not os.path.exists(file_name):
        print(f"Chyba: Soubor {file_name} nebyl nalezen k nahrání!")
        return

    # 1. Hledání a mazání starého souboru ve složce 'moneypuck'
    print("Kontroluji staré verze souboru ve složce...")
    query = f"'{FOLDER_ID}' in parents and name = '{file_name}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    for item in items:
        file_id_to_delete = item['id']
        print(f"Mazání starého souboru (ID: {file_id_to_delete})...")
        service.files().delete(fileId=file_id_to_delete).execute()

    # 2. Nahrání nového souboru
    file_metadata = {
        'name': file_name,
        'parents': [FOLDER_ID]
    }
    
    media = MediaFileUpload(file_name, resumable=True)

    print("Nahrávám nový soubor do složky moneypuck na Google Disk...")
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    print(f"Úspěšně nahráno do složky moneypuck! ID nového souboru: {file.get('id')}")

if __name__ == '__main__':
    upload_to_drive()
