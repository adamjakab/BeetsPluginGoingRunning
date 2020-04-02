[![Build Status](https://travis-ci.org/adamjakab/BeetsPluginGoingRunning.svg?branch=devel)](https://travis-ci.org/adamjakab/BeetsPluginGoingRunning)
[![Coverage Status](https://coveralls.io/repos/github/adamjakab/BeetsPluginGoingRunning/badge.svg?branch=devel)](https://coveralls.io/github/adamjakab/BeetsPluginGoingRunning?branch=devel)
[![PyPi](https://img.shields.io/pypi/v/beets-goingrunning.svg)](https://pypi.org/project/beets-goingrunning/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/beets-goingrunning.svg)](https://pypi.org/project/beets-goingrunning/)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.txt)

# Going Running (Beets Plugin)

The *beets-goingrunning* is a [beets](https://github.com/beetbox/beets) plugin for obsessive-compulsive music geek runners. It lets you configure different training activities by filtering songs based on their tag attributes (bpm, length, mood, loudness, etc), generates a list of songs for that specific training and copies those songs to your player device.

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
    
or with the shorthand alias `run`:

    $ beet run training [options] [QUERY...]

The following command line options are available:

**--list [-l]**: List all the configured trainings. With `beet goingrunning --list` you will be presented the list of the trainings you have configured in your configuration file.

**--count [-c]**: Count the number of songs available for a specific training. With `beet goingrunning longrun --count` you can see how many of your songs will fit the specifications for the `longrun` training.

**--dry-run [-r]**: Only display what would be done without actually making changes to the file system. The plugin will run without clearing the destination and without copying any files.

**--quiet [-q]**: Do not display any output from the command.

**--version [-v]**: Display the version number of the plugin. Useful when you need to report some issue and you have to state the version of the plugin you are using.


## Configuration

All your configuration will need to be created under the key `goingrunning`. There are three concepts you need to know to configure the plugin: targets, trainings and flavours. They are explained in detail below.


### Targets

Targets are named destinations on your file system to which you will be copying your songs. The `targets` key allows you to define multiple targets so that under a specific training session you will only need to refer to it with the `target` key.

The configuration of the target names `MPD1` will look like this:

```yaml
goingrunning:
    targets:
      MPD1:
        device_root: /media/MPD1/
        device_path: MUSIC/AUTO/
        clean_target: yes
        delete_from_device:
          - LIBRARY.DAT
```

The key `device_root` indicates where your operating system mounts the device. The key `device_path` indicates the folder inside the device to which your audio files will be copied. In the above example the final destination is `/media/MPD1/MUSIC/AUTO/`. It is assumed that the folder indicated in the `device_path` key exists. If it doesn't the plugin will exit with a warning. 

The key `clean_target`, when set to yes, instructs the plugin to clean the `device_path` folder before copying the new songs to the device. This will remove all audio songs and playlists found in that folder.

Some devices might have library files or other data files which need to be deleted in order for the device to reindex the new songs. These files can be added to the `delete_from_device` key. The files listed here are relative to the `device_root` directive.


### Trainings

Trainings are the central concept behind the plugin. When you are "going running" you will already have in mind the type of training you will be doing. This configuration section allows you to preconfigure filters that will allow you to launch a `beet run 10K` command whilst you are tying your shoelaces and be out of the house as quick as possible. In fact, the `trainings` section is there for you to be able to preconfigure these trainings.

The configuration of a hypothetical 10K training might look like this:

```yaml
goingrunning:
  trainings:
    10K: 
      query:
        bpm: 160..180
        mood_aggressive: 0.6..
        ^genre: Reggae
      ordering:
        bpm: 100
        average_loudness: 50
      use_flavours: []
      duration: 60
      target: MPD1
```

#### query
The keys under the `query` section are exactly the same ones that you use when you are using beets for any other operation. Whatever is described in the [beets query documentation](https://beets.readthedocs.io/en/stable/reference/query.html) applies here with two restriction: you must query specific fields in the form of `field: value` and (for now) regular expressions are not supported.

#### ordering
Your songs are ordered based on a scoring system. What you indicate under the `ordering` section is the fields by which the songs will be ordered and the weight each one of them will have on the final score. The weight can go from -100 to 100. Negative numbers indicate a reverse ordering. (...probably need more explanation?...)

#### use_flavours
You will find that many of the query specification that you come up with will be repeated across different trainings. To reduce repetition and at the same time to be able to combine many different recipes you can use flavours. Similarly to targets, instead of defining the queries directly on your training you can define queries in a separate section called `flavours` (see below) and then use the `use_flavours` key to indicate which flavours to use. The order in which flavours are indicated is important: the first one has the highest priority meaning that it will overwrite any keys that might be found in subsequent flavours.

#### duration
The duration is expressed in minutes and serves the purpose of defining the total length of the training so that the plugin can select the exact number of songs. 

#### target
This key indicates to which target (defined in the `targets` section) your songs will be copied to.


#### the `fallback` training
You might also define a special `fallback` training:

```yaml
goingrunning:
  trainings:
    fallback: 
      target: my_other_player
```

Any key not defined in a specific training will be looked up from the `fallback` training. So, if in the `10K` example you were to remove the `target` key, it would be looked up from the `fallback` training and your songs would be copied to the `my_other_device` target.


### Flavours
The flavours section serves the purpose of defining named queries. If you have 5 different high intensity trainings different in length but sharing queries about bpm, mood and loudness, you can create a single definition here, called flavour, and reuse that flavour in your different trainings with the `use_flavours` key.

**Note**: Because flavours are only used to group query elements, the `query` key should not be used here (like it is in trainings). 

```yaml
goingrunning:
  flavours:
    overthetop:
      bpm: 170..
      mood_aggressive: 0.8..
      average_loudness: 50..
    rocker:
      genre: Rock
    metallic:
      genre: Metal
  sunshine:
      genre: Reggae
    60s:
      year: 1960..1969
    chillout:
      bpm: 1..120
      mood_happy: 0.5..0.99
```

This way, from the above flavours you might add `use_flavours: [overthetop, rock, 60s]` to one training and `use_flavours: [overthetop, metallic]` to another so they will share the same `overthetop` intensity definition whilst having different genre preferences. Similarly, your recovery session might use `use_flavours: [chillout, sunshine]`.


### Using a separate configuration file
In my experience the configuration section can grow quite long depending on your needs, so I find it useful to keep my `goingrunning` specific configuration in a separate file and from the main configuration file include it like this:

```yaml
include: 
    - plg_goingrunning.yaml
```


## Examples

Show all the configured trainings:

    $ beet goingrunning --list
    
Check what would be done for the `10K` training:

    $ beet goingrunning 10K --dry-run
    
Let's go! Copy your songs to your device based on the `10K` training and using the plugin shorthand:

    $ beet run 10K

Do the same as above but today you feel Ska:

    $ beet run 10K genre:ska


## Issues
If something is not working as expected please use the Issue tracker.
If the documentation is not clear please use the Issue tracker.
If you have a feature request please use the Issue tracker.
In any other situation please use the Issue tracker.


## Roadmap
Please check the [ROADMAP](./docs/ROADMAP.md) file. If there is a feature you would like to see but which is not planned, create a feature request in the Issue tracker. 


## Final Remarks
Enjoy!
