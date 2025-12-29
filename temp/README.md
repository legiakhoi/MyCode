# Secure Database Connection Script

This script provides a secure way to connect to a PostgreSQL database and retrieve data using pandas and SQLAlchemy.

## Features

- Secure credential management using environment variables
- Proper error handling and logging
- Connection pooling for better performance
- Modular code structure for easier maintenance
- Optional data export to Excel

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file based on the `.env.template`:
   ```bash
   cp .env.template .env
   ```

3. Edit the `.env` file with your actual database credentials:
   ```
   DB_HOST=your_database_host
   DB_PORT=your_database_port
   DB_NAME=your_database_name
   DB_USER=your_username
   DB_PASSWORD=your_password
   ```

## Usage

Run the script:
```bash
python secure_database_connection.py
```

## Security Notes

- Never commit the `.env` file to version control (it's included in `.gitignore`)
- Use strong passwords for your database credentials
- Consider using a secrets management system in production environments

## Customization

You can modify the script to:
- Change the SQL query in the `main()` function
- Enable Excel export by uncommenting the `save_to_excel(df)` line
- Adjust connection pool settings in the `.env` file
- Add additional error handling or logging as needed