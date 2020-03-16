[![Build Status](https://travis-ci.org/adamjakab/BeetsPluginGoingRunning.svg?branch=master)](https://travis-ci.org/adamjakab/BeetsPluginGoingRunning)
[![Coverage Status](https://coveralls.io/repos/github/adamjakab/BeetsPluginGoingRunning/badge.svg?branch=master)](https://coveralls.io/github/adamjakab/BeetsPluginGoingRunning?branch=master)
[![PyPi](https://img.shields.io/pypi/v/beets-goingrunning.svg)](https://pypi.org/project/beets-goingrunning/)

# Going Running (beets plugin)

The *beets-goingrunning* is a [beets](https://github.com/beetbox/beets) plugin for obsessive-compulsive music geek runners. It lets you configure different training activities by filtering songs based on their tag attributes (bpm, length, mood, loudness, etc) and generates a list of songs for that specific training.

Have you ever tried to beat your PR and have good old Bob singing about ganja in the background? It doesn’t really work. Or don't you know how those recovery session end up with the Crüe kickstarting your heart? You'll be up in your Zone 4 in no time. 

The fact is that it is very difficult and time consuming to compile an appropriate playlist for a specific training session. This plugin tries to help runners with this by allowing them to use their own library.


## Introduction

To use this plugin at its best and to benefit the most from your library, you will want to make sure that your songs have the most possible information on rhythm, moods, loudness, etc.   

Without going into much detail the most fundamental information you will want to harvest is `bpm`. Normally, when you run a fast pace training you will keep your pace (the number of times your feet hit the ground in a minute) around 170-180. If you are listening to songs with the same rhythm it helps a lot. If your library has many songs without the bpm information (check with `beet ls bpm:0`) you will not be able to use those songs. So, you should consider updating them. There are many tools you can use:

1) Use the built-in [acousticbrainz plugin](https://beets.readthedocs.io/en/stable/plugins/acousticbrainz.html) to fetch the bpm plus many other information about your songs. This is your starting point. It is as easy as `beet cousticbrainz` and it will do the rest. This tool is based on an on-line database so it will be able to fetch only what has been submitted by someone else. If you have many "uncommon" songs you will need to integrate it with other tools. (My library was still 30% uncovered after a full scan.)

2) Use the [bpmanalyser plugin](https://github.com/adamjakab/BeetsPluginBpmAnalyser). This will scan your songs and calculate the tempo (bpm) value for them. If you have a big collection it might take a while, but since this tool does not use an on-line database, you can potentially end up with 100% coverage. This plugin will only give you bpm info.

3) [Essentia extractors](https://essentia.upf.edu/index.html). The Acoustic Brainz (AB) project is based partly on these low and high level extractors. There is currently a highly under-development project [xtractor plugin](https://github.com/adamjakab/BeetsPluginXtractor) which aims to bring your library to 100% coverage. However, for the time being there are no distributable static extractors, so wou will have to compile your own extractors. 

There are many other ways and tools we could list here but I think you got the point...


## Installation
The plugin can be installed via:

```shell script
$ pip install beets-goingrunning
```

Activate the plugin in your configuration file by adding `goingrunning` to the plugins section:

```yaml
plugins:
    - goingrunning
```

Check if plugin is loaded with `beet version`. It should list 'goingrunning' amongst the loaded plugins.


## Usage

Invoke the plugin as:

    $ beet goingrunning training [options] [QUERY...]
    
or with the shorthand alias `gr`:

    $ beet gr training [options] [QUERY...]

The following command line options are available:

**--list [-l]**: List all the configured trainings. With `beet goingrunning --list` you will be presented the list of the trainings you have configured in your configuration file.

**--count [-c]**: Count the number of songs available for a specific training. With `beet goingrunning longrun --count` you can see how many of your songs will fit the specifications for the `longrun` training.

**--dry-run [-r]**: Only display what would be done without actually making changes to the file system. The plugin will run without clearing the destination and without copying any files.

**--quiet [-q]**: Do not display any output from the command.

**--version [-v]**: Display the version number of the plugin. Useful when you need to report some issue and you have to state the version of the plugin you are using.


## Configuration

suggest external configuration file with include:

Your default configuration is:
```yaml
goingrunning:
    query:
      bpm: 90..150
      length: 90..240
    ordering:
      year+: 100
      bpm+: 100
    duration: 60
    targets: []
    target: none
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

- **Trainings** are stored named queries into your library. They have two main attributes (`query` and `ordering`) by which the plugin will decide which songs to chose and in what order to put them. The `duration` attribute (expressed in minutes) is used for limiting the number of songs selected. The keys under `query` and `ordering` are the same as you would use them on the command line. A training can optionally declare the `target` and other attributes to override those present at root level (directly under the `goingrunning` key).

A common configuration section will look something like this:

```yaml
goingrunning:
    # [...]
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
            query:
              bpm: 90..150
              length: 90..240
            duration: 90
        10K: 
            query:
              bpm: 150..180
              length: 120..240
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
    
Check what the `longrun` training would do:

    $ beet goingrunning longrun --dry-run
    
Now do it! Copy your songs to your target based on the `longrun` training:

    $ beet goingrunning longrun
    
Do the same as above but today you feel reggae:

    $ beet goingrunning longrun genre:Reggae

### Issues
If something is not working as expected please use the Issue tracker.
If the documentation is not clear please use the Issue tracker.
If you have a feature request please use the Issue tracker.
In any other situation please use the Issue tracker.

### Roadmap
Please check the [ROADMAP](./docs/ROADMAP.md) file. If there is a feature you would like to see but which is not planned, create a feature request in the Issue tracker. 


### Final Remarks:

- give feedback
- contribute
- enjoy!
