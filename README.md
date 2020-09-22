exit# isaacbot
########################################################################################################################
Isaac the Record Maester, a Discord bot for the game Gloomhaven

    by old beans
    v1.0
 
https://airtable.com/tblbXt5WRf7KqxGmG/viweFT3qDphUWO2ZG?blocks=hide
https://github.com/old-beans/Isaac-GH-discordbot

A Discord bot for the game Gloomhaven. Players can use text commands to update player and world state.
Data stored in Airtable.

Current commands:

Greetings!  I am Isaac-Bot, the Record Keeper of Gloomhaven. 
Please select from the following commands  


!stats *Xxp *Ygp *Zch     Update the author's stats
NEW -- Use a '+' in front of any cost to ADD to your current toal. eg !stats +12xp             
Mix Additions and Totals eg '!stats +24xp 49g +1ch'

!gain/add          Add X to the author's current total
NEW -- eg !gain 25xp; !lose 1ch; !gain 1ch
Only one stat at a time this way

!lose/remove Xxp/Xgp/Xch/item X/ ability X

!donate                   Transfers 10 gold from author to the Sanctuary

!buy X, *Y                Purchase item X for (Cost - Discount)gp
!sell X, *Y               Sell item X for (Cost/2)gp

!levelup X, *Y            Add Ability card X to author's pool
NEW -- Add multiple abilities separated by a space

!loot X                   Unlock one copy and add it to character inventory for 0gp
NEW -- Use to unlock items eg Scenario Loot or Reward, City/Road events, 
!loot X design            Unlock all copies and adds them to store inventory
NEW -- Use to unlock Random Item Design rewards

!ability X lose/remove    Remove ability X from your pool
!ability list             Display list of Lvl 2+ abilities in character pool

!item X gain/add          Add item X to author's inventory
    Item must be unlocked, otherwise '!loot X' should be used
!item X remove/lose       Remove item X from author's inventory
!item X details           Displays information for item X
!item list                Display a list of items in character inventory

!teamstats                Get Donations, Prosperity, and Reputation
!gain/lose pros           Check 1 box on Prosperity track
Automatically checks for Overall Prosperity increase and unlocks new items
!gain/lose rep            Add 1 reputation for the author's party


!discover/unlock X "Name" "Description"    Unlockss a new scenario and updates Name and Description
NEW -- Name and Description must be separately wrapped in quotes
!complete X               Mark a scenario complete
!scenario X details       Shows info and details about the scenario
!scenario X description   Update the description for scenario X


##########################################################################################################################


Future Commands/Features:

Use @mention to perform an command on another player/character 

!retire
Make character retired. Update quest and date retired.

!newcharacter
Create a new character with Name, Class, and gold/xp calculated from prosperity

!gain perk
!lose perk




