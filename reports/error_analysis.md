# Error analysis (exact-match correctness, post-processed like PA)


## test_heldout

### PA per system (line-level, not the macro average)

| system | drain | base_zeroshot | base_fewshot | ft_r16 | ft_r16_cap10 |
|---|---|---|---|---|---|
| Mac | 0.147 | 0.124 | 0.177 | 0.363 | 0.382 |
| OpenStack | 0.006 | 0.32 | 0.325 | 0.354 | 0.334 |
| Proxifier | 0.0 | 0.045 | 0.084 | 0.106 | 0.09 |
| Thunderbird | 0.313 | 0.006 | 0.401 | 0.519 | 0.614 |


### Wrong predictions by category

|  | drain | base_zeroshot | base_fewshot | ft_r16 | ft_r16_cap10 |
|---|---|---|---|---|---|
| format | 7 | 2278 | 1190 | 41 | 30 |
| hallucinated | 0 | 664 | 42 | 91 | 447 |
| under-generalised | 1400 | 398 | 898 | 1185 | 1028 |
| over-generalised | 1812 | 69 | 910 | 1241 | 1188 |
| other | 620 | 26 | 150 | 304 | 162 |


### ft_r16 vs base_fewshot: fixed 424, broke 96 of 4128 lines


**Fixed** (first 20 of 424, one per distinct gold)

- `(DiskStore.Normal:2382) 20cb04f 1.000086`
  - gold `(DiskStore.Normal:<*>) <*> <*>`
  - ft_r16 `(DiskStore.Normal:<*>) <*> <*>`  /  base_fewshot `(<>) (<>) <>`
- `**** [IOBluetoothHostControllerUSBTransport][start] -- completed -- result = TRUE -- 0x2800 ****`
  - gold `**** [IOBluetoothHostControllerUSBTransport][start] -- completed -- result = <*> -- <*> ****`
  - ft_r16 `**** [IOBluetoothHostControllerUSBTransport][start] -- completed -- result = <*> -- <*> ****`  /  base_fewshot `**** [IOBluetoothHostControllerUSBTransport][start] -- completed -- result = TRUE -- 0x2800 ****`
- `-[NETClientConnection effectiveBundleID] using process name CalendarAgent as bundle ID (this is expe`
  - gold `-[NETClientConnection effectiveBundleID] using process name CalendarAgent as bundle ID (this is expe`
  - ft_r16 `-[NETClientConnection effectiveBundleID] using process name CalendarAgent as bundle ID (this is expe`  /  base_fewshot `-[NETClientConnection effectiveBundleID] using process name <*> as bundle ID (this is expected for d`
- `-[SOAPParser:0x7fca6040cb50 parser:didStartElement:namespaceURI:qualifiedName:attributes:] Type not `
  - gold `-[SOAPParser:<*> parser:didStartElement:namespaceURI:qualifiedName:attributes:] Type not found in EW`
  - ft_r16 `-[SOAPParser:<*> parser:didStartElement:namespaceURI:qualifiedName:attributes:] Type not found in EW`  /  base_fewshot `-[SOAPParser:0x7fca6040cb50 parser:didStartElement:namespaceURI:qualifiedName:attributes:] Type not `
- `.sdef warning for argument '' of command 'can continue previous list' in suite 'Microsoft Word Suite`
  - gold `.sdef warning for argument '' of command 'can continue previous list' in suite 'Microsoft Word Suite`
  - ft_r16 `.sdef warning for argument '' of command 'can continue previous list' in suite 'Microsoft Word Suite`  /  base_fewshot `.sdef warning for argument '' of command 'can continue previous list' in suite '<*>': '<*>' is not a`
- `<IMMacNotificationCenterManager: 0x7fdcc9d16380>: notification observer: com.apple.FaceTime   notifi`
  - gold `<IMMacNotificationCenterManager: <*>: notification observer: com.apple.FaceTime notification: __CFNo`
  - ft_r16 `<IMMacNotificationCenterManager: <*>>: notification observer: com.apple.FaceTime   notification: __C`  /  base_fewshot `<IMMacNotificationCenterManager: 0x7fdcc9d16380>: notification observer: com.apple.FaceTime   notifi`
- `ARPT: 620750.434035: wl0: wl_update_tcpkeep_seq: Original Seq: 3226706533, Ack: 3871687177, Win size`
  - gold `ARPT: <*>: wl0: wl_update_tcpkeep_seq: Original Seq: <*>, Ack: <*>, Win size: <*>`
  - ft_r16 `ARPT: <*>: wl0: wl_update_tcpkeep_seq: Original Seq: <*>, Ack: <*>, Win size: <*>`  /  base_fewshot `ARPT: <*>.<>: <*>: <*>_update_tcpkeep_seq: Original Seq: <*>, Ack: <*>, Win size: <*>`
- `ARPT: 621241.634070: wl0: MDNS: IPV6 Addr: 2607:f140:6000:8:c6b3:1ff:fecd:467f`
  - gold `ARPT: <*>: wl0: MDNS: IPV6 Addr: <*>`
  - ft_r16 `ARPT: <*>: wl0: MDNS: IPV6 Addr: <*>`  /  base_fewshot `ARPT: <*>.<>: <*>: MDNS: IPV6 Addr: <*>`
- `ARPT: 621490.858770: wl0: wl_update_tcpkeep_seq: Updated seq/ack/win from UserClient Seq 2119064372,`
  - gold `ARPT: <*>: wl0: wl_update_tcpkeep_seq: Updated seq/ack/win from UserClient Seq <*>, Ack <*>, Win siz`
  - ft_r16 `ARPT: <*>: wl0: wl_update_tcpkeep_seq: Updated seq/ack/win from UserClient Seq <*>, Ack <*>, Win siz`  /  base_fewshot `ARPT: <*>.<>: <*>: <*> update_tcpkeep_seq: Updated seq/ack/win from UserClient Seq <*>, Ack <*>, Win`
- `ARPT: 621542.378462: ARPT: Wake Reason: Wake on Scan offload`
  - gold `ARPT: <*>: ARPT: Wake Reason: Wake on Scan offload`
  - ft_r16 `ARPT: <*>: ARPT: Wake Reason: Wake on Scan offload`  /  base_fewshot `ARPT: <*>. <*>: ARPT: Wake Reason: Wake on Scan offload`
- `ARPT: 645957.322055: wl0: setup_keepalive: Local IP: 10.105.163.202`
  - gold `ARPT: <*>: wl0: setup_keepalive: Local IP: <*>`
  - ft_r16 `ARPT: <*>: wl0: setup_keepalive: Local IP: <*>`  /  base_fewshot `ARPT: <*>.<<>>: <*>: setup_keepalive: Local IP: <*>`
- `ARPT: 671889.268467: wl0: setup_keepalive: Seq: 2040703749, Ack: 3006590414, Win size: 4096`
  - gold `ARPT: <*>: wl0: setup_keepalive: Seq: <*>, Ack: <*>, Win size: <*>`
  - ft_r16 `ARPT: <*>: wl0: setup_keepalive: Seq: <*>, Ack: <*>, Win size: <*>`  /  base_fewshot `ARPT: <*>.<>: <*>: setup_keepalive: Seq: <*>, Ack: <*>, Win size: <*>`
- `ARPT: 673325.798753: ARPT: Wake Reason: Wake on TCP Timeout`
  - gold `ARPT: <*>: ARPT: Wake Reason: Wake on TCP Timeout`
  - ft_r16 `ARPT: <*>: ARPT: Wake Reason: Wake on TCP Timeout`  /  base_fewshot `ARPT: <*>. <*>: ARPT: Wake Reason: Wake on TCP Timeout`
- `ARPT: 682068.402171: framerdy 0x0 bmccmd 7 framecnt 1024`
  - gold `ARPT: <*>: framerdy <*> bmccmd <*> framecnt <*>`
  - ft_r16 `ARPT: <*>: framerdy <*> bmccmd <*> framecnt <*>`  /  base_fewshot `ARPT: <*>.<>: framerdy 0x<*> bmccmd <*> framecnt <*>`
- `ARPT: 682406.173418: wl0: setup_keepalive: Remote IP: 17.249.28.77`
  - gold `ARPT: <*>: wl0: setup_keepalive: Remote IP: <*>`
  - ft_r16 `ARPT: <*>: wl0: setup_keepalive: Remote IP: <*>`  /  base_fewshot `ARPT: <*>.<>: <*>: setup_keepalive: Remote IP: <*>`
- `ARPT: 682834.192587: wlc_dump_aggfifo:`
  - gold `ARPT: <*>: wlc_dump_aggfifo:`
  - ft_r16 `ARPT: <*>: wlc_dump_aggfifo:`  /  base_fewshot `ARPT: <*>.<>: wlc_dump_aggfifo:`
- `ARPT: 724509.898718: wl0: MDNS: IPV4 Addr: 10.105.160.226`
  - gold `ARPT: <*>: wl0: MDNS: IPV4 Addr: <*>`
  - ft_r16 `ARPT: <*>: wl0: MDNS: IPV4 Addr: <*>`  /  base_fewshot `ARPT: <*>.<>: <*>: MDNS: IPV4 Addr: <*>`
- `AirPort: Link Up on awdl0`
  - gold `AirPort: Link Up on awdl0`
  - ft_r16 `AirPort: Link Up on awdl0`  /  base_fewshot `AirPort: Link Up on <*>`
- `Cocoa scripting error for '0x00660011': four character codes must be four characters long.`
  - gold `Cocoa scripting error for '<*>': four character codes must be four characters long.`
  - ft_r16 `Cocoa scripting error for '<*>': four character codes must be four characters long.`  /  base_fewshot `Cocoa scripting error for ' <*> ': four character codes must be four characters long.`
- `DB Error: 1 "no such table: tb_c2cMsg_2658655094"`
  - gold `DB Error: <*> "no such table: <*>"`
  - ft_r16 `DB Error: <*> "no such table: tb_c<*>_<*>"`  /  base_fewshot `DB Error: 1 "no such table: tb_c2cMsg_<*>""`

**Broke** (first 20 of 96, one per distinct gold)

- `<<<< MediaValidator >>>> mv_LookupCodecSupport: Unrecognized codec 1`
  - gold `<<<< MediaValidator >>>> mv_LookupCodecSupport: Unrecognized codec <*>`
  - ft_r16 `MediaValidator: Unrecognized codec <*>`  /  base_fewshot `<<<< MediaValidator >>>> mv_LookupCodecSupport: Unrecognized codec <*>`
- `AirPort: Link Down on en0. Reason 8 (Disassociated because station leaving).`
  - gold `AirPort: Link Down on en0. Reason <*> (Disassociated because station leaving).`
  - ft_r16 `AirPort: Link Down on <*>. Reason <*> (Disassociated because station leaving).`  /  base_fewshot `AirPort: Link Down on en0. Reason <*> (Disassociated because station leaving).`
- `AirPort: Link Up on en0`
  - gold `AirPort: Link Up on en0`
  - ft_r16 `AirPort: Link Up on <*>`  /  base_fewshot `AirPort: Link Up on en0`
- `CCDataTap::profileRemoved, Owner: com.apple.driver.AirPort.Brcm4360.0, Name: StateSnapshots`
  - gold `CCDataTap::profileRemoved, Owner: <*>, Name: <*>`
  - ft_r16 `CCDataTap::profileRemoved, Owner: com.apple.driver.AirPort.Brcm4360.<*>, Name: StateSnapshots`  /  base_fewshot `CCDataTap::profileRemoved, Owner: <*>, Name: <*>`
- `en0: BSSID changed to 00:a2:ee:1a:71:8c`
  - gold `en0: BSSID changed to <*>`
  - ft_r16 `en0: BSSID changed to <*>:<*>:<*>:<*>:<*>:<*>`  /  base_fewshot `en0: BSSID changed to <*>`
- `en0: Supported channels 1 2 3 4 5 6 7 8 9 10 11 12 13 36 40 44 48 52 56 60 64 100 104 108 112 116 12`
  - gold `en0: Supported channels <*>`
  - ft_r16 `en<*>: Supported channels <*> <*> <*> <*> <*> <*> <*> <*> <*> <*> <*> <*> <*> <*> <*> <*> <*> <*> <*`  /  base_fewshot `en0: Supported channels <*>`
- `vm_compressor_fastwake_warmup (581519 - 591525) - starting`
  - gold `vm_compressor_fastwake_warmup (<*> - <*>) - starting`
  - ft_r16 `vm_compressor_fastwake_warmup (<*>) - starting`  /  base_fewshot `vm_compressor_fastwake_warmup (<*> - <*>) - starting`
- `Successfully synced instances from host 'cp-1.slowvm1.tcloud-pg0.utah.cloudlab.us'.`
  - gold `Successfully synced instances from host '<*>'.`
  - ft_r16 `Successfully synced instances from host 'cp-<*>'.`  /  base_fewshot `Successfully synced instances from host '<*>'.`
- `[instance: 43204226-2f87-4da7-b7ee-4d20cc66e846] Terminating instance`
  - gold `[instance: <*>] Terminating instance`
  - ft_r16 `[Terminating instance: <*>]`  /  base_fewshot `[instance: <*>] Terminating instance`
- `[instance: b562ef10-ba2d-48ae-bf4a-18666cba4a51] Total memory: 64172 MB, used: 512.00 MB`
  - gold `[instance: <*>] Total memory: <*> MB, used: <*> MB`
  - ft_r16 `[instance: <*>] Total memory: <*> MB, used: <*>.`  /  base_fewshot `[instance: <*>] Total memory: <*> MB, used: <*> MB`
- `apis.google.com:443 open through proxy proxy.cse.cuhk.edu.hk:5070 HTTPS`
  - gold `<*>:<*> open through proxy <*>:<*> HTTPS`
  - ft_r16 `apis.<*>:<*> open through proxy proxy.<*>:<*> HTTPS`  /  base_fewshot `<*>:<*> open through proxy <*>:<*> HTTPS`
- `Detected 3591.360 MHz processor.`
  - gold `Detected <*> MHz processor.`
  - ft_r16 `Detected <*> processor.`  /  base_fewshot `Detected <*> MHz processor.`
- `IOAPIC (id[0x09] address[0xfec80000] gsi_base[32])`
  - gold `IOAPIC (id[<*>] address[<*>] gsi_base[<*>])`
  - ft_r16 `IOAPIC (id[<*> address[<*>] gsi_base[<*>])`  /  base_fewshot `IOAPIC (id[<*>] address[<*>] gsi_base[<*>])`
- `Now running on #29#'s privileges.`
  - gold `Now running on #<*>#'s privileges.`
  - ft_r16 `Now running on <*>#'s privileges.`  /  base_fewshot `Now running on #<*>#'s privileges.`
- `User #29#, coming from #30#, authenticated.`
  - gold `User #<*>#, coming from #<*>#, authenticated.`
  - ft_r16 `User <*>, coming from <*>, authenticated.`  /  base_fewshot `User #<*>#, coming from #<*>#, authenticated.`
- `Using 14.318180 MHz HPET timer.`
  - gold `Using <*> MHz HPET timer.`
  - ft_r16 `Using <*> HPET timer.`  /  base_fewshot `Using <*> MHz HPET timer.`
- `Warning: we failed to resolve data source name an910 an911 an912 an913 an914 an915 an916 an917 an918`
  - gold `Warning: we failed to resolve data source name <*>`
  - ft_r16 `Warning: we failed to resolve data source name <*> <*> <*> <*> <*> <*> <*> <*> <*> <*> <*> <*> <*> <`  /  base_fewshot `Warning: we failed to resolve data source name <*>`
- `colour VGA+ 80x25`
  - gold `colour VGA+ <*>`
  - ft_r16 `colour VGA+ <*> <*>`  /  base_fewshot `colour VGA+ <*>x<*>`
- `data_thread() got not answer from any [Thunderbird_A1] datasource`
  - gold `data_thread() got not answer from any [<*>] datasource`
  - ft_r16 `data_thread() got not answer from any [<Thunderbird_A1>] datasource`  /  base_fewshot `data_thread() got not answer from any [<*>] datasource`
- `synchronized to #3#, stratum 1`
  - gold `synchronized to <*>, stratum <*>`
  - ft_r16 `synchronized to <*>#, stratum <*>`  /  base_fewshot `synchronized to <*>, stratum <*>`

## test_template_disjoint

### PA per system (line-level, not the macro average)

| system | drain | base_zeroshot | base_fewshot | ft_r16 | ft_r16_cap10 |
|---|---|---|---|---|---|
| Apache | 0.03 | 0.939 | 1.0 | 1.0 | 1.0 |
| BGL | 0.775 | 0.264 | 0.901 | 1.0 | 0.995 |
| HDFS | 0.032 | 0.0 | 0.014 | 0.619 | 0.499 |
| HPC | 0.23 | 0.0 | 0.148 | 0.197 | 0.262 |
| Hadoop | 0.301 | 0.072 | 0.735 | 0.783 | 0.783 |
| HealthApp | 0.022 | 0.003 | 0.363 | 0.613 | 0.613 |
| Linux | 0.816 | 0.0 | 0.737 | 0.842 | 0.816 |
| OpenSSH | 0.878 | 0.0 | 0.962 | 0.833 | 0.885 |
| Spark | 0.132 | 0.57 | 0.572 | 0.693 | 0.739 |
| Zookeeper | 0.059 | 0.282 | 0.565 | 0.906 | 0.894 |


### Wrong predictions by category

|  | drain | base_zeroshot | base_fewshot | ft_r16 | ft_r16_cap10 |
|---|---|---|---|---|---|
| format | 0 | 1034 | 954 | 0 | 0 |
| hallucinated | 0 | 534 | 23 | 13 | 0 |
| under-generalised | 958 | 359 | 167 | 268 | 338 |
| over-generalised | 426 | 49 | 53 | 316 | 298 |
| other | 630 | 57 | 217 | 172 | 172 |


### ft_r16 vs base_fewshot: fixed 675, broke 30 of 2480 lines


**Fixed** (first 20 of 675, one per distinct gold)

- `1 tree receiver 1 in re-synch state event(s) (dcr 0x0185) detected over 244 seconds`
  - gold `<*> tree receiver <*> in re-synch state event(s) (dcr <*>) detected over <*> seconds`
  - ft_r16 `<*> tree receiver <*> in re-synch state event(s) (dcr <*>) detected over <*> seconds`  /  base_fewshot `<*> tree receiver <*> in re-synch state event(s) (dcr 0x<>) detected over <*> seconds`
- `3 L3 EDRAM error(s) (dcr 0x0157) detected and corrected`
  - gold `<*> L3 EDRAM error(s) (dcr <*>) detected and corrected`
  - ft_r16 `<*> L3 EDRAM error(s) (dcr <*>) detected and corrected`  /  base_fewshot `<*> L3 EDRAM error(s) (dcr 0x0157) detected and corrected`
- `Node card VPD check: U01 node in processor card slot J08 do not match. VPD ecid 075F04E8A27BFFFF0702`
  - gold `Node card VPD check: <*> node in processor card slot <*> do not match. VPD ecid <*>, found <*>`
  - ft_r16 `Node card VPD check: <*> node in processor card slot <*> do not match. VPD ecid <*>, found <*>`  /  base_fewshot `Node card VPD check: <*> node in processor card slot <*> do not match. VPD ecid <>, found <>`
- `ciod: Error reading message prefix on CioStream socket to 172.16.96.116:41587, Connection reset by p`
  - gold `ciod: Error reading message prefix on CioStream socket to <*>:<*>, Connection reset by peer`
  - ft_r16 `ciod: Error reading message prefix on CioStream socket to <*>:<*>, Connection reset by peer`  /  base_fewshot `ciod: Error reading message prefix on CioStream socket to <*>:<>*, Connection reset by peer`
- `data TLB error interrupt`
  - gold `data TLB error interrupt`
  - ft_r16 `data TLB error interrupt`  /  base_fewshot `<*> TLB error interrupt`
- `lr:00004ed0 cr:28244842 xer:20000002 ctr:00086000`
  - gold `lr:<*> cr:<*> xer:<*> ctr:<*>`
  - ft_r16 `lr:<*> cr:<*> xer:<*> ctr:<*>`  /  base_fewshot `lr:<> cr:<> xer:<> ctr:<>`
- `rts: bad message header: expecting type 57 instead of type 3 (softheader=00131db8 81aa0003 00000002 `
  - gold `rts: bad message header: expecting type <*> instead of type <*> (softheader=<*> <*> <*> <*>) PSR0=<*`
  - ft_r16 `rts: bad message header: expecting type <*> instead of type <*> (softheader=<*> <*> <*> <*>) PSR0=<*`  /  base_fewshot `rts: bad message header: expecting type <*> instead of type <*> (softheader=<>) PSR0=<> PSR1=<> PRXF`
- `rts: kernel terminated for reason 1001rts: bad message header: invalid cpu, type=42315, cpu=105, ind`
  - gold `rts: kernel terminated for reason <*>: bad message header: invalid cpu, type=<*>, cpu=<*>, index=<*>`
  - ft_r16 `rts: kernel terminated for reason <*>rts: bad message header: invalid cpu, type=<*>, cpu=<*>, index=`  /  base_fewshot `rts: kernel terminated for reason <*>rts: bad message header: invalid cpu, type=<>, cpu=<>, index=<>`
- `special purpose registers:`
  - gold `special purpose registers:`
  - ft_r16 `special purpose registers:`  /  base_fewshot `special purpose registers: <*>`
- `10.250.15.198:50010 Starting thread to transfer block blk_4292382298896622412 to 10.250.15.240:50010`
  - gold `<*>:<*> Starting thread to transfer block <*> to <*>:<*>`
  - ft_r16 `<*>:<*> Starting thread to transfer block <*> to <*>:<*>`  /  base_fewshot `<*>:<*> Starting thread to transfer block <*> to <*>:<>`
- `BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.250.10.223:50010 is added to blk_-19485055891`
  - gold `BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>`
  - ft_r16 `BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>`  /  base_fewshot `BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<> is added to blk_<> size <*>`
- `Receiving block blk_-1133573997287815203 src: /10.251.123.195:59430 dest: /10.251.123.195:50010`
  - gold `Receiving block <*> src: <*>:<*> dest: <*>:<*>`
  - ft_r16 `Receiving block <*> src: <*>:<*> dest: <*>:<*>`  /  base_fewshot `Receiving block blk_-<*> src: <*>:<> dest: <*>:<>`
- `Verification succeeded for blk_-1383276859207001328`
  - gold `Verification succeeded for <*>`
  - ft_r16 `Verification succeeded for <*>`  /  base_fewshot `Verification succeeded for blk_<>`
- `Link error`
  - gold `Link error`
  - ft_r16 `Link error`  /  base_fewshot `<*>`
- `active`
  - gold `active`
  - ft_r16 `active`  /  base_fewshot `<*>`
- `bootGenvmunix  (command 1903)`
  - gold `bootGenvmunix (command <*>)`
  - ft_r16 `bootGenvmunix (command <*>)`  /  base_fewshot `bootGenvmunix (<>)`
- `normal`
  - gold `normal`
  - ft_r16 `normal`  /  base_fewshot `<*>`
- `not responding`
  - gold `not responding`
  - ft_r16 `not responding`  /  base_fewshot `<*>`
- `risBoot  (command 1903)`
  - gold `risBoot (command <*>)`
  - ft_r16 `risBoot (command <*>)`  /  base_fewshot `risBoot (<>)`
- `Opening proxy : 04DN8IQ.fareast.corp.microsoft.com:54883`
  - gold `Opening proxy : <*>:<*>`
  - ft_r16 `Opening proxy : <*>:<*>`  /  base_fewshot `Opening proxy : <*>:<>`

**Broke** (first 20 of 30, one per distinct gold)

- `Fan speeds ( 3534 3534 3375 **** 3497 3479 )`
  - gold `Fan speeds ( <*> <*> <*> **** <*> <*> )`
  - ft_r16 `Fan speeds ( <*> <*> <*> <*> <*> <*> )`  /  base_fewshot `Fan speeds ( <*> <*> <*> **** <*> <*> )`
- `CPU 0 irqstacks, hard=02345000 soft=02344000`
  - gold `CPU <*> irqstacks, hard=<*> soft=<*>`
  - ft_r16 `CPU <*> irqstacks, hard=<*>, soft=<*>`  /  base_fewshot `CPU <*> irqstacks, hard=<*> soft=<*>`
- `Detected 731.219 MHz processor.`
  - gold `Detected <*> MHz processor.`
  - ft_r16 `Detected <*> processor.`  /  base_fewshot `Detected <*> MHz processor.`
- `Invalid user Management from 103.99.0.122`
  - gold `Invalid user <*> from <*>`
  - ft_r16 `Invalid user Management from <*>`  /  base_fewshot `Invalid user <*> from <*>`
- `input_userauth_request: invalid user eoor [preauth]`
  - gold `input_userauth_request: invalid user <*> [preauth]`
  - ft_r16 `input_userauth_request: invalid user eoor [preauth]`  /  base_fewshot `input_userauth_request: invalid user <*> [preauth]`

## handcrafted

### PA per system (line-level, not the macro average)

| system | drain | base_zeroshot | base_fewshot | ft_r16 | ft_r16_cap10 |
|---|---|---|---|---|---|
| Docker | 0.417 | 0.25 | 0.25 | 0.75 | 0.75 |
| Kafka | 0.375 | 0.125 | 0.438 | 0.562 | 0.625 |
| Nginx | 0.273 | 0.0 | 0.455 | 0.364 | 0.545 |
| OpenSearch | 0.5 | 0.0 | 0.667 | 0.5 | 0.583 |
| PostgreSQL | 0.3 | 0.0 | 0.4 | 0.5 | 0.6 |
| Redis | 0.917 | 0.0 | 0.75 | 1.0 | 1.0 |
| kubelet | 0.364 | 0.0 | 0.273 | 0.182 | 0.182 |


### Wrong predictions by category

|  | drain | base_zeroshot | base_fewshot | ft_r16 | ft_r16_cap10 |
|---|---|---|---|---|---|
| format | 0 | 36 | 22 | 3 | 1 |
| hallucinated | 0 | 36 | 6 | 1 | 1 |
| under-generalised | 32 | 2 | 7 | 15 | 14 |
| over-generalised | 7 | 4 | 6 | 10 | 11 |
| other | 7 | 1 | 4 | 8 | 5 |


### ft_r16 vs base_fewshot: fixed 17, broke 9 of 84 lines


**Fixed** (first 20 of 17, one per distinct gold)

- `nginx/1.31.7`
  - gold `nginx/<*>`
  - ft_r16 `nginx/<*>`  /  base_fewshot `<*>/<*>`
- `Redis version=7.4.10, bits=64, commit=00000000, modified=0, pid=1, just started`
  - gold `Redis version=<*>, bits=<*>, commit=<*>, modified=<*>, pid=<*>, just started`
  - ft_r16 `Redis version=<*>, bits=<*>, commit=<*>, modified=<*>, pid=<*>, just started`  /  base_fewshot `Redis version=<> , bits=<> , commit=<> , modified=<> , pid=<> , just started`
- `Running mode=standalone, port=6379.`
  - gold `Running mode=<*>, port=<*>.`
  - ft_r16 `Running mode=<*>, port=<*>.`  /  base_fewshot `Running mode=standalone, port=<>`
- `Done loading RDB, keys loaded: 1, keys expired: 0.`
  - gold `Done loading RDB, keys loaded: <*>, keys expired: <*>.`
  - ft_r16 `Done loading RDB, keys loaded: <*>, keys expired: <*>.`  /  base_fewshot `Done loading RDB, keys loaded: <*>, keys expired: <*>`
- `relation "nope" does not exist at character 15`
  - gold `relation "<*>" does not exist at character <*>`
  - ft_r16 `relation "<*>" does not exist at character <*>`  /  base_fewshot `relation "<>" does not exist at character <*>`
- `listening on IPv6 address "::", port 5432`
  - gold `listening on IPv6 address "<*>", port <*>`
  - ft_r16 `listening on IPv6 address "<*>", port <*>`  /  base_fewshot `listening on IPv6 address "<::>", port <*>`
- `[ControllerServer id=1] Waiting for all of the authorizer futures to be completed`
  - gold `[ControllerServer id=<*>] Waiting for all of the authorizer futures to be completed`
  - ft_r16 `[ControllerServer id=<*>] Waiting for all of the authorizer futures to be completed`  /  base_fewshot `[ControllerServer id=<>] Waiting for all of the authorizer futures to be completed`
- `[LogLoader partition=__consumer_offsets-13, dir=/tmp/kraft-combined-logs] Loading producer state til`
  - gold `[LogLoader partition=<*>, dir=<*>] Loading producer state till offset <*> with message format versio`
  - ft_r16 `[LogLoader partition=<*>, dir=<*>] Loading producer state till offset <*> with message format versio`  /  base_fewshot `[LogLoader partition=<>-<*>, dir=<>] Loading producer state till offset <*> with message format vers`
- `[MetadataLoader id=1] maybePublishMetadata(LOG_DELTA): The loader finished catching up to the curren`
  - gold `[MetadataLoader id=<*>] maybePublishMetadata(LOG_DELTA): The loader finished catching up to the curr`
  - ft_r16 `[MetadataLoader id=<*>] maybePublishMetadata(LOG_DELTA): The loader finished catching up to the curr`  /  base_fewshot `[MetadataLoader id=<>] maybePublishMetadata(LOG_DELTA): The loader finished catching up to the curre`
- `[AdminClient clientId=adminclient-1] Connection to node -1 (/172.17.0.1:1) could not be established.`
  - gold `[AdminClient clientId=<*>] Connection to node <*> (<*>) could not be established. Node may not be av`
  - ft_r16 `[AdminClient clientId=<*>] Connection to node <*> (<*>) could not be established. Node may not be av`  /  base_fewshot `[AdminClient clientId=adminclient-1] Connection to node <*> (/ <*>:<*>) could not be established. No`
- `Loaded [ad_ldap_logtype.json] log type`
  - gold `Loaded [<*>] log type`
  - ft_r16 `Loaded [<*>] log type`  /  base_fewshot `Loaded [<>] log type`
- `level=info msg="started new containerd process" address=/var/run/docker/containerd/containerd.sock m`
  - gold `level=info msg="started new containerd process" address=<*> module=libcontainerd pid=<*>`
  - ft_r16 `level=info msg="started new containerd process" address=<*> module=libcontainerd pid=<*>`  /  base_fewshot `level=info msg="started new containerd process" address=<> module=libcontainerd pid=<>`
- `level=info msg="cleaning up dead shim" namespace=moby`
  - gold `level=info msg="cleaning up dead shim" namespace=moby`
  - ft_r16 `level=info msg="cleaning up dead shim" namespace=moby`  /  base_fewshot `level=info msg="cleaning up dead shim" namespace=<>`
- `level=info msg="shim disconnected" id=752289f59f6b2e98bb978d9dd943bff355d405939ec6ad8db2841952194f40`
  - gold `level=info msg="shim disconnected" id=<*> namespace=moby`
  - ft_r16 `level=info msg="shim disconnected" id=<*> namespace=moby`  /  base_fewshot `level=info msg="shim disconnected" id=<> namespace=<>`
- `level=error msg="Not continuing with pull after error: manifest unknown: manifest unknown"`
  - gold `level=error msg="Not continuing with pull after error: manifest unknown: manifest unknown"`
  - ft_r16 `level=error msg="Not continuing with pull after error: manifest unknown: manifest unknown"`  /  base_fewshot `level=error msg="Not continuing with pull after error: <*>"`
- `level=info msg="starting containerd" revision=bcc810d6b9066471b0b6fa75f557a15a1cbf31bb version=v1.7.`
  - gold `level=info msg="starting containerd" revision=<*> version=<*>`
  - ft_r16 `level=info msg="starting containerd" revision=<*> version=<*>`  /  base_fewshot `level=info msg="starting containerd" revision=<> version=<>`
- `level=warning msg="cleaning up after shim disconnected" id=752289f59f6b2e98bb978d9dd943bff355d405939`
  - gold `level=warning msg="cleaning up after shim disconnected" id=<*> namespace=moby`
  - ft_r16 `level=warning msg="cleaning up after shim disconnected" id=<*> namespace=moby`  /  base_fewshot `level=warning msg="cleaning up after shim disconnected" id=<> namespace=<>`

**Broke** (first 20 of 9, one per distinct gold)

- `{"time":"2026-10-19T16:32:19+00:00","remote":"192.168.65.1","method":"GET","uri":"/","status":200,"b`
  - gold `{"time":"<*>","remote":"<*>","method":"<*>","uri":"<*>","status":<*>,"bytes":<*>,"rt":<*>}`
  - ft_r16 `{"time":"<*>","remote":"<*>","method":"GET","uri":"/","status":<*>,"bytes":<*>,"rt":<*>}`  /  base_fewshot `{"time":"<*>","remote":"<*>","method":"<*>","uri":"<*>","status":<*>,"bytes":<*>,"rt":<*>}`
- `checkpoint starting: immediate force wait`
  - gold `checkpoint starting: immediate force wait`
  - ft_r16 `checkpoint starting: <*> <*> wait`  /  base_fewshot `checkpoint starting: immediate force wait`
- `Exception in thread "main" org.apache.kafka.common.config.ConfigException: If using process.roles, c`
  - gold `Exception in thread "main" org.apache.kafka.common.config.ConfigException: If using process.roles, c`
  - ft_r16 `Exception in thread "<main>" org.apache.kafka.common.config.ConfigException: If using process.roles,`  /  base_fewshot `Exception in thread "main" org.apache.kafka.common.config.ConfigException: If using process.roles, c`
- `joptsimple.UnrecognizedOptionException: timeout is not a recognized option`
  - gold `joptsimple.UnrecognizedOptionException: <*> is not a recognized option`
  - ft_r16 `joptsimple.UnrecognizedOptionException: timeout is not a recognized option`  /  base_fewshot `joptsimple.UnrecognizedOptionException: <*> is not a recognized option`
- `Loaded [429] field mapping docs successfully!`
  - gold `Loaded [<*>] field mapping docs successfully!`
  - ft_r16 `Loaded <*> field mapping docs successfully!`  /  base_fewshot `Loaded [<*>] field mapping docs successfully!`
- `loaded plugin [opensearch-ml]`
  - gold `loaded plugin [<*>]`
  - ft_r16 `loaded plugin [opensearch-ml]`  /  base_fewshot `loaded plugin [<*>]`
- `Exception in thread "main" java.lang.RuntimeException: starting java failed with [1]`
  - gold `Exception in thread "main" java.lang.RuntimeException: starting java failed with [<*>]`
  - ft_r16 `Exception in thread "<main>" java.lang.RuntimeException: starting java failed with [<*>]`  /  base_fewshot `Exception in thread "main" java.lang.RuntimeException: starting java failed with [<*>]`
- `kubelet.go:1011] "ClusterTrustBundle informer will be started eventually once a trust bundle is requ`
  - gold `kubelet.go:<*>] "ClusterTrustBundle informer will be started eventually once a trust bundle is reque`
  - ft_r16 `kubelet.go:<*> "ClusterTrustBundle informer will be started eventually once a trust bundle is reques`  /  base_fewshot `kubelet.go:1011] "ClusterTrustBundle informer will be started eventually once a trust bundle is requ`
