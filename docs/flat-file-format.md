# Flat File Format
This app uses a flat file system for storing pastes, allowing for easier setup and backups. If you want to export/import from other systems this section will talk about the format of this system.

The following is the structure of the pastes root folder. If you have used git before you might recognise it uses a similar format for storing objects in the objects directory.

For those that haven't seen this format before. The randomly generated id for the paste gets split, using two characters at the beginning for the folder, and the rest for the filename, this aids in adding compatibility to some filesystems.

```
pastes/
    2a/
        57b832d3f0de70
        ...
    41/
        2671634c77057d
        ...
    ...
```

Since no database is used and some extra metadata needs to be stored. The paste file's first line of the file is the metadata in JSON format, the rest of the lines after that will be the paste content. The following is an example of the metadata:

```json
{"paste_id": "562671634c70056d", "creation_dt": "2022-07-26T20:37:12.508930", "expire_dt": null}
```
