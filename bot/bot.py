from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2
from sc2.player import Bot, Computer
import random

class CompetitiveBot(BotAI):
    NAME: str = "xl8-zerg-bot"    
    RACE: Race = Race.Zerg
    
    def select_target(self):
        if self.enemy_structures.exists:
            return random.choice(self.enemy_structures).position
        return self.enemy_start_locations[0]
    
    async def on_start(self):
        print("Game started")

    async def on_step(self, iteration: int):
        if iteration == 0:
            await self.chat_send(f"glhf")
        if iteration % 100 == 0:
            await self.chat_send(f"Time: {iteration}")

        await self.distribute_workers()
        await self.build_overlords()
        await self.build_hatcheries()
        await self.build_spawning_pool()
        await self.build_extractors()
        await self.build_queens()
        await self.inject_queens()
        await self.build_evolution_chamber()
        # await self.build_baneling_nest()
        await self.build_lair()
        await self.research_zergling_speed()
        await self.research_one_one()
        
        await self.build_workers()
        # await self.morph_banelings()
        await self.train_zerglings()
        
        await self.attack(iteration=iteration)
        pass
    
    async def build_workers(self):
        for larva in self.units(UnitTypeId.LARVA).ready:
            if (self.can_afford(UnitTypeId.DRONE) 
                and self.workers.amount < self.townhalls.amount * 14
                and self.supply_left > 1):
                larva.train(UnitTypeId.DRONE)

    async def build_overlords(self):
        for larva in self.units(UnitTypeId.LARVA).ready:
            if (self.supply_left < 4 
                and not self.already_pending(UnitTypeId.OVERLORD)
                and self.can_afford(UnitTypeId.OVERLORD)):
                larva.train(UnitTypeId.OVERLORD)
            if (self.supply_used > 36 and self.supply_left < 8
                and not self.already_pending(UnitTypeId.OVERLORD) >= 5
                and self.can_afford(UnitTypeId.OVERLORD)):
                larva.train(UnitTypeId.OVERLORD)
            
    async def build_hatcheries(self):
        if (self.structures(UnitTypeId.HATCHERY).amount < 3
            and self.can_afford(UnitTypeId.HATCHERY)
            and not self.already_pending(UnitTypeId.HATCHERY)):
            await self.expand_now()
        if (self.structures(UnitTypeId.HATCHERY).amount < 3
            and self.can_afford(UnitTypeId.HATCHERY)
            and not self.already_pending(UnitTypeId.HATCHERY)
            and self.workers.amount > 32):
            await self.expand_now()
    
    async def build_spawning_pool(self):
        if (self.supply_used >= 17 
            and self.structures(UnitTypeId.SPAWNINGPOOL).amount == 0 
            and not self.already_pending(UnitTypeId.SPAWNINGPOOL) 
            and not self.townhalls.amount == 1):
            if self.can_afford(UnitTypeId.SPAWNINGPOOL):
                await self.build(
                    UnitTypeId.SPAWNINGPOOL, 
                    near=self.townhalls.first)
    
    async def build_extractors(self):
        if (self.supply_used > 18 
            and not self.already_pending(UnitTypeId.EXTRACTOR)
            and self.structures(UnitTypeId.EXTRACTOR).amount < self.townhalls.amount
        ):
            for hatchery in self.townhalls.ready:
                vgs = self.vespene_geyser.closer_than(15, hatchery)
                for vg in vgs:
                    if (self.can_afford(UnitTypeId.EXTRACTOR) 
                        and not self.structures(UnitTypeId.EXTRACTOR).closer_than(20, vg).exists
                        and not self.already_pending(UnitTypeId.SPAWNINGPOOL)):
                        drone = self.select_build_worker(vg.position)
                        if drone:
                            drone.build(UnitTypeId.EXTRACTOR, vg)
                            break
    
    async def build_queens(self):
        if (self.structures(UnitTypeId.HATCHERY).amount > self.units(UnitTypeId.QUEEN).amount
            and self.can_afford(UnitTypeId.QUEEN)):
            for hatchery in self.townhalls.ready.idle:
                if hatchery.is_ready:
                    hatchery.train(UnitTypeId.QUEEN)
                
    async def inject_queens(self):
        if self.units(UnitTypeId.QUEEN).amount > 0:
            for queen in self.units(UnitTypeId.QUEEN).idle:
                hatchery = self.townhalls.closest_to(queen.position)
                if queen.energy >= 25 and hatchery:
                    queen(AbilityId.EFFECT_INJECTLARVA, hatchery)
    
    async def train_zerglings(self):
        if (self.structures(UnitTypeId.SPAWNINGPOOL).ready.exists
            and self.can_afford(UnitTypeId.ZERGLING)):
            for larva in self.units(UnitTypeId.LARVA).ready:
                larva.train(UnitTypeId.ZERGLING)
                
    async def build_evolution_chamber(self):
        if (self.structures(UnitTypeId.EVOLUTIONCHAMBER).amount < 2
            and self.structures(UnitTypeId.SPAWNINGPOOL).amount < 2
            and self.structures(UnitTypeId.SPAWNINGPOOL).ready.exists
            and self.can_afford(UnitTypeId.EVOLUTIONCHAMBER)
            and not self.already_pending(UnitTypeId.EVOLUTIONCHAMBER)):
            await self.build(
                UnitTypeId.EVOLUTIONCHAMBER, 
                near= self.townhalls.first.position.towards(self.game_info.map_center, 5))
        
    # async def build_baneling_nest(self):
    #     if (self.structures(UnitTypeId.BANELINGNEST).amount < 1
    #         and self.structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists
    #         and self.can_afford(UnitTypeId.BANELINGNEST)
    #         and not self.already_pending(UnitTypeId.BANELINGNEST)):
    #         await self.build(
    #             UnitTypeId.BANELINGNEST, 
    #             near=self.townhalls.first)
            
    async def build_lair(self):
        if (self.structures(UnitTypeId.LAIR).amount < 1
            and self.structures(UnitTypeId.HIVE).amount < 1
            and self.structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists
            and self.can_afford(UnitTypeId.LAIR)
            and not self.already_pending(UnitTypeId.LAIR)):
            lair = self.structures(UnitTypeId.HATCHERY).ready.first
            if lair:
                lair(AbilityId.UPGRADETOLAIR_LAIR)
            
    # async def morph_banelings(self):
    #     if (self.structures(UnitTypeId.BANELINGNEST).ready.exists
    #         and self.can_afford(UnitTypeId.BANELING)
    #         and self.army_count > 0
    #         and self.units(UnitTypeId.BANELING).amount < self.army_count / 2):
    #         for zergling in self.units(UnitTypeId.ZERGLING).ready:
    #             if (self.can_afford(UnitTypeId.BANELING)):
    #                 zergling.train(UnitTypeId.BANELING)
                
    
    async def attack(self, iteration):
        if self.units(UnitTypeId.ZERGLING).amount > 0:
            armor = self.units(UnitTypeId.ZERGLING).ready.random.armor_upgrade_level
            atk = self.units(UnitTypeId.ZERGLING).ready.random.attack_upgrade_level
            if (self.units(UnitTypeId.ZERGLING).amount > 70
                and iteration % 50 == 0
                and armor < 3
                and atk < 3):
                for unit in self.units(UnitTypeId.ZERGLING).idle:
                    unit.attack(self.select_target())
        
    async def research_zergling_speed(self):
        if (self.structures(UnitTypeId.SPAWNINGPOOL).ready.exists
            and self.units(UnitTypeId.ZERGLING).amount > 20
            and self.can_afford(UpgradeId.ZERGLINGMOVEMENTSPEED)
            and not self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED)):
            self.research(UpgradeId.ZERGLINGMOVEMENTSPEED)
    
    async def research_one_one(self):
        if (self.structures(UnitTypeId.EVOLUTIONCHAMBER).ready
            and self.army_count > 20
            and self.can_afford(UpgradeId.ZERGMELEEWEAPONSLEVEL1)
            and not self.already_pending_upgrade(UpgradeId.ZERGMELEEWEAPONSLEVEL1)):
            self.research(UpgradeId.ZERGMELEEWEAPONSLEVEL1)
        if (self.structures(UnitTypeId.EVOLUTIONCHAMBER).ready
            and self.army_count > 20
            and self.can_afford(UpgradeId.ZERGGROUNDARMORSLEVEL1)
            and not self.already_pending_upgrade(UpgradeId.ZERGGROUNDARMORSLEVEL1)):
            self.research(UpgradeId.ZERGGROUNDARMORSLEVEL1)
            
    
    async def on_end(self, result: Result):
        print("Game ended.")
