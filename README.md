# gpu_mon
Python script which monitors gpu access and manages external programs when GPU is idle

## How

Every N seconds it checks /dev/nvidiaX device file for other processes accessing them (using fuser tool). 
According to this, it treats gpu card as idle or busy. If GPU becomes idle, it can start external program, which will 
be stopped when device file will be accesses by some process later.
 
Additionally, it can monitor PTY sessions to check that there are active users logged in and stop it's processes to 
avoid influence with somebody's work.

## Why

1. Monitoring and reporting of gpu usage
2. Mining on idle hardware.

## Requirements and limitations

Written on python3. Developed and tested under linux (ubuntu and debian) with NVidia cards. Don't have external 
libraries requirements except standard library.
  
## Running

1. create configuration file in ~/.config/gpu_mon.conf from provided template in `conf` dir
2. run `./gpu_mon.py`

## Configuration

Basic configuration file looks like this and mostly self-explaining:
```ini
[defaults]
; how frequently perform GPU and tty checks
interval_seconds=10

; configuration of GPUs to monitor for external program access. It could be several such sections with 'gpu-' prefix
[gpu-all]
; list of comma-separated gpu indices or ALL to handle all available gpus
gpus=ALL
; comma-separated list of programs which can access gpu and should be ignored
ignore_programs=nvidia-smi

; program which will be started on gpu during idle time
[process-all]
dir=/tmp
cmd=miner-run
; list of gpu indices or ALL to handle all available gpus
gpus=ALL
; log for processes. If not specified, show on console, if specified to file, data will be appended
log=/dev/null

; configuration of tty monitoring if enabled and user is active and not in whitelist, all processes will be stopped
[tty]
enabled=True
whitelist=user1,user2
; how long user should be inactive in tty to be ignored by checker
idle_seconds=300
```

## Donations

If you find this useful and want to support developer, please consider donation.

* BTC: 1FvhCby4UNtHmm2DFzzFRvfDL64uLSt4CN
* BCC: 18cpNK3LmH7mbYkvUyDo6TSji4zGraCsu
* ZEC: t1WMErz3JZZwkK1NLVadoi9ydgFHZhPHrWo
* KMD: R9uk6UARL1vbyoGuP8NQNf8JvTxyRA1Xt1
* Paypal: https://www.paypal.me/shmuma
