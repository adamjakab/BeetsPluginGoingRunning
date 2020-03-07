# TODOS (ROADMAP)
This is a list of things that will be implemented at some point.

## Short term implementations 

- stats - show statistics about the library - such as number of songs without bpm information
- training info: show total listening time for a specific training
- targets - target definition should include some extra info - just some ideas:
```yaml
goingrunning:
    # [...]
    targets:
        -
            name: SONY-1
            device_path: /media/player_2
            subfolder: MUSIC/AUTO
            create_training_folder: yes
            clean_destination: yes
            create_playlist: yes
            delete_extra_files:
              - STDBDATA.DAT
    # [...]
```
- generate playlist


## Long term implementations 

- maximize unheard song proposal(optional) by:
    - incrementing listen count on export
    - adding it to the query and proposing songs with lower counts
- enable song merging and exporting all songs merged into one single file (optional)
- possibility to handle sections inside a training (for interval trainings / strides at different speeds)
    - sections can also be repeated
- enable audio TTS files to give instructions during training: "Run for 10K at 4:45. RUN!" exporting it as mp3 files and adding it into the song list.
