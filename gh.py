#! python
import os
from datetime import datetime
from airtable import Airtable

# datetime object containing current date and time

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")  # stored in .env
AIRTABLE_BASE_KEY = os.getenv("AIRTABLE_BASE_KEY")  # stored in .env
CAMPAIGN_NAME = os.getenv("CAMPAIGN_NAME")  # stored in .env

CAMPAIGN_AIRTABLE = Airtable(AIRTABLE_BASE_KEY, "Campaign")
PARTY_AIRTABLE = Airtable(AIRTABLE_BASE_KEY, "Parties")
CHARACTERS_AIRTABLE = Airtable(AIRTABLE_BASE_KEY, "Characters")
SCENARIO_AIRTABLE = Airtable(AIRTABLE_BASE_KEY, "Scenarios")
ITEMS_AIRTABLE = Airtable(AIRTABLE_BASE_KEY, "Items")  # items record lookup
ABILITIES_AIRTABLE = Airtable(
    AIRTABLE_BASE_KEY, "Character Abilities"
)  # abilities record lookup
CLASSES_AIRTABLE = Airtable(
    AIRTABLE_BASE_KEY, "Character Classes"
)  # class record lookup
# storylines_airtable = Airtable(AIRTABLE_BASE_KEY, "Storylines")
PLAYERS_AIRTABLE = Airtable(AIRTABLE_BASE_KEY, "Players")
ACHIEVEMENTS_AIRTABLE = Airtable(AIRTABLE_BASE_KEY, "Achievements")

CHARACTER_LEVELS = (0, 45, 95, 150, 210, 275, 345, 420, 500)
PROSPERITY_LEVELS = (0, 4, 9, 15, 22, 30, 39, 50, 64)

class Player:
    # CHARACTER_LEVELS = (0, 45, 95, 150, 210, 275, 345, 420, 500)
    # PROSPERITY_LEVELS = (0, 4, 9, 15, 22, 30, 39, 50, 64)

    def __init__(self, author):
        self.name = author
        self.player_rec = PLAYERS_AIRTABLE.match("discordUsername", author)

    def activate_character(self, ch_name):
        character_rec = CHARACTERS_AIRTABLE.match("name", ch_name)
        CHARACTERS_AIRTABLE.update(
            character_rec["id"],
            {"discordUsername": [self.player_rec["id"]], "isActive": True},
        )

    def create_character(self, ch_name, ch_class):
        self.world = World(CAMPAIGN_AIRTABLE.match("name", "Camp Pain")["id"])
        self.party = Party(PARTY_AIRTABLE.match("name", "Wyld Stallyns")["id"])
        prosperity = self.world.prosperity
        xp = CHARACTER_LEVELS[prosperity]
        gold = (prosperity + 1) * 15
        charclass = CLASSES_AIRTABLE.match("name", ch_class)["id"]
        CHARACTERS_AIRTABLE.insert(
            {
                "name": ch_name,
                "xp": xp,
                "gold": gold,
                "checks": 0,
                "class": [charclass],
                "isActive": True,
                "owner": [self.player_rec["id"]],
                "discordUsername": [self.player_rec["id"]],
                "campaign": [self.world.campaign_rec["id"]],
                "party": [self.party.party_rec["id"]],
            }
        )

        print(
            f"[Isaacbot Logger]--{datetime.now()}-- New Character {ch_name}  {ch_class} "
        )


class World:
    # campaign_rec, name, donations, pticks, prosperity, achievements
    PROSPERITY_LEVELS = (0, 4, 9, 15, 22, 30, 39, 50, 64)
    DONATION_LEVELS = (100, 150, 200, 250, 300, 350, 400, 500, 600, 700, 800, 900, 1000)

    def __init__(self, campaign_rec_id):
        # Use World(character.campaign[0])
        self.campaign_rec = CAMPAIGN_AIRTABLE.get(campaign_rec_id)
        # campaign name is an env varibale for the bot eg CAMPAIGN_NAME=Camp Pain
        self.name = self.campaign_rec["fields"]["name"]
        self.donations = self.campaign_rec["fields"]["totalDonations"]
        self.pticks = self.campaign_rec["fields"]["prosperityTicks"]
        self.prosperity = self.prosperity_calc(self.pticks)
        self.achievements = self.campaign_rec["fields"]["achievements"]

    def prosperity_calc(self, pticks):
        for i in range(len(self.PROSPERITY_LEVELS)):
            # calculate prosperity from the prosperity_levels tuple
            if (
                pticks >= self.PROSPERITY_LEVELS[i]
                and pticks < self.PROSPERITY_LEVELS[i + 1]
            ):
                prosperity = i + 1
                break
            else:
                continue
        return prosperity

    def gain_prosperity(self):
        self.gain_ptick()
        if self.pticks in self.PROSPERITY_LEVELS:
            self.prosperity += 1
            print(
                f"[Isaacbot Logger]--{datetime.now()}-- +1 Overall Prosperity....{self.name}, {self.prosperity}"
            )
            self.unlock_prosperity(self.prosperity)

    def gain_ptick(self):
        self.pticks += 1
        CAMPAIGN_AIRTABLE.update(
            self.campaign_rec["id"], {"prosperityTicks": self.pticks}
        )
        print(
            f"[Isaacbot Logger]--{datetime.now()}-- Gain prosperity....{self.name}, {self.pticks} ticks"
        )

    def lose_ptick(self):
        self.pticks -= 1
        CAMPAIGN_AIRTABLE.update(
            self.campaign_rec["id"], {"prosperityTicks": self.pticks}
        )
        print(
            f"[Isaacbot Logger]--{datetime.now()}-- Lose prosperity....{self.name}, {self.pticks} ticks"
        )

    def unlock_prosperity(self, level_to_unlock):
        items_to_unlock = ITEMS_AIRTABLE.search(
            "prosperityRequirement", level_to_unlock
        )

        for item in items_to_unlock:
            ITEMS_AIRTABLE.update(
                item["id"], {"maxCount": item["fields"]["realMax"], "isUnlocked": True}
            )

        print(
            f"[Isaacbot Logger]--{datetime.now()}-- Lvl{level_to_unlock} items unlocked"
        )

    def donate(self):
        self.donations += 10
        CAMPAIGN_AIRTABLE.update(
            self.campaign_rec["id"], {"totalDonations": self.donations}
        )
        print(
            f"[Isaacbot Logger]--{datetime.now()}-- +10gp donated.....Total: {self.donations}"
        )

    def calc_donations_needed(self):
        for d in range(len(self.DONATION_LEVELS)):
            if (
                self.donations >= self.DONATION_LEVELS[d]
                and self.donations < self.DONATION_LEVELS[d + 1]
            ):
                self.next_donation_level = self.DONATION_LEVELS[d + 1]
                return self.next_donation_level


class Scenario:
    # scenario_rec, number
    # Scenario details for scen_no
    # Can be used to unlock or complete a scenario
    # In future: get all available scenarios, add description, scenario info

    def __init__(self, scene_no):
        self.scenario = SCENARIO_AIRTABLE.match("number", int(scene_no))
        self.number = int(scene_no)
        self.name = ""
        self.unlocked = None
        self.description = ""
        self.complete = None
        self.outcome = ""

        try:
            self.unlocked = self.scenario["fields"]["isUnlocked"]
            self.name = self.scenario["fields"]["name"]
            try:
                self.description = self.scenario["fields"]["description"]
            except:
                pass
        except:
            self.unlocked = False
        try:
            if self.scenario["fields"]["isComplete"] == True:
                self.complete = True
                try:
                    self.outcome = self.scenario["fields"]["outcome"]
                except:
                    pass
        except:
            self.complete = False
            self.outcome = ""

    def mark_unlocked(self, scene_name, scene_description=""):
        self.unlocked = self.scenario["fields"]["isUnlocked"] = True
        self.name = scene_name
        self.description = scene_description
        SCENARIO_AIRTABLE.update(
            self.scenario["id"],
            {"isUnlocked": True, "name": self.name, "description": self.description},
        )
        print(f"[Isaacbot Logger]--{datetime.now()}-- Scenario {self.number} unlocked")

    def mark_complete(self):
        self.scenario["fields"]["isComplete"] = True
        SCENARIO_AIRTABLE.update(self.scenario["id"], {"isComplete": True})
        print(
            f"[Isaacbot Logger]--{datetime.now()}-- Scenario {self.number}: {self.name} complete"
        )

    def update_description(self, description):
        self.description = description
        SCENARIO_AIRTABLE.update(self.scenario["id"], {"description": description})
        print(
            f"[Isaacbot Logger]--{datetime.now()}--Scenario {self.number} description added -- '{description}'"
        )

    def update_outcome(self, outcome):
        self.outcome = outcome
        SCENARIO_AIRTABLE.update(self.scenario["id"], {"outcome": self.outcome})
        print(
            f"[Isaacbot Logger]--{datetime.now()}-- Scenario {self.number} outcome added -- '{outcome}'"
        )


class Party:

    __slots__ = ('party_rec', 'name', 'members', 'reputation', 'discount', 'achievements')

    DISOUNT_LEVELS = (0, 3, 7, 11, 15, 19)
    # reputation levels where discount changes (+ or -)

    def __init__(self, party_rec_id):
        self.party_rec = PARTY_AIRTABLE.get(party_rec_id)
        self.name = self.party_rec["fields"]["name"]
        self.members = self.party_rec["fields"]["characters"]
        self.reputation = self.party_rec["fields"]["reputation"]
        self.discount = self.discount_calc(self.reputation)
        self.achievements = self.party_rec["fields"]["achievements"]

    def discount_calc(self, reputation):
        # determine discount based on reputation. Used for buy action
        for j in range(len(self.DISOUNT_LEVELS)):
            if self.reputation >= 19:
                discount = -5
            elif (
                abs(self.reputation) >= self.DISOUNT_LEVELS[j]
                and self.reputation < self.DISOUNT_LEVELS[j + 1]
            ):
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
        CAMPAIGN_AIRTABLE.update(self.party_rec["id"], {"reputation": self.reputation})
        print(
            f"[Isaacbot Logger]--{datetime.now()}-- Gain Reputation....{self.name}, {self.reputation}"
        )

    def lose_reputation(self):
        self.reputation -= 1
        self.discount = self.discount_calc(self.reputation)
        CAMPAIGN_AIRTABLE.update(self.party_rec["id"], {"reputation": self.reputation})
        print(
            f"[Isaacbot Logger]--{datetime.now()}-- Lose Reputation....{self.name}, {self.reputation}"
        )

    def gain_achiev(self):
        pass

    def lose_achiev(self):
        pass


class Character:
    
    __slots__ = ('character_rec', 'party', 'campaign', 'name', 'charclass', 'xp', 'lvl', 'gold', 'checks', 'items', 'abilities')

    def __init__(self, author):
        self.character_rec = CHARACTERS_AIRTABLE.match(
            "discordUsername", author
        )  # returns dict
        self.party = self.character_rec["fields"]["party"]
        # record id
        self.campaign = self.character_rec["fields"]["campaign"]
        # record id
        self.name = self.character_rec["fields"]["name"]
        self.charclass = CLASSES_AIRTABLE.get(self.character_rec["fields"]["class"][0])[
            "fields"
        ]["name"]
        self.xp = self.character_rec["fields"]["xp"]
        self.lvl = self.lvl_calc()
        self.gold = self.character_rec["fields"]["gold"]
        self.checks = self.character_rec["fields"]["checks"]
        self.ch = self.check_calc()
        self.id = self.character_rec["id"]

        try:
            self.items = self.character_rec["fields"]["items"]

        except KeyError:
            self.items = []
            CHARACTERS_AIRTABLE.update(self.character_rec["id"], {"items": self.items})

        finally:
            self.item_nums = sorted(
                ITEMS_AIRTABLE.get(a)["fields"]["number"] for a in self.items
            )

        try:
            self.abilities = self.character_rec["fields"]["abilities"]

        except KeyError:
            self.abilities = []
            CHARACTERS_AIRTABLE.update(
                self.character_rec["id"], {"abilities": self.abilities}
            )

        self.ability_numbers = sorted(
            ABILITIES_AIRTABLE.get(a)["fields"]["number"] for a in self.abilities
        )

    def retire(self, quest=""):
        CHARACTERS_AIRTABLE.update(
            self.character_rec["id"],
            {"isActive": False, "isRetired": True, "quest": quest},
        )

    def deactivate(self):
        CHARACTERS_AIRTABLE.update(self.id, {"discordUsername": "", "isActive": False})

    def gain_xp(self, xp_gained):
        self.xp += xp_gained
        # Input XP gained and it will be added to the author's previous total
        CHARACTERS_AIRTABLE.update(self.character_rec["id"], {"xp": self.xp})
        print(
            f"[Isaacbot Logger]--{datetime.now()}-- {self.name}  Gain {xp_gained}xp   Total: {self.xp}xp"
        )
        new_lvl = self.lvl_calc()
        if new_lvl > self.lvl:
            print(
                f"[Isaacbot Logger]--{datetime.now()}-- {self.name} leveled up to Lvl {new_lvl}"
            )
            self.lvl += 1
            return True
        else:
            return False

    def change_xp(self, new_xp):
        # update author xp to input
        self.xp = new_xp
        CHARACTERS_AIRTABLE.update(self.character_rec["id"], {"xp": self.xp})
        print(f"[Isaacbot Logger]--{datetime.now()}-- {self.name}  Total: {self.xp}xp")
        new_lvl = self.lvl_calc()

        if new_lvl > self.lvl:
            print(
                f"[Isaacbot Logger]--{datetime.now()}-- {self.name} leveled up to Lvl {new_lvl}"
            )
            return True
        else:
            return False

    def lvl_calc(self):
        if self.xp >= 500:
            level = 9
        else:
            for i in range(len(CHARACTER_LEVELS)):
                if (
                    CHARACTER_LEVELS[i] <= self.xp
                    and CHARACTER_LEVELS[i + 1] > self.xp
                ):
                    level = i + 1
        return level

    def gain_gold(self, gold_gained):
        # for gold lost use a negative number
        self.gold += gold_gained
        CHARACTERS_AIRTABLE.update(self.character_rec["id"], {"gold": self.gold})
        print(
            f"[Isaacbot Logger]--{datetime.now()}-- {self.name} +{gold_gained}gp  Total: {self.gold}gold"
        )

    def change_gold(self, new_gold):
        # update author gold to input
        self.gold = new_gold
        CHARACTERS_AIRTABLE.update(self.character_rec["id"], {"gold": self.gold})
        print(
            f"[Isaacbot Logger]--{datetime.now()}-- {self.name}  Total: {self.gold}gold"
        )

    def gain_checks(self, checks_gained):
        # for lose_checks use negative number
        self.checks += checks_gained
        CHARACTERS_AIRTABLE.update(self.character_rec["id"], {"checks": self.checks})
        print(
            f"[Isaacbot Logger]--{datetime.now()}-- {self.name} +{checks_gained} checks  Total: {self.checks}checks"
        )
        self.ch = self.check_calc()

    def change_checks(self, new_checks):
        self.checks = new_checks
        CHARACTERS_AIRTABLE.update(self.character_rec["id"], {"checks": self.checks})
        # update author checks to input
        print(
            f"[Isaacbot Logger]--{datetime.now()}-- {self.name}  Total: {self.checks}checks"
        )
        self.ch = self.check_calc()

    def check_calc(self):
        if self.checks == 1:
            self.ch = "check"
        else:
            self.ch = "checks"
        return self.ch

    def level_up(self, abil_to_add):
        # abil must be given as a list of Airtable record ID eg [rec92398626]
        self.abilities = self.abilities + list(abil_to_add)
        CHARACTERS_AIRTABLE.update(
            self.character_rec["id"], {"abilities": self.abilities}
        )

    def item_transaction(self, action, item_number):
        item = Item(item_number)
        if action == "gain":
            self.items.append(item.item_rec["id"])
            self.item_nums = sorted(
                (ITEMS_AIRTABLE.get(a)["fields"]["number"] for a in self.items)
            )
            print(
                f"[Isaacbot Logger]--{datetime.now()}-- {self.name} gain item {item.number}"
            )
        elif action == "lose":
            self.items.remove(item.item_rec["id"])
            self.item_nums = sorted(
                (ITEMS_AIRTABLE.get(a)["fields"]["number"] for a in self.items)
            )
            print(
                f"[Isaacbot Logger]--{datetime.now()}-- {self.name} lose item {item.number}"
            )
        elif action == "loot":
            self.items.append(item.item_rec["id"])
            self.item_nums = sorted(
                (ITEMS_AIRTABLE.get(a)["fields"]["number"] for a in self.items)
            )
            print(
                f"[Isaacbot Logger]--{datetime.now()}-- {self.name} loot item {item.number}"
            )
        CHARACTERS_AIRTABLE.update(self.character_rec["id"], {"items": self.items})

    def abil_transaction(self, action, ability_number):
        ability = Ability(ability_number)

        if action == "gain":
            self.abilities.append(ability.ability["id"])
            self.ability_fnumbers = sorted(
                (ABILITIES_AIRTABLE.get(a)["fields"]["number"] for a in self.abilities)
            )
            print(
                f"[Isaacbot Logger]--{datetime.now()}-- {self.name} gain abil {ability.number}, {self.ability_numbers}"
            )

        elif action == "lose":
            self.abilities.remove(ability.ability["id"])
            self.ability_numbers = sorted(
                (ABILITIES_AIRTABLE.get(a)["fields"]["number"] for a in self.abilities)
            )
            print(
                f"[Isaacbot Logger]--{datetime.now()}-- Ghostface remove abil {ability.number}, {sorted(self.ability_numbers)}"
            )

        CHARACTERS_AIRTABLE.update(
            self.character_rec["id"], {"abilities": self.abilities}
        )


class Item:
    def __init__(self, item_num):

        self.item_rec = ITEMS_AIRTABLE.match("number", item_num)

        self.number = item_num
        self.level = self.item_rec["fields"]["prosperityRequirement"]

        try:
            self.unlocked = self.item_rec["fields"]["isUnlocked"]
            self.number = self.item_rec["fields"]["number"]
            self.name = self.item_rec["fields"]["name"]
            self.cost = self.item_rec["fields"]["cost"]
            self.text = self.item_rec["fields"]["description"]
            self.numberAvailable = self.item_rec["fields"]["numberAvailable"]
            self.maxCount = self.item_rec["fields"]["maxCount"]
            self.realMax = self.item_rec["fields"]["realMax"]
            self.owners = self.item_rec["fields"]["characterCount"]
            self.num_name = f"{self.number}: {self.name}"
            self.description = self.item_rec["fields"]["description"]

        except:
            self.unlocked = False
            self.numberAvailable = 0
            self.maxCount = 0
            self.realMax = self.item_rec["fields"]["realMax"]

    def unlock_design(self):
        # via gain_prosperity or loot design (all copies become available)

        self.unlocked = True
        self.maxCount = self.realMax
        update = {"isUnlocked": True, "maxCount": self.maxCount}
        ITEMS_AIRTABLE.update(self.item_rec["id"], update)
        print(
            f"[Isaacbot Logger]--{datetime.now()}-- Item Design {self.number} unlocked"
        )

    def unlock_loot(self):
        # via loot design
        self.unlocked = True
        if self.maxCount < self.realMax:
            self.maxCount += 1
        ITEMS_AIRTABLE.update(
            self.item_rec["id"],
            {"isUnlocked": self.unlocked, "maxCount": self.maxCount},
        )
        print(f"[Isaacbot Logger]--{datetime.now()}-- Item {self.number} looted.")


class Ability:
    def __init__(self, abil_num):
        self.ability = ABILITIES_AIRTABLE.match("number", abil_num)
        self.number = abil_num
        self.lvl = self.ability["fields"]["levelRequired"]
        self.charclass = CLASSES_AIRTABLE.get(self.ability["fields"]["class"][0])[
            "fields"
        ]["name"]
        self.name = self.ability["fields"]["name"]
        self.num_name = f"Lvl {self.lvl} -- {self.name}"


print("done")
