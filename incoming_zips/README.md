# Skin Files Directory

This directory should contain your skin ZIP files organized by champion name.

## Directory Structure

```
incoming_zips/
├── [ChampionName]/
│   ├── [SkinName1].zip
│   ├── [SkinName2].zip
│   └── ...
├── [AnotherChampion]/
│   ├── [SkinName1].zip
│   └── ...
└── ...
```

## Example

```
incoming_zips/
├── Ahri/
│   ├── KDA.zip
│   ├── Spirit Blossom.zip
│   └── Star Guardian.zip
├── Yasuo/
│   ├── High Noon.zip
│   ├── Project.zip
│   └── True Damage.zip
└── Jinx/
    ├── Firecracker.zip
    └── Star Guardian.zip
```

## Notes

- Skin ZIP files should be named to match the skin names detected by OCR
- The application will use fuzzy matching to find the best match
- Champion names should match the names used in the game
- ZIP files should contain the actual skin files ready for injection
