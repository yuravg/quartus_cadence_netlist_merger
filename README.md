# Overview

Quartus pin and Cadence Allegro net-list merger (cnl - Cadence Net-List)


Quartus pin file
```
Pin Name/Usage               : Location  : Dir.   : I/O Standard      : Voltage : I/O Bank  : User Assignment
-------------------------------------------------------------------------------------------------------------
GND                          : A1        : gnd    :                   :         :           :
adc_db[9]                    : F19       : output : LVDS              :         : 6         : Y
VCCINT                       : G12       : power  :                   : 1.2V    :           :
pwr_stv[0]                   : G13       : bidir  : 3.3-V LVCMOS      :         : 7         : Y
```

Output example:

```
Pin Name(capture) :  Net Name(capture) :  Pin Name/Usage               : Location  : Dir.   : I/O Standard      : Voltage : I/O Bank  : User Assignment
-------------------------------------------------------------------------------------------------------------
GND_A1              GND                  GND                          : A1        : gnd    :                   :         :           :
DIFFIO_R8P          DOUTBH9              adc_db[9]                    : F19       : output : LVDS              :         : 6         : Y
VCCINT_G12          VCCINT_1V2           VCCINT                       : G12       : power  :                   : 1.2V    :           :
IO_G13              PWR_STV0             pwr_stv[0]                   : G13       : bidir  : 3.3-V LVCMOS      :         : 7         : Y
```

# Install

install release or install from source

## Install release

- download latest [release](https://github.com/yuravg/quartus_cadence_netlist_merger/releases)

- install `pip install quartus_cadence_netlist_merger-<version>.whl`

## Build and install from source

- Download source

- Build

to build the Python package you need to run

`make build`

- Install

to install python package:

`make install`

or

`pip install quartus_cadence_netlist_merger-<version>.whl`

# Usage

run at the command prompt:

`q2_cnl_merger`

(Quartus II, Cadence Net-List merger)
