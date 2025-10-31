# ACQ400 Regression

Test Features of D-tacq Digitizers.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sambelltacq/acq400_regression
cd acq400_regression
```

2. Install in development mode:
```bash
pip install -e .
```

## Command Line Usage

The package provides a command-line interface accessible via `acq400_regression`:

```bash
# List tests
acq400_regression test --help

# Test post
acq400_regression test post acq2206_088 --siggen=SG0792

# Test rtm on two UUTs
acq400_regression test rtm acq2206_088 acq2206_089 --siggen=SG0792

# Test post then stream
acq400_regression test post,stream acq2206_088 --siggen=SG0792

# Exec tests from file
acq400_regression exec test_def.json acq2206_088

# Upload test results to remote host(bespin)
acq400_regression upload bespin/regression
```

## Overview

Each ***test*** has a number of parameters ( trigger, events, translen ) we test every unique combination of these parameters each is called a ***test run***.

Each ***test run***, repeats a number of times called ***test shots***

When the  ***test shots*** complete or error its configuration, results and any attached files (binary data, console logs, plot images) are saved to disk

Files are saved to the path `results/UUT+MODULE/timestamp/TEST/TEST_RUN`

Files can be uploaded to a remote host

A test definition file can be created that specfies all tests to run and all args values

Multiple tests can be run consecutively by adding commas to the test positional `post,prepost,rtm` however tests will share args so `post=50000` applies to all, use a definition file to run multiple with differing arguments
## Tests

### Post

#### Test Post transient functionality
```bash
usage: acq400_regression test post [--channels CHANNELS] [--shots SHOTS]
                                   [--wavelength WAVELENGTH] [--cycles CYCLES]
                                   [--demux DEMUX] [--spad SPAD] [--verbose] --siggen
                                   SIGGEN [--post POST] [--trigger TRIGGER]
                                   uuts [uuts ...]

positional arguments:
  uuts                  uut hostnames

options:
  --channels CHANNELS   Channels to test (e.g., 1,2,3,4 or all)
  --shots SHOTS         Total shots per run
  --wavelength WAVELENGTH
                        target samples in waveform
  --cycles CYCLES       waveform cycles
  --demux DEMUX         Demux (disabled: 0) or (enabled: 1)
  --spad SPAD           spad value
  --verbose, -v         Enable verbose output
  --siggen SIGGEN       signal generator hostname
  --post POST           Post samples
  --trigger TRIGGER, --triggers TRIGGER
                        Triggers to test 1,0,0/1,0,1/1,1,1 or all
```

### Prepost

#### Test Prepost transient functionality
```bash
usage: acq400_regression test prepost [--channels CHANNELS] [--shots SHOTS]
                                      [--wavelength WAVELENGTH] [--cycles CYCLES]
                                      [--demux DEMUX] [--spad SPAD] [--verbose] --siggen
                                      SIGGEN [--pre PRE] [--post POST]
                                      [--trigger TRIGGER] [--event EVENT]
                                      uuts [uuts ...]

positional arguments:
  uuts                  uut hostnames

options:
  --channels CHANNELS   Channels to test (e.g., 1,2,3,4 or all)
  --shots SHOTS         Total shots per run
  --wavelength WAVELENGTH
                        target samples in waveform
  --cycles CYCLES       waveform cycles
  --demux DEMUX         Demux (disabled: 0) or (enabled: 1)
  --spad SPAD           spad value
  --verbose, -v         Enable verbose output
  --siggen SIGGEN       signal generator hostname
  --pre PRE             Post samples
  --post POST           Post samples
  --trigger TRIGGER, --triggers TRIGGER
                        Triggers to test 1,0,0/1,0,1/1,1,1 or all
  --event EVENT, --events EVENT
                        Events to test 1,0,0/1,0,1 or all
```

### RTM

#### Test RTM transient functionality
```bash
usage: acq400_regression test rtm [--channels CHANNELS] [--shots SHOTS]
                                  [--wavelength WAVELENGTH] [--cycles CYCLES]
                                  [--demux DEMUX] [--spad SPAD] [--verbose] --siggen
                                  SIGGEN [--post POST] [--trigger TRIGGER] [--rgm RGM]
                                  [--translen TRANSLEN]
                                  uuts [uuts ...]

positional arguments:
  uuts                  uut hostnames

options:
  --channels CHANNELS   Channels to test (e.g., 1,2,3,4 or all)
  --shots SHOTS         Total shots per run
  --wavelength WAVELENGTH
                        target samples in waveform
  --cycles CYCLES       waveform cycles
  --demux DEMUX         Demux (disabled: 0) or (enabled: 1)
  --spad SPAD           spad value
  --verbose, -v         Enable verbose output
  --siggen SIGGEN       signal generator hostname
  --post POST           Post samples
  --trigger TRIGGER, --triggers TRIGGER
                        Triggers to test 1,1,1 or all
  --rgm RGM, --rgms RGM
                        Triggers to test 3,0,1 or all
  --translen TRANSLEN   rtm_translen value
```

### Bolo

#### Test Bolo transient functionality
```bash
TODO
```


### Stream

#### Test continuous Stream functionality

```bash
usage: acq400_regression test stream [--channels CHANNELS] [--shots SHOTS]
                                     [--wavelength WAVELENGTH] [--cycles CYCLES]
                                     [--demux DEMUX] [--spad SPAD] [--verbose]
                                     [--runtime RUNTIME] [--mask MASK]
                                     uuts [uuts ...]

positional arguments:
  uuts                  uut hostnames

options:
  --channels CHANNELS   Channels to test (e.g., 1,2,3,4 or all)
  --shots SHOTS         Total shots per run
  --wavelength WAVELENGTH
                        target samples in waveform
  --cycles CYCLES       waveform cycles
  --demux DEMUX         Demux (disabled: 0) or (enabled: 1)
  --spad SPAD           spad value
  --verbose, -v         Enable verbose output
  --runtime RUNTIME     stream runtime
  --mask MASK           Stream mask
```

### RTM Stream

#### Test continuous RTM Stream functionality

```bash
usage: acq400_regression test stream [--channels CHANNELS] [--shots SHOTS]
                                     [--wavelength WAVELENGTH] [--cycles CYCLES]
                                     [--demux DEMUX] [--spad SPAD] [--verbose]
                                     [--runtime RUNTIME] [--mask MASK]
                                     uuts [uuts ...]

positional arguments:
  uuts                  uut hostnames

options:
  --channels CHANNELS   Channels to test (e.g., 1,2,3,4 or all)
  --shots SHOTS         Total shots per run
  --wavelength WAVELENGTH
                        target samples in waveform
  --cycles CYCLES       waveform cycles
  --demux DEMUX         Demux (disabled: 0) or (enabled: 1)
  --spad SPAD           spad value
  --verbose, -v         Enable verbose output
  --runtime RUNTIME     stream runtime
  --mask MASK           Stream mask#
  --rgm RGM, --rgms RGM
                        Triggers to test 3,0,1 or all
  --translen TRANSLEN   rtm_translen value
```

### Slowmon Stream

#### Test continuous Slowmon Stream functionality

```bash
TODO
```


### AWG Play

#### Test AWG Play functionality

```bash
TODO
```

### Segments Play

#### Test Segments Play functionality

```bash
TODO
```

### GPG Play

#### Test GPG Play functionality

```bash
TODO
```



### HUDP Stream

#### Test continuous HUDP Stream functionality

```bash
TODO
```


### HTS

#### Test afhba HTS functionality

```bash
TODO
```

### LLC

#### Test afhba LLC functionality

```bash
TODO
```
