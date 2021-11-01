So now I have this block store in algorand, right?  Each block of data is 'just' a stateful app that loads up the program's scratch buffers with literal data and then exits.  I've been having fun with this.. I can stash whole movies in there and stream them back.  Whoopee.  But can we create a data-bearing application that can only be modified according to certain rules?  A good start would be appending.. then perhaps we could have guest books and things.  I think it can be done, because transaction groups are crazy powerful.  Basically we can sandwich an application update transaction between two calls to the application, and then approve the group based on a comparison between the original call and the call to the updated txn. It could even be simpler maybe? The append could be an argument to an application update transaction, the update call itself would load the scratch buffers for the original program, and the subsequent call to the updated app validates that the updated app has been modified so as to represent the original buffer's content plus the content of the argument to the call.  And it can all be bolted down super well, because transactions in a group can all see each other perfectly and decide to fail based on literally any information in them.

This whole flow wasn't possible until pretty recently btw-- Teal v4 was necessary to observe the scratch space of other apps in the group, and it came out in like July.

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
* self host this project on-chain and GTFO github forever plzkthx.
* design the smallest possible shell script that can bootstrap this software from the chain (might need stages).

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
Email.  Usenet. Web.  Napster.  BitTorrent.   These protocols and their implementations represent a kind of public digital infrastructure, available for use without ceremony; like a park bench or a fruit tree.  Network and regulatory conditions define the ecosystem in which these protocols must survive if they are to remain infrastructure.   Changes in these can render the infrastructure obsolete, broken, or captured (each of which failure mode is well worth further discussion).

Suppose that the algorand blockchain is public digital infrastructure performing the function of data storage and state synchronization.  Might it in fact be pretty good at that?  It's hard to know-- historically, challenges to digital infrastructure present themselves only at large user/time scales.  Some experiment must be made and grown in order to determine the suitability of algorand for public use.  As the system scales, its qualities will be shown by its availablity to deliver utility while avoiding being broken, captured, or obsoleted.

Before developing implementations and protocols atop Algorand, we want to understand what algorand might be good at, and how the environment might signal that goodness to us.  The price of data storage in the network is interesting in this regard.  Network consensus parameters as of August '21 give the minimum balance that must be maintained for an account to control the largest possible stateful application as .4 Algos; around 60 cents.  We can store around 5k of data in that application.  So for a deposit of around ten cents per kilobyte, a user is promised indefinite data durability, dozens of replicas, access via a public-facing API, and the ability to prove ownership of that data.  The user can also involve that data in consensus computations, but it's not clear today what benefit that will provide.  Probably some, right?

Something else too-- something I'm not sure how to say.  I feel like at least some cryptocurrencies can be priced according to the cost of running them, and that the correct price for a very good cryptocurrency might be very low, given fixed transaction fees. 

Like, suppose I want to run a decentralized anonymous forum via a dApp.  The dApp needs to store lots of data on-chain, so it is expensive to run in MainNet.  Like I said, ten cents per kilobyte.  But if the forum has its own dedicated blockchain, its operators can give away megabytes of storage for the 'price' of a CAPTCHA solve.  With four second transaction finality, things are starting to look pretty good for all kinds of fun dApps.. web forums, craps, a space merchant clone.. reddit clones, twitter clones.. I gotta ask: why isn't this stuff up and running?  I have a good answer: lack of oxygen.  These fun dApp projects are like open source software:  Rather than capturing value for the software creators, they tend to take private value and capture it in public: a dApp forum in a private chain you can host yourself.. who makes money off of that?   But of course people do make open source software.. so why aren't there any big fun open source dApps?  I think it's because dApp developers don't understand the stuff I was saying about coin prices.  See, I think low coin prices are good. They think high coin prices are good-- they aim for and expect it.  Which naturally means they will buy the coins they develop for.  That means they want to write for mainnet, where cost of use is highest.  That means they want to keep data and coordination off-chain.. which seems like a shame.  It seems like so little has been done with 'pure' distributed state consensus applications.  Granted even very simple applications are pretty hard to write.. but that's what makes it fun!!

OR 

The best non-fungible tokens of all were the friends we made along the way.

OR 
These days, a unit of cryptocurrency is treated like a share in a company.. but that's not the nature of the fundamental value of a unit of cryptocurrency. A share in a company entitles its holder to some of the dividends accrued on the capital owned collectively by shareholders.  A unit of cryptocurrency entitles its holder to access to some of the capital owned collectively by token holders.

Just like the fundamental source of value of fiat currency is its ability to pay taxes, the fundamental source of value of a cryptocurrency is its ability to pay transaction fees, which fees have the singular purpose of durably mutating data in a public consensus network.

-

a representation of a thing is not the thing itself (data is not physical)
a link to a representation of a thing is not a representation of a thing (links don't guarantee availability.)