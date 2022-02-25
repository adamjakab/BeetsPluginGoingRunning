# TODOS (ROADMAP)

This is an ever-growing list of ideas that will be scheduled for implementation at some point.


## Short term implementations 
These should be easily implemented.

- allow passing `flavour` names on command line
- training info: show full info for a specific training:
    - total time
    - number of bins
    - ...
- targets - target definition should include some extra info - just some ideas:
```yaml
goingrunning:
    targets:
      SONY-1:
        create_training_folder: yes
```


## Long term implementations 
These need some proper planning.

- **possibility to handle multiple sections** inside a training (for interval trainings / strides at different speeds)
    - sections can also be repeated

example of an interval training with 5 minutes fast and 2.5 minutes recovery repeated 5 times:    
```yaml
goingrunning:
    trainings:
      STRIDES-1K:
        use_sections: [fast, recovery]
        repeat_sections: 5
        sections:
          fast:
            use_flavours: [energy, above170]
            duration: 300
          recovery:
            use_flavours: [chillout, sunshine]
            duration: 150
```    

- enable song merging and exporting all songs merged into one single file (optional)
- enable audio TTS files to give instructions during training: "Run for 10K at 4:45. RUN!" exporting it as mp3 files and adding it into the song list.


## Will not implement
These ideas are kept because they might be valuable for some future development but they will not part of the present plugin

- stats - show statistics about the library - such as number of songs without bpm information