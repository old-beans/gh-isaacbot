#! python
from airtable import Airtable
import discord, fstrings, re, random, os
from datetime import datetime

# datetime object containing current date and time

AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')  # stored in .env
AIRTABLE_BASE_KEY = os.getenv('AIRTABLE_BASE_KEY')  # stored in .env
CAMPAIGN_NAME = os.getenv('CAMPAIGN_NAME')

campaign_airtable = Airtable(AIRTABLE_BASE_KEY, 'Campaign')
party_airtable = Airtable(AIRTABLE_BASE_KEY, 'Parties')
characters_airtable = Airtable(AIRTABLE_BASE_KEY, 'Characters')    
scenario_airtable = Airtable(AIRTABLE_BASE_KEY, 'Scenarios')
items_airtable = Airtable(AIRTABLE_BASE_KEY, 'Items') # items record lookup
abilities_airtable = Airtable(AIRTABLE_BASE_KEY, 'Character Abilities') # abilities record lookup
classes_airtable = Airtable(AIRTABLE_BASE_KEY, 'Character Classes') # class record lookup
storylines_airtable = Airtable(AIRTABLE_BASE_KEY, 'Storylines')
players_airtable = Airtable(AIRTABLE_BASE_KEY, 'Players')
achievements_airtable = Airtable(AIRTABLE_BASE_KEY, 'Achievements')

class Player:
    character_levels = (0,45,95,150,210,275,345,420,500) 
    prosperity_levels = (0,4,9,15,22,30,39,50,64)


    def __init__(self, author):
        self.name = author
        self.player_rec = players_airtable.match('name', author)
    
    def activate_character(self, ch_name):
        character_rec = characters_airtable.match('name', ch_name)
        characters_airtable.update(character_rec['id'], {'discordUsername': [self.player_rec['id']], 'isActive': True})

    def create_character(self, ch_name, ch_class):
        self.world = World(campaign_airtable.match('name', 'Camp Pain')['id'])
        self.party = Party(party_airtable.match('name', 'Wyld Stallyns')['id'])
        prosperity = self.world.prosperity
        xp = self.character_levels[prosperity]
        gold = (prosperity + 1) * 15
        charclass = classes_airtable.match('name', ch_class)['id']
        characters_airtable.insert(
            {
                'name': ch_name, 'xp': xp, 'gold': gold, 'checks': 0, 'class': [charclass], 'isActive': True, 
                'owner': [self.player_rec['id']], 'discordUsername': [self.player_rec['id']], 
                'campaign': [self.world.campaign_rec['id']], 'party': [self.party.party_rec['id']]
                })


        print(f"[Isaacbot Logger]--{datetime.now()}-- New Character {ch_name}  {ch_class} ")


class World:
    # campaign_rec, name, donations, pticks, prosperity, achievements
    prosperity_levels = (0,4,9,15,22,30,39,50,64)
    donation_levels = (100,150,200,250,300,350,400,500,600,700,800,900,1000)
    def __init__(self, campaign_rec_id):
        # Use World(character.campaign[0])
        self.campaign_rec = campaign_airtable.get(campaign_rec_id)
        # campaign name is an env varibale for the bot eg CAMPAIGN_NAME=Camp Pain
        self.name = self.campaign_rec['fields']['name']
        self.donations = self.campaign_rec['fields']['totalDonations']
        self.pticks = self.campaign_rec['fields']['prosperityTicks']
        self.prosperity = self.prosperity_calc(self.pticks)
        self.achievements = self.campaign_rec['fields']['achievements']


    def prosperity_calc(self, pticks):
        for i in range(len(self.prosperity_levels)):
        # calculate prosperity from the prosperity_levels tuple      
            if pticks >= self.prosperity_levels[i] and pticks < self.prosperity_levels[i+1]:
                prosperity = i+1
                break
            else:
                continue

        return prosperity


    def gain_prosperity(self):

        self.gain_ptick()
        if self.pticks in self.prosperity_levels:
            self.prosperity += 1
            print(f"[Isaacbot Logger]--{datetime.now()}-- +1 Overall Prosperity....{self.name}, {self.prosperity}")
            self.unlock_prosperity(self.prosperity)


    def gain_ptick(self):
        self.pticks += 1
        campaign_airtable.update(self.campaign_rec['id'], {'prosperityTicks':self.pticks})
        print(f"[Isaacbot Logger]--{datetime.now()}-- Gain prosperity....{self.name}, {self.pticks} ticks")


    def lose_ptick(self):
        self.pticks -= 1
        campaign_airtable.update(self.campaign_rec['id'], {'prosperityTicks':self.pticks})
        print(f"[Isaacbot Logger]--{datetime.now()}-- Lose prosperity....{self.name}, {self.pticks} ticks")


    def unlock_prosperity(self, level_to_unlock):
        items_to_unlock = items_airtable.search('prosperityRequirement', level_to_unlock)

        for item in items_to_unlock:
            items_airtable.update(item['id'], {'maxCount':item['fields']['realMax'], 'isUnlocked':True})

        print(f"[Isaacbot Logger]--{datetime.now()}-- Lvl{level_to_unlock} items unlocked")


    def donate(self):
        self.donations += 10
        campaign_airtable.update(self.campaign_rec['id'], {'totalDonations':self.donations})
        print(f"[Isaacbot Logger]--{datetime.now()}-- +10gp donated.....Total: {self.donations}")


    def calc_donations_needed(self):
        for d in range(len(self.donation_levels)):
            if self.donations >=  self.donation_levels[d] and self.donations < self.donation_levels [d + 1]:
                self.next_donation_level = self.donation_levels[d + 1]
                return self.next_donation_level


class Scenario:
    # scenario_rec, number
    # Scenario details for scen_no 
    # Can be used to unlock or complete a scenario
    # In future: get all available scenarios, add description, scenario info

        def __init__(self, scene_no):
            self.scenario = scenario_airtable.match('number', int(scene_no))
            self.number = int(scene_no)
            self.name = ""            
            self.unlocked = None
            self.description = ""
            self.complete = None
            self.outcome = ""

            try:
                self.unlocked = self.scenario['fields']['isUnlocked']
                self.name = self.scenario['fields']['name']
                try:
                    self.description = self.scenario['fields']['description']
                except:
                    pass
            except:
                self.unlocked = False
            try:
                if self.scenario['fields']['isComplete'] == True:
                    self.complete = True
                    try:
                        self.outcome = self.scenario['fields']['outcome']
                    except:
                        pass
            except:
                self.complete = False
                self.outcome = ""



        def mark_unlocked(self, scene_name, scene_description=''):
            self.unlocked = self.scenario['fields']['isUnlocked'] = True
            self.name = scene_name
            self.description = scene_description
            scenario_airtable.update(self.scenario['id'], {'isUnlocked':True, 'name':self.name, 'description': self.description})
            print(f"[Isaacbot Logger]--{datetime.now()}-- Scenario {self.number} unlocked")


        def mark_complete(self):
            self.scenario['fields']['isComplete'] = True
            scenario_airtable.update(self.scenario['id'], {'isComplete':True})
            print(f"[Isaacbot Logger]--{datetime.now()}-- Scenario {self.number}: {self.name} complete")


        def update_description(self, description):
            self.description = description
            scenario_airtable.update(self.scenario['id'], {'description':description})
            print(f"[Isaacbot Logger]--{datetime.now()}--Scenario {self.number} description added -- '{description}'")


        def update_outcome(self, outcome):
            self.outcome = outcome
            scenario_airtable.update(self.scenario['id'], {'outcome':self.outcome})
            print(f"[Isaacbot Logger]--{datetime.now()}-- Scenario {self.number} outcome added -- '{outcome}'")


class Party:
    # party_rec, name, members, reputation, discount, achievements
    discount_levels = (0,3,7,11,15,19)
    # reputation levels where discount changes (+ or -)

    def __init__(self, party_rec_id):
        self.party_rec = party_airtable.get(party_rec_id)
        self.name = self.party_rec['fields']['name']
        self.members = self.party_rec['fields']['characters']
        self.reputation = self.party_rec['fields']['reputation']
        self.discount = self.discount_calc(self.reputation)
        self.achievements = self.party_rec['fields']['achievements']

    def discount_calc(self, reputation):
        # determine discount based on reputation. Used for buy action
        for j in range(len(self.discount_levels)):
            if self.reputation >= 19:
                discount = -5
            elif abs(self.reputation) >= self.discount_levels[j] and self.reputation < self.discount_levels[j+1]:
                discount = -j
                break
            else:
                continue
            if reputation < 0:
                discount = discount * -1
        return discount


    def gain_reputation(self):
        self.reputation += 1
        self.discount = self.discount_calc(self.reputation)
        campaign_airtable.update(self.party_rec['id'], {'reputation':self.reputation})
        print(f"[Isaacbot Logger]--{datetime.now()}-- Gain Reputation....{self.name}, {self.reputation}")


    def lose_reputation(self):
        self.reputation -= 1
        self.discount = self.discount_calc(self.reputation)
        campaign_airtable.update(self.party_rec['id'], {'reputation':self.reputation})
        print(f"[Isaacbot Logger]--{datetime.now()}-- Lose Reputation....{self.name}, {self.reputation}")

    def gain_achiev(self):
        pass

    def lose_achiev(self):
        pass


class Character:
    # character_rec, party, campaign, name, charclass, xp, lvl, gold, checks, items, abilities
    character_levels = (0,45,95,150,210,275,345,420,500)  
        # xp values for character level-up

    def __init__(self, author):
        self.character_rec = characters_airtable.match('discordUsername', author)   #returns dict
        self.party = self.character_rec['fields']['party']
        # record id
        self.campaign = self.character_rec['fields']['campaign']
        # record id
        self.name = self.character_rec['fields']['name']
        self.charclass = classes_airtable.get(self.character_rec['fields']['class'][0])['fields']['name']
        self.xp = self.character_rec['fields']['xp']
        self.lvl= self.lvl_calc()
        self.gold = self.character_rec['fields']['gold']
        self.checks = self.character_rec['fields']['checks']
        self.ch = self.check_calc()
        self.id = self.character_rec['id']

        try:
            self.items = self.character_rec['fields']['items']

        except KeyError:
            self.items = []
            characters_airtable.update(self.character_rec['id'], {'items':self.items})

        finally:
            self.item_nums = sorted(items_airtable.get(a)['fields']['number'] for a in self.items)


        try:
            self.abilities = self.character_rec['fields']['abilities']

        except KeyError:
            self.abilities = []
            characters_airtable.update(self.character_rec['id'], {'abilities':self.abilities})
        
        self.abil_nums = sorted(abilities_airtable.get(a)['fields']['number'] for a in self.abilities)


    def retire(self, quest=''):
        characters_airtable.update(self.character_rec['id'], {'isActive': False, 'isRetired': True, 'quest': quest})

    def deactivate(self):
        characters_airtable.update(self.id, {'discordUsername': '', 'isActive': False})

    def gain_xp(self, xp_gained):
        self.xp += xp_gained
            # Input XP gained and it will be added to the author's previous total
        characters_airtable.update(self.character_rec['id'], {'xp':self.xp})
        print(f"[Isaacbot Logger]--{datetime.now()}-- {self.name}  Gain {xp_gained}xp   Total: {self.xp}xp")
        new_lvl = self.lvl_calc()
        if new_lvl > self.lvl:
            print(f"[Isaacbot Logger]--{datetime.now()}-- {self.name} leveled up to Lvl {new_lvl}")
            self.lvl += 1
            return True
        else:
            return False


    def change_xp(self, new_xp):
    # update author xp to input
        self.xp = new_xp
        characters_airtable.update(self.character_rec['id'], {'xp':self.xp})
        print(f"[Isaacbot Logger]--{datetime.now()}-- {self.name}  Total: {self.xp}xp")
        new_lvl= self.lvl_calc()

        if new_lvl> self.lvl:
            print(f"[Isaacbot Logger]--{datetime.now()}-- {self.name} leveled up to Lvl {new_lvl}")
            return True
        else:
            return False


    def lvl_calc(self):
        if self.xp >= 500:
            level = 9
        else:
            for i in range(len(self.character_levels)):
                if self.character_levels[i] <= self.xp and self.character_levels[i+1] > self.xp:
                    level = i+1
        return level


    def gain_gold(self, gold_gained):
        # for gold lost use a negative number
        self.gold += gold_gained
        characters_airtable.update(self.character_rec['id'], {'gold':self.gold})
        print(f"[Isaacbot Logger]--{datetime.now()}-- {self.name} +{gold_gained}gp  Total: {self.gold}gold")


    def change_gold(self, new_gold):
        # update author gold to input
        self.gold = new_gold
        characters_airtable.update(self.character_rec['id'], {'gold':self.gold})
        print(f"[Isaacbot Logger]--{datetime.now()}-- {self.name}  Total: {self.gold}gold")


    def gain_checks(self, checks_gained):
        # for lose_checks use negative number
        self.checks += checks_gained
        characters_airtable.update(self.character_rec['id'], {'checks':self.checks})
        print(f"[Isaacbot Logger]--{datetime.now()}-- {self.name} +{checks_gained} checks  Total: {self.checks}checks")
        self.ch = self.check_calc()


    def change_checks(self, new_checks):
        self.checks = new_checks
        characters_airtable.update(self.character_rec['id'], {'checks':self.checks})
        # update author checks to input
        print(f"[Isaacbot Logger]--{datetime.now()}-- {self.name}  Total: {self.checks}checks")
        self.ch = self.check_calc()


    def check_calc(self):
        if self.checks == 1:
            self.ch = 'check'
        else: 
            self.ch = 'checks'
        return self.ch


    def level_up(self, abil_to_add):
        # abil must be given as a list of Airtable record ID eg [rec92398626]
        self. abilities = self.abilities + list(abil_to_add)
        characters_airtable.update(self.character_rec['id'], {'abilities':self.abilities})


    def item_transaction(self, action, item_num):
        item = Item(item_num)
        if action == 'gain':
            self.items.append(item.item_rec['id'])
            self.item_nums = sorted((items_airtable.get(a)['fields']['number'] for a in self.items))
            print(f"[Isaacbot Logger]--{datetime.now()}-- {self.name} gain item {item.number}")
        elif action == 'lose':
            self.items.remove(item.item_rec['id'])
            self.item_nums = sorted((items_airtable.get(a)['fields']['number'] for a in self.items))
            print(f"[Isaacbot Logger]--{datetime.now()}-- {self.name}e lose item {item.number}")
        elif action == 'loot':
            self.items.append(item.item_rec['id'])
            self.item_nums = sorted((items_airtable.get(a)['fields']['number'] for a in self.items))
            print(f"[Isaacbot Logger]--{datetime.now()}-- {self.name} loot item {item.number}")
        characters_airtable.update(self.character_rec['id'], {'items': self.items})


    def abil_transaction(self, action, abil_num):
        abil = Ability(abil_num)

        if action == 'gain':
            self.abilities.append(abil.ability['id'])
            self.abil_nums = sorted((abilities_airtable.get(a)['fields']['number'] for a in self.abilities))
            print(f"[Isaacbot Logger]--{datetime.now()}-- {self.name} gain abil {abil.number}, {self.abil_nums}")

        elif action == 'lose':
            self.abilities.remove(abil.ability['id'])
            self.abil_nums = sorted((abilities_airtable.get(a)['fields']['number'] for a in self.abilities))
            print(f"[Isaacbot Logger]--{datetime.now()}-- Ghostface remove abil {abil.number}, {sorted(self.abil_nums)}")

        characters_airtable.update(self.character_rec['id'], {'abilities':self.abilities})


class Item:

    def __init__(self, item_num):
        
        self.item_rec = items_airtable.match('number', item_num)
        
        self.number = item_num
        self.level = self.item_rec['fields']['prosperityRequirement']

        try:
            self.unlocked = self.item_rec['fields']['isUnlocked']
            self.number = self.item_rec['fields']['number']
            self.name = self.item_rec['fields']['name']
            self.cost = self.item_rec['fields']['cost']
            self.text = self.item_rec['fields']['description']
            self.numberAvailable = self.item_rec['fields']['numberAvailable']
            self.maxCount = self.item_rec['fields']['maxCount']
            self.realMax = self.item_rec['fields']['realMax']
            self.owners = self.item_rec['fields']['characterCount']
            self.num_name = f"{self.number}: {self.name}"
            self.description = self.item_rec['fields']['description']

        except:
            self.unlocked = False
            self.numberAvailable = 0
            self.maxCount = 0
            self.realMax = self.item_rec['fields']['realMax']


    def unlock_design(self):  
    # via gain_prosperity or loot design (all copies become available)
        
        self.unlocked = True
        self.maxCount = self.realMax
        update = {'isUnlocked':True, 'maxCount':self.maxCount}
        items_airtable.update(self.item_rec['id'], update)
        print(f"[Isaacbot Logger]--{datetime.now()}-- Item Design {self.number} unlocked")


    def unlock_loot(self):
    # via loot design
        self.unlocked = True
        if self.maxCount < self.realMax:
            self.maxCount += 1
        items_airtable.update(self.item_rec['id'], {'isUnlocked':self.unlocked, 'maxCount':self.maxCount})
        print(f"[Isaacbot Logger]--{datetime.now()}-- Item {self.number} looted.")


class Ability:
    def __init__(self, abil_num):
        self.ability = abilities_airtable.match('number', abil_num)      
        self.number = abil_num
        self.lvl= self.ability['fields']['levelRequired']
        self.charclass = classes_airtable.get(self.ability['fields']['class'][0])['fields']['name']
        self.name = self.ability['fields']['name']
        self.num_name = f"Lvl {self.lvl} -- {self.name}"


print('done')