# CHANGELOG


## v1.2.2

### New features:
- multiple trainings/playlists on MPD device using 'clean_target: training'
- songs on device are now stored on separate folders for each training

### Fixes
- ordering on fallback training is now honoured
- some minor ordering/song picking fixes


## v1.2.1

### New features:
- creating playlists on target
- possibility to disable song copy (playlist only)
- negated lists can also be used
- fields in queries can now be used as lists
- fields in different flavours now expand the selection (instead of substitution)
- maximize unheard song proposal by incrementing play_count on export

### Fixes
- multiple logging issues



## v1.2.0

### New features:
- introduced `play_count` handling and `favour_unplayed` based song selection

### Fixes
- multiple lines in logging
- trainings without target



## v1.1.2

### New features:
- introduced flavour based song selection
- improved library item fetching and filtering - support for numeric flex attributes (such as mood_happy) 
- added special "fallback" training
- added file check for stale library items 
- advanced ordering based on multi-item scoring system

### Fixes
- temporary fix for incompatibility issue with other plugins declaring the same types (Issue #15)
- now removing .m3u playlist files from device on cleanup
- removed confusing "bubble up" concept from config/code



## v1.1.1

**Special note**: Deleted right after its release due to an incompatibility issue with some core plugins.



## v1.1.0

### New features:
- Queries are now compatible with command line queries (and can be overwritten)
- Ordering is now possible on numeric fields
- Cleaning of target device from extra files
- Implemented --dry-run option to show what would be done without execution

### Fixes
