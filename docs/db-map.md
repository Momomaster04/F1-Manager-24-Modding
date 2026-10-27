# F1 Manager 24 save database map (engines and suppliers)

Mapped from one career save (`save13.sav`, game version `volta24 game 1.1`, in-game ~Aug 2025, player team Alpine).
Everything here was read-only. Unverified points are flagged **(unverified)**.

## Save file layout

```
[GVAS header]            Unreal save header (~3.4 KB)
u32 compressed_size      bytes of zlib data that follow (runs to end of file)
u32 db_size[3]           size of each SQLite database once decompressed
[zlib data]              three SQLite databases, back to back
```

- All three databases have the same 328 tables.
- **Database 1 is the live career** (latest date in `Player_State`). Databases 2 and 3 are older snapshots of the same career. The game's purpose for them is **(unverified)**.
- `tools/unpack.py` splits a save into `<name>_db1..3.sqlite`.
- `tools/repack.py` recompresses the three databases (zlib level 6) and rewrites the four u32 sizes. Repacking an untouched save gives a byte-identical file, so there's no checksum or other size field to update.

## Game tables

### `Parts_Enum_EngineManufacturers`: the supplier list

| Value | Name | TeamID (works) | Engine / ERS / Gearbox DesignID | Cost |
|---|---|---|---|---|
| 1 | Ferrari | 1 Ferrari | 1 / 2 / 3 | 23,000,000 |
| 2 | Renault | 5 Alpine | 10 / 11 / 12 | 20,000,000 |
| 3 | Honda | 3 Red Bull | 4 / 5 / 6 | 21,000,000 |
| 4 | Mercedes | 4 Mercedes | 7 / 8 / 9 | 22,000,000 |

It also has columns `StartOfSeasonUpfrontCost`, `StartOfSeasonMonthlyCost` and `StartOfSeasonMonthlyCostNumMonths` (10).
There are only four rows. Whether a fifth row works in game is **(unverified)**.

### `Parts_Designs`: one row per part design

- `PartType`: 0 Engine, 1 ERS, 2 Gearbox (from `Parts_Enum_Type`).
- DesignIDs 1–12 are the four manufacturers' **master** designs (`ValidFrom` 2022, `TeamID` = works team).
- **Customer teams have their own copies** (for example 485–487 for McLaren), created on season day 1 (`DayCreated` 45658, `ValidFrom` 2025), with stats identical to their supplier's master.
- Works teams use the master designs directly.

### `Parts_Designs_StatValues`: the stats

`(DesignID, PartStat, Value, UnitValue, DesignFocus, ExpertiseGain, ExpertiseEffect)`

Stats used by powertrain parts (`Parts_Enum_Stats`):

| PartStat | Name | Used on |
|---|---|---|
| 6 | FuelEfficiency | Engine |
| 10 | Power | Engine |
| 11 | DEPRECATED_PerformanceThreshold | Engine |
| 12 | DEPRECATED_PerformanceLoss | Engine |
| 14 | OperationalRange | Engine |
| 15 | Durability | ERS, Gearbox |

- `UnitValue` looks like the visible rating. `Value` is a 0–1000 score that follows from `UnitValue` linearly within a stat range: Power 80→0 and 100→1000, FuelEfficiency 50→0 and 100→1000. The exact ranges per stat are **(unverified)**.

Current engine ratings (`UnitValue`):

| Engine | Power | FuelEff | OpRange | Thresh* | Loss* | ERS Dur | Gearbox Dur |
|---|---|---|---|---|---|---|---|
| Ferrari | 95 | 75 | 68 | 80 | 77.5 | 50 | 57 |
| Honda | 100 | 65 | 60 | 85 | 70 | 62 | 50 |
| Mercedes | 90 | 50 | 80 | 65 | 82.75 | 70 | 70 |
| Renault | 80 | 100 | 73 | 75 | 85 | 75 | 100 |

\* deprecated stats. Whether the game still reads them is **(unverified)**.

### `Parts_TeamHistory`: which supplier each team has

`(SeasonID, TeamID, EngineManufacturer)`, one row per team per season from 2021 (custom team from 2022).

### Related tables

- `Parts_EnginePurchase_MonthlyPayments` `(TeamID, EngineManufacturerID, MonthsLeft)`: what customers still owe. It matches `Parts_TeamHistory` for 2025.
- `Player_PreSeason.SelectedEngineManufacturer`: the player's pick in pre-season (2 = Renault).
- `Player.TeamID`: the player's team (5 = Alpine).
- `Parts_PowertrainRaceHistoryData`: engine, ERS and gearbox parts used per race.

## DB Editor tables (third party, not read by the game)

Added by the f1dbeditor.com tool. The game itself doesn't appear to use them.

| Table | Contents |
|---|---|
| `Custom_Engines_List` | editor's names, keyed by engine DesignID (1 Ferrari, 4 "Red Bull", 7 Mercedes, 10 Renault) |
| `Custom_Engines_Stats` | copy of the master stats `(engineId, designId, partStat, unitValue, Value)`. Ferrari's ERS and gearbox durability are swapped compared with the game |
| `Custom_Engine_Allocations` | `(teamId, engineId)`: the supplier the editor wants for each team |
| `Custom_Engine_Progression` | empty. Meant for per-race power tracking |
| `Custom_Engine_Regulation_State` | `lastSeasonApplied` = 2025 |

## Finding: the cars don't match the game's supplier record

For five teams, the engine copy on the car matches the editor's allocation, not the game's own 2025 record:

| Team | `Parts_TeamHistory` 2025 | Stats on the car / editor allocation |
|---|---|---|
| McLaren | Renault | Mercedes |
| Williams | Renault | Mercedes |
| Alfa Romeo | Mercedes | Ferrari |
| Aston Martin | Honda | Mercedes |
| Custom team | Honda | Ferrari |

The same is true in all three snapshots.

**Hypothesis (unverified):** at season rollover the game rebuilds each customer's design copy from its own supplier record and master stats, which discards the editor's changes.

**Implication for the mod:** write to the game's own tables (supplier record, master designs, every customer copy) and re-apply after every season change, instead of relying on side tables.

## Open questions

- Confirm the rollover behaviour by comparing a save from just before and just after a season change.
- Does editing `UnitValue` alone work, or must `Value` be kept in sync?
- Does a fifth manufacturer row work, or must an existing slot be reused?
- Should repacking change only database 1, or all three?
