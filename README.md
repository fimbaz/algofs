## AlgoFS
### Wut
Treat algorand like s3
### Y
find the price of storage in this network
### how
jam ~8k into a stateful application, then do filesystem things until someone gets mad.
### wont that get expensive?
Txn costs should stay reasonable.. In terms of locked funds, yeah maybe.  Hopefully the cost of algorand goes down.  Could use a private network too!
### Done already:
* ~8k block read/write
### Want:
* multiblock objects
* named multiobject storage
* infinite scale

### Hacks:
need the developer API to use this at all-- we dry-run execute the smart contract to read the data.

### Demo:
```
(.venv) fimbaz@kolombus:~/algofs$ python block.py write foon                                                                                                                                                                                                                                 
Waiting for confirmation                                               
11 

(.venv) fimbaz@kolombus:~/algofs$ python block.py read 11                                                                                                                                                                                                                                    
────────▓▓▓▓▓▓▓────────────▒▒▒▒▒▒                                      
──────▓▓▒▒▒▒▒▒▒▓▓────────▒▒░░░░░░▒▒                                    
────▓▓▒▒▒▒▒▒▒▒▒▒▒▓▓────▒▒░░░░░░░░░▒▒▒                                  
───▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▒▒░░░░░░░░░░░░░░▒                                 
──▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░░▒                                
──▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░░░▒                               
─▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░░░░▒                              
▓▓▒▒▒▒▒▒░░░░░░░░░░░▒▒░░▒▒▒▒▒▒▒▒▒▒▒░░░░░░▒                              
▓▓▒▒▒▒▒▒▀▀▀▀▀███▄▄▒▒▒░░░▄▄▄██▀▀▀▀▀░░░░░░▒                              
▓▓▒▒▒▒▒▒▒▄▀████▀███▄▒░▄████▀████▄░░░░░░░▒                              
▓▓▒▒▒▒▒▒█──▀█████▀─▌▒░▐──▀█████▀─█░░░░░░▒                              
▓▓▒▒▒▒▒▒▒▀▄▄▄▄▄▄▄▄▀▒▒░░▀▄▄▄▄▄▄▄▄▀░░░░░░░▒                              
─▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░░░▒                               
──▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░░▒                                
───▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▀▀▀░░░░░░░░░░░░░░▒                                 
────▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░▒▒                                  
─────▓▓▒▒▒▒▒▒▒▒▒▒▄▄▄▄▄▄▄▄▄░░░░░░░░▒▒                                   
──────▓▓▒▒▒▒▒▒▒▄▀▀▀▀▀▀▀▀▀▀▀▄░░░░░▒▒                                    
───────▓▓▒▒▒▒▒▀▒▒▒▒▒▒░░░░░░░▀░░░▒▒                                     
────────▓▓▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░▒▒                                      
──────────▓▓▒▒▒▒▒▒▒▒▒░░░░░░░░▒▒                                        
───────────▓▓▒▒▒▒▒▒▒▒░░░░░░░▒▒                                         
─────────────▓▓▒▒▒▒▒▒░░░░░▒▒                                           
───────────────▓▓▒▒▒▒░░░░▒▒                                            
────────────────▓▓▒▒▒░░░▒▒                                             
──────────────────▓▓▒░▒▒                                               
───────────────────▓▒░▒                                                
────────────────────▓▒                                                 


```

### Motiviation
Email.  Usenet. Napster.  BitTorrent.   These protocols and their implementations represent a kind of public digital infrastructure, available for use without ceremony; like a park bench or a fruit tree.  Network and regulatory conditions define the ecosystem in which these protocols must survive if they are to remain infrastructure.   Changes in these can render the infrastructure either non-functional (broken) or render some of its benefits uavailable to a portion of its intended audience (capture). 

Suppose that the algorand blockchain is public digital infrastructure performing the function of data storage and state synchronization.  Might it in fact be pretty good at that?  It's hard to know-- historically, challenges to digital infrastructure present themselves only at large user/time scales.  Some experiment must be made and grown in order to determine the suitability of algorand for public use.  As the system scales, its qualities will be shown by its availablity to deliver utility at scale while avoiding being broken or captured.

Demonstrations that could be grown to show the properties of this infrastructure:
* Something like Usenet
* Something like Email
* Something like Napster
