# Hasty Paste
![GitHub](https://img.shields.io/github/license/enchant97/hasty-paste?style=flat-square)
![Supported Python Version](https://img.shields.io/badge/python%20version-3.10-blue?style=flat-square)
![Lines of code](https://img.shields.io/tokei/lines/github/enchant97/hasty-paste?style=flat-square)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/enchant97/hasty-paste?style=flat-square)
![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/enchant97/hasty-paste?include_prereleases&label=latest%20release&style=flat-square)

A fast and minimal paste bin, written in Python using Quart.

> **IMPORTANT NOTICE** Some deprecated features will be removed in V1.7, view [here](https://github.com/enchant97/hasty-paste/issues/50)

## Features
- Quickly paste and save, to share some text
- Publicly accessible, no auth needed
- Randomly generated id's, optional "long" id to reduce brute force attacks
- Add expiring pastes
- Dark theme
- Optional syntax highlighting
- No JavaScript needed
- Uses minimal resources
- REST API
- No Database needed, everything stored as flat-files
- Lightweight Docker image (uses Alpine Linux)

## Showcase
[![Showcase Image](docs/assets/showcase.png)](docs/assets/showcase.png)

## Docs
Docs are located in the [/docs](docs/index.md) directory.

## Branches
| Name         | Description            | State         |
| :----------- | :--------------------- | :------------ |
| main         | Work ready for release | Stable        |
| next         | Work for next version  | Very Unstable |
| historical-X | Historical versions    | Unsupported   |

> Choose a tag/release for most stable if running project

## Why Is It Called "Hasty Paste"?
The name was chosen not because the project is written badly, but because you use it so fast without a care in the world and "Fast Paste" was already taken!

## License
This project is Copyright (c) 2022 Leo Spratt, licences shown below:

Code

    AGPL-3 or any later version. Full license found in `LICENSE.txt`

Documentation

    FDLv1.3 or any later version. Full license found in `docs/LICENSE.txt`
