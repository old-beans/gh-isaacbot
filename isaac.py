# Isaac the Record Master
# Discord bot 


import discord, fstrings, re, random, os
from dotenv import load_dotenv
load_dotenv()
from airtable import Airtable
from discord.ext import commands
from datetime import datetime
from gh import World, Scenario, Party, Character, Item, Ability

# perks_airtable = Airtable(AIRTABLE_BASE_KEY, perks_sheet) # perks record lookup


DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')  # stored in .env
bot = commands.Bot(command_prefix = "!", help_command = None)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(name='Test'))
    print('Logged in as {0.user}'.format(bot))




@bot.command(aliases=['Help'])
async def help(ctx):
# Get list of possible actions. alternative to !help

    
    message = f"""
Greetings!  I am Isaac-Bot, the Record Keeper of Gloomhaven. 
Please select from the following commands  {"* = Optional":>}

!stats *Xxp *Ygp *Zch     {"Update the author's stats":.<24}
NEW -- Use a '+' in front of any cost to ADD to your current toal. eg !stats +12xp             
NEW -- Mix Additions and Totals eg '!stats +24xp 49g +1ch'

!gain/add XYZ  {"Add to the author's current total":.<24}
!lose/remove XYZ  {"Add to the author's current total":.<24}
NEW -- XYZ can be any one of the following - Xxp, Xgp, Xch, item X, ability X

!levelup X, *y            {"Add Ability card x to author's pool":.<24}

!donate                   {"Transfers 10 gold from author to the Sanctuary":.<24}

!buy X, *Y                {"Purchase item X and update gold, store":.<24}
!sell X, *Y               {"Sell item X and update gold, store":.<24}

!loot X                   {"Unlock one copy and add it to character inventory for 0gp":.<24}
!loot X design            {"Unlock all copies and adds them to store inventory":.<24}

!ability list             {"Display list of Lvl 2+ abilities in character pool":.<24}

!item list                {"Display a list of item in character inventory":.<24}
!item X details           {"Displays details for item X"}

!teamstats                {"Get Donations, Prosperity, and Reputation"}
!gain/lose pros           {"Check 1 box on Prosperity track":.<24}
  Automatically checks for Overall Prosperity increase and unlcoks new itemsx
!gain/lose rep            {"Add 1 reputation for the author's party":.<24}


!discover/unlock X "Name" "Description"    {"Unlockss a new scenario and updates Name and Description":.<24}
  Name and Description must be separately wrapped in quotes
!complete X               {"Mark a scenario complete":.<24}
!scenario X details       {"Shows info and details about the scenario":.<24}
!scenario X description   {"Update the description for scenario X":.<24}
"""

    await ctx.send(f"```{message}```")


@bot.command(aliases=["getall","worldstats","campaignstats","partystats"])
async def teamstats(ctx):
    author = ctx.message.author.name
    character = Character(author)
    world = World(character.campaign[0])
    party = Party(character.party[0])

    message = f"""{world.name}:   
  {f"{world.donations}gp donated":.<18}+1 prosperity at {world.calc_donations_needed()}gp
  {f"Prosperity {world.prosperity}":.<18}{world.pticks}/{world.prosperity_levels[world.prosperity]}

{party.name}:
  {f"Reputation: {party.reputation}":.<18}Discount: {party.discount}"""
# Global Achievements: {world.achievements}
# Party Achievements: {party.achievements}""")
    
    await ctx.send(f"```{message}```")


@bot.command(aliases=["donation","makedonation"])
async def donate(ctx):
    #Adds a donation to the total and asjusts player gold.
    #+1 propserity tick when appropriate
    #+1 overall prosperity when appropriate
    #Updates overall propserity when applicable
    author = ctx.message.author.name
    character = Character(author)
    world = World(character.campaign[0])

    # Not enough gold
    if character.gold < 10:

        message = f"You only have {character.gold}. Better pick up some more goin in the next battle, or check your stats."
            

    else:
        
        character.gain_gold(-10)

        world.donate()
        
        message = f"The Sanctuary of the Great Oak thanks you. Have a blessed battle!\nDonations: {world.donations}......{character.name}: {character.gold} gold left"


        if world.donations in world.donation_levels:

            if world.donations == 100:

                message = f"{message}\n\nThe Sanctuary has received a total of 100 gold in donations.\nPlease open Envelope B."

            world.gain_prosperity()
            
            message = f"{message}\n\n+1 prosperity......{world.pticks}/{world.prosperity_levels[world.prosperity]}"

            if world.pticks == world.prosperity_levels[world.prosperity - 1]:

                message = f"{message}\n\n*The Overall Prosperity has increased to {world.prosperity}*\nNew items are now available in the item store.\nAll characters may level up to Lvl{world.prosperity} while in Gloomhaven."
                            

    await ctx.send(f"```{message}```")


@bot.command(aliases=['add'])
async def gain (ctx, thing_to_gain, *thing):
    author = ctx.message.author.name
    character = Character(author)
    world = World(character.campaign[0])
    party = Party(character.party[0])

    parse_gain(thing_to_gain, *thing)

    if thing_to_gain == 'item':
        item_num = thing[0].strip(',')
        
        item = Item(item_num)
        
        if item.unlocked == True:

            if item.number not in character.item_nums:

                if item.numberAvailable > 0:

                    character.item_transaction('gain', item.number)

                    message = f"{character.name} gained {item.num_name}.\n  Items: {character.item_nums}"

                else:

                    message = f"There are no copies of {item.num_name} available in the store."

            else:

                message = f"You already own {item.num_name}! You cannot own two copies.I should striek you down right here, so help me Blood God!"
        else:

            message = f"Item {item.number} is not unlocked. Use !loot to add scenario loot or items unlocked via road or city event."

    elif thing_to_gain == 'ability':
        if len(character.abilities) < character.lvl - 1:
            ability_num = thing[0].strip(',')
            ability = Ability(ability_num)

            if character.lvl < int(ability.lvl):

                message = f"That card ({ability.lvl}) is above your level. Please select an ability of Level {character.lvl} or lower to add to your pool."

            else:

                if character.charclass != ability.charclass:

                    message = f"Please choose an ability card from your own dang class."

                else: 

                    if ability.ability['id'] in character.abilities:

                        message = f"Ability {ability.number} is already in your pool. Please choose again."

                    else:

                        character.abil_transaction('gain', ability.number)

                        message = f"Level {ability.lvl} - {ability.name} [{ability.number}] added to your pool.\nAbilities: {sorted(character.abil_nums)}"
        else:
            message = f"You have added too many abilities. You are Level {character.lvl} so you can only have {character.lvl-1} level 2+ abilities in your pool."

    elif 'rep' in thing_to_gain:

        party.gain_reputation()

        message = f"{party.name} +1 Reputation:\nReputation: {party.reputation}    Discount: {party.discount}"

    elif 'pros' in thing_to_gain:

        world.gain_prosperity()

        message = f"{world.name} +1 Prosperity:\nProsperity: {world.pticks}/{world.prosperity_levels[world.prosperity]}    Overall: {world.prosperity}"

        if world.pticks == world.prosperity_levels[world.prosperity - 1]:

            message = f"{message}\nThe Overall Prosperity has increased to {world.prosperity}\nNew items are now available in the item store.\nAll characters may level up to Lvl{world.prosperity} while in Gloomhaven."

    elif 'xp' in thing_to_gain:
        
        xp = int(re.sub("[^0-9]", "", thing_to_gain))
        
        lvl_up = character.gain_xp(xp)

        message = f"{character.name} gained {xp}xp\n{character.xp}xp {character.gold}gp {character.checks}{character.ch}"
        
        
        if lvl_up == True:

            message = f"{message}\nYou reached Level {character.lvl}! You may level up when you return to Gloomhaven."

    elif 'gold' in thing_to_gain or 'gp' in thing_to_gain:

        gold = int(re.sub("[^0-9]", "", thing_to_gain))

        character.gain_gold(gold)

        message = f"{character.name} gained {gold}gp\n{character.xp}xp {character.gold}gp {character.checks}{character.ch}"

    elif 'ch' in thing_to_gain:
        
        checks = int(re.sub("[^0-9]", "", thing_to_gain))

        character.gain_checks(checks)
        
        message = f"{character.name} gained {checks}checks\n{character.xp}xp {character.gold}gp {character.checks}{character.ch}"
        
        if character.checks % 3 == 0:

            message = f"{message}\nYou earned your 3rd check. Gain a Perk!"

    await ctx.send(f"```{message}```")


@bot.command(aliases=['remove'])
async def lose(ctx, thing_to_lose, *, things):
    author = ctx.message.author.name
    character = Character(author)
    world = World(character.campaign[0])
    party = Party(character.party[0])

    if thing_to_lose == 'item':
        item_num = thing[0].strip(',')

        item = Item(item_num)
        
        if int(item.number) in character.item_nums:

            character.item_transaction('lose', item.number)

            message = f"Item {item.number} has been removed from your inventory.\nItems: {sorted(character.item_nums)}"

        else:
            
            message = f"You don't own that item. Please try again.\nItems: {sorted(character.item_nums)}"

    elif thing_to_lose == 'ability':
        ability_num = thing[0].strip(',')
        ability = Ability(ability_num)

        if int(ability.number) in character.abil_nums:
            
            character.abil_transaction('lose', ability.number)

            message = f"Ability {ability.number} has been remove from your pool.\nAbilities: {sorted(character.abil_nums)}"

        else:
            message = f"That ability is not in your pool.\nAbilities: {sorted(character.abil_nums)}"

    elif 'pros' in thing_to_lose:


        if world.pticks in world.prosperity_levels:

            message = f"You're in luck. Prosperity cannot be descreased below its current cost."


        else: 

            world.lose_ptick()

            message = f"{world.name} -1 Prosperity\nProsperity: {world.pticks}/{world.prosperity_levels[world.prosperity]}    Overall: {world.prosperity}"

    elif 'rep' in thing_to_lose:


        party.lose_reputation()

        message = f"{party.name} -1 Reputation\nReputation: {party.reputation}     Discount: {party.discount}"

    elif 'xp' in thing_to_lose:
        
        xp = int(re.sub("[^0-9]", "", thing_to_lose))
        
        lvl_up = character.gain_xp(-xp)

        message = f"{character.name} lost {xp}xp\n{character.xp}xp {character.gold}gp {character.checks}{character.ch}"
        
        
        if lvl_up == True:

            message = f"{message}\nYou reached Level {character.lvl}! You may level up when you return to Gloomhaven."

    elif 'gold' in thing_to_lose or 'gp' in thing_to_lose:

        gold = int(re.sub("[^0-9]", "", thing_to_lose))

        character.gain_gold(-gold)

        message = f"{character.name} lost {gold}gp\n{character.xp}xp {character.gold}gp {character.checks}{character.ch}"

    elif 'ch' in thing_to_lose:
        
        checks = int(re.sub("[^0-9]", "", thing_to_lose))

        if character.checks % 3 == 0:

            message = f"You cannot lose a check because it would break up a compelte triplet."
        
        else:
            
            character.gain_checks(-checks)
        
            message = f"{character.name} lost {checks}checks\n{character.xp}xp {character.gold}gp {character.checks}{character.ch}"


    await ctx.send(f"```{message}```")


@bot.command()
async def stats(ctx, *stats_to_update):
    # get or update character stats by Discord username
    # update requires this format in Discord "!stats 100xp 100gp 100ch"
    # def choose_char():
    author = ctx.message.author.name
    character = Character(author)

    if len(stats_to_update) > 0:

        for stat in stats_to_update:

            if 'x' in stat:                

                xp = int(re.sub("[^0-9]", "", stat))

                if '+' in stat:

                    lvl_up = character.gain_xp(xp)
                    character = Character(author)

                else:

                    lvl_up = character.change_xp(xp)
                    character = Character(author)


                if lvl_up == True:

                    await ctx.send(f"You reached Level {character.lvl}! You may level up when you return to Gloomhaven.")


            if 'g' in  stat:                

                gold = int(re.sub("[^0-9]", "", stat))

                
                if '+' in stat:

                    character.gain_gold(gold)

                        
                else:

                    character.change_gold(gold)

                

            if 'ch' in stat:                

                checks = int(re.sub("[^0-9]", "", stat))

                
                if '+' in stat:

                    character.gain_checks(checks)

                    
                else:
                    
                    character.change_checks(checks)

                            
                if character.checks % 3 == 0:

                    await ctx.send(f"You earned your 3rd check. Gain a Perk!")
            

    message = f"""{character.name} -- Lvl {character.lvl} -- {character.charclass}
    {character.xp}xp  -  {character.gold}gp  -  {character.checks}{character.ch}
 Abilities: {sorted(character.abil_nums)}
 Items:     {sorted(character.item_nums)}"""
        
    await ctx.send(f"```{message}```")


@bot.command()
async def levelup(ctx, *abil_nums):
    author = ctx.message.author.name
    character = Character(author)
    ch_abil_count = len(character.abilities)

    for abil_num in abil_nums:
        if ch_abil_count < character.lvl - 1:
            abil_num = abil_num.strip(',')
            ability = Ability(abil_num)

            if character.lvl < int(ability.lvl):

                message = f"That card ({ability.lvl}) is above your level ({character.lvl}). You must select a card of your current level or lower.\n Abilities: {character.abil_nums}"

            else:

                if character.charclass != ability.charclass:
                    message = f"Please choose an ability card from your own dang class."

                else:

                    if ability.ability['id'] in character.abilities:
                        
                        message = f"Ability {ability.number} is already in your pool. Please choose again.\n Abilities: {character.abil_nums}"
                    
                    else:

                        character.abil_transaction('gain', abil_num)
                        ch_abil_count += 1
                        message = f"Level {ability.lvl} - {ability.name} [{ability.number}] added to your pool."

        else:
            message = f"You have added too many abilities. You are Level {character.lvl} so you can only have {character.lvl-1} level 2+ abilities in your pool."
        await ctx.send(f"```{message}```")

    await ctx.send(f"```{character.name}\n Abilities: {sorted(character.abil_nums)}```")


@bot.command(aliases=['show', 'list', 'get'])
async def display(ctx, option):
    author = ctx.message.author.name
    character = Character(author)

    if option == 'abilities':
        
        message = f"{character.name} -- Lvl {character.lvl} -- {character.charclass}"

        for abil in sorted(character.abil_nums):

            abil = Ability(abil)

            message += f"\n {abil.num_name:35} {abil.number}"
            

    elif option == 'items':
        
        message = f"{character.name} -- Lvl {character.lvl} -- {character.charclass}"

        for item in sorted(character.item_nums):

            item = Item(item)

            message += f"\n {item.num_name}"

    elif option == 'fullstats':


        message = f"{character.name} -- Lvl {character.lvl} -- {character.charclass}\n    {character.xp}xp  -  {character.gold}gp  -  {character.checks}{character.ch}\n Abilities:"

        for item in sorted(character.item_nums):

            item = Item(item)

            message += f"\n  {item.num_name:35} {item.cost}gp"

        message = f"{message}\n Items:"

        for abil in sorted(character.abil_nums):

            abil = Ability(abil)

            message += f"\n  {abil.num_name:35} {abil.number}"        


    await ctx.send(f"```{message}```")


@bot.command(aliases=['abil'])
async def ability(ctx, ability_num):
    # command input !ability X
    # adds selected abilities to the character pool
    # You can only add one at a time
    author = ctx.message.author.name
    character = Character(author)

    ability = Ability(ability_num)

    if ability.lvl <= character.lvl:

        message = f"{ability.number}: {ability.name} -- {ability.charclass} Lvl {ability.lvl}"

    else:

        message = f"That ability is above your level. You can't see it until you earn it."

    await ctx.send(f"```{message}```")

@bot.command()
async def item(ctx, item_num):
    # command input !item X
    # adds selected abilities to the character pool
    # You can only add one at a time
    author = ctx.message.author.name
    character = Character(author)
    party = Party(character.party[0])
    world = World(character.campaign[0])

    item = Item(item_num)

    if item.unlocked == True:

        message = f"{item.num_name} -- {item.cost}gp\n{item.description}\n  Current stock: {item.numberAvailable}\n  Known copies: {item.maxCount}"

    else:

        message = "We don't have that item. Never even heard of it. Let us know if you find one!"


    await ctx.send(f"```{message}```")


@bot.command(aliases=['scene','scen'])
async def scenario(ctx, scene_no, *action_text):
# !scenario 12 unlocked
# !scenario 12 complete We ran away with the treasure
  
    scenario = Scenario(scene_no)
    action_text = list(action_text)

    if 'details' in action_text:

        if scenario.unlocked == False:

            message = f"Scenario {scene_no} has not been discovered yet."    


        elif scenario.unlocked == True and scenario.complete == False:

            message = f"{scene_no}: {scenario.name}"


            if len(scenario.description) > 1: 

                message = f"{scene_no}: {scenario.name}\n{scenario.description}"


        elif scenario.unlocked == True and scenario.complete == True:

            message = f"{scene_no}: {scenario.name} -- Complete"

            if len(scenario.description) > 1:

                message = f"{message}\n{scenario.description}"

    elif 'descr' in action_text[0]:

        del action_text[0]

        description_text = ' '.join(action_text)

        scenario.update_description(description_text)   

        message = f'Your notes about Scenario {scenario.number} have been saved.\n"{description_text}"'

    await ctx.send(f"```{message}```")


@bot.command()
async def buy(ctx, *item_nums):

    author = ctx.message.author.name
    character = Character(author)
    party = Party(character.party[0])

    for item in item_nums:
        item = item.strip(',')
        item = Item(item)

        if item.unlocked == True:
            
            price = item.cost + party.discount
            
            if item.item_rec['id'] not in character.items: 
                
                if item.numberAvailable > 0:

                    if character.gold >= price:

                        character.gain_gold(-price)
                        character.item_transaction('gain', item.number)
                        # item.store_transaction(False)
                        character = Character(author)
                        message = f"{character.name} bought {item.num_name} for {price}gp\n{item.description}"
                        await ctx.send(f"```{message}```")

                    else:
                        message = f"You don't have enough gold. Better pick up some goin in the next battle."
                        await ctx.send(f"```{message}```")
                        
                else: 
                    message = f"We're sold out at the moment. Come back when we get some in stock."
                    await ctx.send(f"```{message}```")
                    
            else:
                message = f"You already own {item.number} according to my ledger. Please try again or perhaps I could interest you in something a little...different?"
                await ctx.send(f"```{message}```")

        else:
            message = f"We don't carry that item. I've heard of them but have never seen a design. If you find one, let us know using the '!loot {item.number}' or '!loot item design {item.number}'."
            await ctx.send(f"```{message}```")

    await ctx.send(f"```Gold:  {character.gold}gp\nItems: {sorted(character.item_nums)}```")


@bot.command()
async def sell(ctx, *item_nums):

    author = ctx.message.author.name
    character = Character(author)

    for item in item_nums:
        item = item.strip(',')
        item = Item(item)
        price = int(item.cost / 2)

        if item.unlocked == True:

            if item.item_rec['id'] in character.items:

                character.item_transaction('lose', item.number)
                character.gain_gold(price)

                message = f"{character.name} sold {item.number}: {item.name} for {price}gp."
                await ctx.send(f"```{message}```")

            else:
                message = f"You don't own that item. Are you trying to pull a fast one, you son of a a bitch??"
                await ctx.send(f"```{message}```")

        else: 
            message = f"You don't own that item. I've never even heard of that. Are you trying to pull one a fast one, you son of a a bitch??"
            await ctx.send(f"```{message}```")

    await ctx.send(f"```Gold:  {character.gold}gp\nItems: {sorted(character.item_nums)}```")


@bot.command()
async def loot(ctx, item_num, *design):

    author = ctx.message.author.name
    
    character = Character(author)
    item = Item(item_num)

    design = list(design)

    if design:

        if item.unlocked == False:

            item.unlock_design()

            item = Item(item_num)

            message = f"Thank you, {character.name}! Our most skilled artisans will get right to work on crafting this...\nIt's Ready.\n{item.num_name} -- {item.cost}gp\n{item.description}"


        elif item.maxCount == item.realMax:

            item = Item(item.number)

            message = f"Thank you, but {item.num_name} is alrady unlocked. Please double check the item number."


    else:
        item.unlock_loot()
        item = Item(item_num)
        if item.number not in character.item_nums:

            character.item_transaction('loot', item.number)

            message = f"""{character.name} looted {item.num_name}! 
 {item.description}
   Gold:  {character.gold}gp
   Items: {sorted(character.item_nums)}"""


        else:

            message = f"{character.name} looted {item.num_name}!\nSince they already own a copy, the item is now available for purchase.\n{item.num_name} -- {item.cost}gp\n{item.description}"


    await ctx.send(f"```{message}```")


@bot.command(aliases=['unlock', 'discover'])
async def discover_scenario(ctx, scene_no, scene_name, scene_description):
    # command input "!unlockscen 1 Black Barrow"
    # multi-word Scene Name's and Descriptions must be wrapped in ""
    scene_no = scene_no.strip(":")
    scenario = Scenario(scene_no)

    # scene_name = ' '.join(scene_name)
    scenario.mark_unlocked(scene_name, scene_description)

    message = f"{scenario.number}: {scenario.name} -- Unlocked\n{scenario.description}"

    await ctx.send(f"```{message}```")


@bot.command(aliases=['complete'])
async def complete_scenario(ctx, scene_no):
    # command input "!completescen 1"

    scenario = Scenario(scene_no)

    if scenario.unlocked == True:

        scenario.mark_complete()

    if scenario.complete == True:

        message = f"{scene_no}: {scenario.name} --  Complete"

    else:

        message = f"You haven't discovered Scenario {scene_no}. Please double-check and try again, or use !unlock."

    await ctx.send(f"```{message}```")




bot.run(DISCORD_TOKEN)




