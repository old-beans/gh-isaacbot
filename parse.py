



def parse_gain(thing_to_gain, *thing):

    actions = {'item':[lose_item(thing), gain_item(thing)],
        'ability':[lose_abili(thing), gain_abili(thing)],
        ['rep','reputation']:[lose_rep(), gain_rep()],
        ['pros', 'prosperity']:[lose_pros(), gain_pros()],
        'xp':[lose_xp(thing), gain_xp(thing)],
        'gp':[lose_gp(thing), gain_xp(thing)],
        'ch': [lose_ch(thing), gain_ch(thing)]}

    actions[thing_to_gain]



def gain_item(thing):

        item_num = thing[0].strip(',')

        gain_item()

        item = Item(item_num)

        if item.unlocked == True:

            if item.number not in character.item_nums:

                if item.numberAvailable > 0:

                    character.item_transaction('gain', item.number)

                    message = f"{character.name} gained {item.num_name}.\n  Items: {character.item_nums}"

                else:

                    message = f"There are no copies of {item.num_name} available in the store."

            else:

                message = f"You already own {item.num_name}! You cannot own two copies.I should strike you down right here, so help me Blood God!"
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


