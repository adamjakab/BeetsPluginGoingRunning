# CHANGELOG

## v1.1.3 (in development)

### New features:


### Fixes



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
