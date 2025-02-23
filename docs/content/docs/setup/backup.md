---
title: 03 - Backups
---
To avoid data-loss it is important to backup your application data.

## What Do I Need To Backup?
Here's a simple list:

- Database, located at: `DB_URI`
    - If using a database server, you will need to perform a database dump.
    - If using sqlite, just copying the sqlite file (while app is shutdown) is needed.
- Paste Assets, located at: `ATTACHMENTS_PATH`
    - Copy directory (while app is shutdown)

## How Is Data Stored?
Most data is stored in the database however, paste attachments are stored on the file system in the following format:

```text
attachments/
    01953292-cfb0-7d1b-924e-de60d957ca6a.bin
    ...
```
