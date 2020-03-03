[![Build Status](https://travis-ci.org/adamjakab/BeetsPluginGoingRunning.svg?branch=master)](https://travis-ci.org/adamjakab/BeetsPluginGoingRunning)
[![Coverage Status](https://coveralls.io/repos/github/adamjakab/BeetsPluginGoingRunning/badge.svg?branch=master)](https://coveralls.io/github/adamjakab/BeetsPluginGoingRunning?branch=master)
[![PyPi](https://img.shields.io/pypi/v/beets-goingrunning.svg)](https://pypi.org/project/beets-goingrunning/)

# Going Running (beets plugin)

*A [beets](https://github.com/beetbox/beets) plugin for insane obsessive-compulsive music geeks.*

The *beets-goingrunning* plugin is for runners. It lets you configure different training activities by filtering 
songs based on their speed(bpm) and duration and attempts to create a list of songs for that training.

## Introduction

To use this plugin at its best and to benefit the most from your library, you will need to make sure that you have
bpm information on all of your songs. Since this plugin uses the bpm information to select songs, the songs with bpm=0 will be ignored (check with `beet ls bpm:0`). If you have many you should update them. There are two ways:

1) use the built-in [acousticbrainz plugin](https://beets.readthedocs.io/en/stable/plugins/acousticbrainz.html) to fetch
the bpm information for your songs. It does a lot for well know songs but my library was still 30% uncovered after a full scan

2) Use the [bpmanalyser plugin](https://github.com/adamjakab/BeetsPluginBpmAnalyser). This will scan your songs and calculate
the tempo (bpm) value for them. If you have a big collection it might take a while, but you can potentially end up with 
100% coverage.

The following explains how to use the *beets-goingrunning* plugin. If something is not clear please use the Issue tracker. Also, if there is a feature not present, please check the [roadmap](./ROADMAP.md) document to check if it is planned. If not, create a feature request in the Issue tracker. 


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

Check if plugin is loaded with `beet version`. It should list 'goingrunning' amongst the loaded plugins.


## Usage

Invoke the plugin as:

    $ beet goingrunning training_name [-lcq] [QUERY...]
    
The following switches are available:

**--list [-l]**: List all the configured trainings with their attributes. With this switch you do not enter the name of the training, just `beet goingrunning --list`

**--count [-c]**: Count the number of songs available for a specific training. With `beet goingrunning longrun --count` you can see how many of your songs there are in your library that fit your specs.

**--quiet [-q]**: Do not display any output from the command.


## Configuration

Your default configuration is:
```yaml
goingrunning:
    song_bpm: [90, 150]
    song_len: [90, 240]
    duration: 60
    targets: []
    target: no
    clean_target: no
```

There are two concepts you need to know to configure the plugin: targets and trainings:

- **Targets** are named destinations on your file system to which you will be copying your songs. The `targets` key allows you to define multiple targets whilst the `target` key allows you to specify the name of your default player to which the plugin will always copy your songs (if not otherwise specified in the configuration of a specific training).

```yaml
goingrunning:
    # [...]
    targets:
        my_player_1:
            device_root: /mnt/player_1
            device_path: 
        my_other_player:
            device_root: /media/player_2
            device_path: Songs
    target: my_player_1
    # [...]
```

- **Trainings** are not much more than named queries into your library. They have two main attributes (`song_bpm` and `song_len`) by which the plugin will decide which songs to chose and a `duration` element (expressed in minutes) used for limiting the number of songs selected. The `song_bpm` and `song_len` attributes have two numbers which indicate the lower and the higher limit of that attribute. A training can optionally declare the `target` and other attributes to override those present at root level (directly under the `goingrunning` key).

A common configuration section will look something like this:

```yaml
goingrunning:
    # [...]
    clean_target: no
    target: my_player_1
    targets:
        my_player_1:
            device_root: /mnt/player_1
            device_path: 
        my_other_player:
            device_root: /media/player_2
            device_path: Songs
            clean_target: yes
            delete_from_device:
                - STDBDATA.DAT
                - STDBSTR.DAT
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
    # [...]
```

Once you have configured your targets and created your trainings, connect your device to your pc and launch:

    $ beet goingrunning longrun
    
and the songs matching that training will be copied to it.

The path where the songs will be copied is given by the `device_root` + `device_path`. This means that for `my_player_1` the songs will be copied to the `/mnt/player_1/` folder whilst for the `my_player_2` target they will be copied to the `/media/player_2/Songs/` folder.
The `clean_target` attribute will instruct the plugin to clean these folders before copying the new songs.
The option `delete_from_device` allows you to list additional files that need to be removed. The files listed here are relative to the `device_root` directive.

For now, within a training the selection of the songs is completely random and no ordering is applied. One of the future plans is to allow you to be more in control of the song selection and song ordering. You can of course use the usual query syntax to fine tune your selection (see examples below) but the ordering will still be casual.

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
