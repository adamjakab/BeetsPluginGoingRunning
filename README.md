[![Build Status](https://travis-ci.org/adamjakab/BeetsPluginGoingRunning.svg?branch=master)](https://travis-ci.org/adamjakab/BeetsPluginGoingRunning)
[![Coverage Status](https://coveralls.io/repos/github/adamjakab/BeetsPluginGoingRunning/badge.svg?branch=master)](https://coveralls.io/github/adamjakab/BeetsPluginGoingRunning?branch=master)

# Going Running (beets plugin)

*A [beets](https://github.com/beetbox/beets) plugin for insane obsessive-compulsive music geeks.*

The *beets-goingrunning* plugin is for runners. It lets you configure different training activities by filtering 
songs based on their speed(bpm) and duration and attempts to create a list of songs for that training.

## Introduction

I in advance apologize for the following guide. I promise I will explain things a bit better at some point. Until then if something is not clear please use the Issue tracker.

## Installation
The plugin can be installed via:

```shell script
$ pip install beets-goingrunning
```

Activate the plugin in your configuration file:

```yaml
plugins:
    - goingrunning
    # [...]
```

Check if plugin is loaded with `beet version`. It should list 'bpmanalyser' amongst the loaded plugins.


## Usage

Invoke the plugin as:

    $ beet goingrunning training_name [-lcq] [QUERY...]
    
There are the following switches available:

- --list [-l]: List all the configured trainings with their attributes. With this switch you do not enter the name of the training, just `beet goingrunning --list`
- --count [-c]: Count the number of songs available for a specific training. With `beet goingrunning longrun --count` you can see how many of your songs there are in your library that fit your specs.
- --quiet [-q]: Do not display any output from the command.


## Configuration

Your default configuration is:
```yaml
goingrunning:
    song_bpm: [90, 150]
    song_len: [90, 240]
    duration: 60
    targets: {}
    target: no
    clean_target: no
```

There are two concepts you need to know to configure the plugin: targets and trainings:

- Targets are named destinations on your file system to which you will be copying your songs. The `targets` key allows you to define multiple targets whilst the `target` key allows you to specify the name of your default player to which the plugin will always copy your songs (if not otherwise specified).

```yaml
goingrunning:
    # [...]
    targets:
        my_player_1: /mnt/player_1
        my_other_player: /media/player_2
    target: my_player_1
    # [...]
```

- Trainings are not much more than named queries (for now - but I have some really cool plans) into your library. They
have two attributes by which the plugin will decide which songs to chose (`song_bpm` and `song_len`) and a `duration` 
element (expressed in minutes) for deciding how many songs to select. The `song_bpm` and `song_len` attributes have two numbers which indicate the lower and the higher limit of that attribute.

A common configuration section will look something like this:

```yaml
goingrunning:
    # [...]
    clean_target: no
    targets:
        my_player_1: /mnt/player_1
        my_other_player: /media/player_2
    target: my_player_1
    trainings:
        longrun: 
            song_bpm: [120, 150]
            song_len: [120, 600]
            duration: 90
        10K: 
            song_bpm: [150, 180]
            song_len: [120, 240]
            duration: 90
            target: my_other_player
            clean_target: yes
    # [...]
```

Once you have created your trainings you will just attach your player to your pc and launch:

    $ beet goingrunning 10K
    
and you will always have your music with you that matches your training.

All the configuration options are looked up in the entire configuration tree. This means that whilst the songs for the the `10K` training will be copied to the `my_other_player` target, the `longrun` training (which does not declare this attribute), will use that on the root level: `my_player_1`. This holds for all attributes.

The `clean_target` attribute, when set to `yes` will ensure that all songs are removed from the target before copying the new songs.

    
### Examples:

Show all the configured trainings:

    $ beet goingrunning --list
    
Copy your songs to your target based on the `longrun` training:

    $ beet goingrunning longrun
    
Do the same as above but today you feel reggae:

    $ beet goingrunning longrun genre:Reggae


### Final Remarks:

- give feedback
- contribute
- enjoy!
