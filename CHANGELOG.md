# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-04-24
### Added
- #121; ability to disable anonymous paste creation
- #122; paste size limit & ability to disable attachments
- #123; ability to change random slug length
- #124; docker health check
- #129; migrate lexer alias code to official method
### Changed
- show paste link on paste page
- bump deps
- update to go1.24

## [2.0.0] - 2025-02-27
### Added
- V2 app
### Removed
- V1 app

## [1.10.0] - 2024-02-17
### Changed
- Bump deps & migrate some code
- Use hatch for python management

## [1.9.0] - 2023-02-16
### Added
- #27; :construction: Experimental S3 storage support
- Add ability to hide ascii art boot message
### Changed
- #70; Long ID only adjustable through config value
- Bump deps

## [1.8.0] - 2022-12-21
### Added
- Ensure Redis can be reached on app launch
- Add ASCII art for launch :)
- #67; log loaded configs on launch
- #66; custom 404 page
- Support installing using pip through setuptools pyproject
- Added optional json accelerator (installed by default in Docker image)
### Changed
- #68; make Docker image rootless (increase security)
- Reduce number of final Docker image layers
- Remove ability to use "Copy Share Link" when not under secure connection
- Improved launch scripts
- Bump pip versions
### Fixed
- Fix long id

## [1.7.0] - 2022-10-30
### Added
- Show expiry on paste screen
- Configurable multi-tiered caching
- CLI can remove empty cache folders
- Strict paste id checking in URLs
- Better general exception handling
- Add human padding for paste id
- Some more unit tests
### Changed
- Major code refactoring (pastes are no longer dependant on storage types, for future s3 object support)
- Tidy REST API routes
### Fixed
- Fixed #53 Expiry set in UI always interpreted as UTC, by having a configurable timezone
### Removed
- Removed deprecated features, see #50

## [1.6.1] - 2022-10-09
### Fixed
- #51, When override lexer is given in paste url incorrectly uses cached content

## [1.6.0] - 2022-10-08
### Added
- Simple paste creation through the api
- Ability to hide version number
- Optional caching with internal or redis
### Changed
- Code refactoring
- Update requirements
- Dependency updates

## [1.5.0] - 2022-09-23
### Added
- #39, brand customisation
### Changed
- Only generate paste id's with A-Za-z0-9
- Put config into groups
- Update pip requirements
  - quart-schema to ~=0.13.0
  - pydantic[dotenv] to ~=1.10.2
  - mkdocs-material to ~=8.5.3
- Split routes into separate modules

## [1.4.0] - 2022-08-27
### Added
- #21, Experimental management CLI
### Changed
- #19, Use --link for dockerfile, improving build speed
### Fixed
- #26, Backwards compatibility for copy share link button

## [1.3.0] - 2022-08-19
### Added
- #18, add ability to clone a paste content into new paste
- #20, add optional paste title
- #22, override lexer name with `.<ext>` of paste URL
### Fixed
- Fixed not being able to select "No Highlighting" option

## [1.2.1] - 2022-08-14
### Fixed
- Fixed not being able to select "No Highlighting" option

## [1.2.0] - 2022-08-13
### Added
- #8, add filtered highlighter syntax dropdown
- #6, config option to turn index page into new paste page
### Changed
- add ability to hide long id form checkbox
- #10, centred horizontal positioned options in new paste form
- use shorter names for syntax highlighting
### Fixed
- #9, turn off auto correction features

## [1.1.0] - 2022-08-04
### Added
- Configurable default expiry for UI (disabled by default)
- Optional syntax highlighting
- Optional public list api route (disabled by default)

## [1.0.0] - 2022-07-31
### Added
- Initial release
