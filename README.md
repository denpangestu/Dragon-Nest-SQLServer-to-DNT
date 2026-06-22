# DragonNest SQL to DNT Converter

A user-friendly Python GUI application designed to convert data from **SQL Server** back into **DragonNest (.dnt)** binary files. This tool is essential for developers and server admins who manage game data within SQL Server and need to synchronize it back to the game client or server resource files.

### 🚀 Features

* **Intuitive GUI**: Built with `tkinter` for easy interaction; no command-line hassle.
* **Windows Authentication**: Supports secure login using your current Windows credentials (no hardcoded passwords).
* **Multi-Table Selection**: Select multiple tables at once and export them in one click.
* **Progress Tracking**: Real-time progress bar and detailed log for monitoring the export process.
* **Automatic Formatting**: Handles binary structure (versions, column types, and data types) automatically based on metadata.

### 📋 Prerequisites

* **Windows OS**
* **Python 3.x**
* **ODBC Driver for SQL Server** (e.g., Driver 17 or 18)
* Required Python libraries:
```bash
pip install pyodbc tqdm

```



### 🛠 How to Setup

1. **Database Configuration**:
Open `main.py` and update the `DB_CONFIG` dictionary with your server name and database name.
```python
DB_CONFIG = {
    'server': 'YOUR_SERVER_NAME',
    'database': 'DragonNest_DNT',
    'driver': '{ODBC Driver 17 for SQL Server}'
}

```


2. **Permissions**:
Ensure your Windows account has the necessary permissions (`db_owner` or `sysadmin`) to read from the database.
3. **Run the Application**:
```bash
python sql_to_dnt_sa.py

```



### 📖 Usage

1. Open the application.
2. The app will automatically list all tables that have metadata entries.
3. **Select** the tables you wish to export from the listbox (Hold `Ctrl` for multiple selection).
4. Click **Browse** to choose the destination folder.
5. Click **"MULAI EXPORT KE DNT"** and wait for the log to show the success message.

### 🛡 License

This project is for educational purposes for the DragonNest community. Please use it responsibly.

---
