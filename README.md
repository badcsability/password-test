# Password Test

A small local CLI password manager that stores credentials in JSON with encrypted usernames and passwords.

## Features

- Encrypts credential fields using `cryptography.fernet` via `KeyManager`.
- Organizes entries by service (for example: `gmail`, `github`, `bank`).
- Supports adding, listing, retrieving, and removing credentials.
- Copies retrieved passwords to clipboard with `pyperclip`.
- Persists data to disk in a JSON file referenced by environment configuration.

## Project Files

- `pw_manager.py`: CLI entrypoint and command handling.
- `pw_class.py`: Data model (`pw`, `loginList`, `pwStruct`) and JSON serialization logic.
- `key_manager.py`: Encryption key bootstrap and encrypt/decrypt helpers.
- `pwlist.json`: Example password-store format.
- `makefile`: Builds executable script `pmanage` from `pw_manager.py`.

## Requirements

- Python 3.10+ (uses `match` statement).
- Python packages:
  - `cryptography`
  - `python-dotenv`
  - `pyperclip`

Install dependencies:

```bash
pip install cryptography python-dotenv pyperclip
```

## Environment Setup

Create a `.env` file in the project root with:

```dotenv
PWD_FILE=pwlist.json
```

Notes:

- `PWD_FILE` is required. It points to your JSON password store.
- `ENCRYPTION_KEY` is created automatically by running `init` the first time.

## Usage

Run the CLI directly:

```bash
python3 pw_manager.py <command>
```

Or build executable:

```bash
make
./pmanage <command>
```

Available commands:

- `init`: Create key/file if missing, or validate/load existing store.
- `add`: Add a login (service, username, password, optional URL).
- `get`: Retrieve logins for a service; copies selected password to clipboard.
- `remove`: Remove one login or all logins for a service.
- `show`: Show all services and usernames.
- `clear`: Delete all stored credentials and remove the JSON file.
- `help`: Print command descriptions.
- `change`: Reserved/placeholder command (not implemented yet).

## Typical Workflow

1. Configure `.env` with `PWD_FILE`.
2. Run `python3 pw_manager.py init`.
3. Add credentials with `python3 pw_manager.py add`.
4. Retrieve credentials with `python3 pw_manager.py get`.
5. Remove stale entries with `python3 pw_manager.py remove`.

## Data Model and Storage Format

`pwStruct` stores all credentials in this top-level JSON shape:

```json
{
  "pass-list": {
    "service-name": {
      "site-name": "service-name",
      "logins": [
        {
          "service": "service-name",
          "user": "<encrypted>",
          "pwd": "<encrypted>",
          "url": "https://example.com",
          "created_at": 0.0,
          "last_accessed": 0.0
        }
      ]
    }
  },
  "meta": {
    "created_at": 0.0,
    "last_modified": 0.0
  }
}
```

- `user` and `pwd` are encrypted ciphertext strings.
- Timestamps are stored as Unix epoch seconds (UTC).

## Security Notes

- Encryption key is loaded from `.env` (`ENCRYPTION_KEY`).
- If `.env` is lost but JSON remains, encrypted credentials cannot be decrypted.
- Do not commit `.env` or production password-store files to version control.

## Known Limitations

- No master password flow or key-rotation support.
- `change` command is currently a stub.
- Clipboard-based retrieval can expose passwords to other local apps.
