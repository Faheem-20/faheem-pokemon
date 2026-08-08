from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TrainerProfile, TrainerInventory, KingdomMap, BattleStatistics

@receiver(post_save, sender=TrainerProfile)
def create_trainer_default_data(sender, instance, created, **kwargs):
    if created:
        # Create BattleStatistics
        BattleStatistics.objects.get_or_create(trainer=instance)

        # Create default Inventory
        default_inventory = [
            {"id": 1, "name": "Master Ball", "category": "Poké Balls", "qty": 1},
            {"id": 2, "name": "Ultra Ball", "category": "Poké Balls", "qty": 12},
            {"id": 3, "name": "Great Ball", "category": "Poké Balls", "qty": 25},
            {"id": 4, "name": "Poke Ball", "category": "Poké Balls", "qty": 50},
            {"id": 5, "name": "Premier Ball", "category": "Poké Balls", "qty": 10},
            {"id": 6, "name": "Beast Ball", "category": "Poké Balls", "qty": 2},
            {"id": 28, "name": "Quick Ball", "category": "Poké Balls", "qty": 10},
            {"id": 29, "name": "Dusk Ball", "category": "Poké Balls", "qty": 12},
            {"id": 30, "name": "Luxury Ball", "category": "Poké Balls", "qty": 5},
            {"id": 7, "name": "Max Potion", "category": "Potions", "qty": 4},
            {"id": 8, "name": "Hyper Potion", "category": "Potions", "qty": 8},
            {"id": 9, "name": "Super Potion", "category": "Potions", "qty": 15},
            {"id": 10, "name": "Potion", "category": "Potions", "qty": 30},
            {"id": 11, "name": "Full Restore", "category": "Potions", "qty": 5},
            {"id": 31, "name": "Antidote", "category": "Potions", "qty": 15},
            {"id": 32, "name": "Paralyze Heal", "category": "Potions", "qty": 15},
            {"id": 33, "name": "Full Heal", "category": "Potions", "qty": 10},
            {"id": 12, "name": "Revive", "category": "Battle Items", "qty": 10},
            {"id": 13, "name": "Max Revive", "category": "Battle Items", "qty": 3},
            {"id": 14, "name": "Rare Candy", "category": "Battle Items", "qty": 5},
            {"id": 15, "name": "PP Max", "category": "Battle Items", "qty": 2},
            {"id": 34, "name": "X Attack", "category": "Battle Items", "qty": 8},
            {"id": 35, "name": "X Defense", "category": "Battle Items", "qty": 8},
            {"id": 36, "name": "Elixir", "category": "Battle Items", "qty": 4},
            {"id": 37, "name": "Max Elixir", "category": "Battle Items", "qty": 2},
            {"id": 16, "name": "Fire Stone", "category": "Evolution Stones", "qty": 3},
            {"id": 17, "name": "Water Stone", "category": "Evolution Stones", "qty": 4},
            {"id": 18, "name": "Thunder Stone", "category": "Evolution Stones", "qty": 2},
            {"id": 19, "name": "Leaf Stone", "category": "Evolution Stones", "qty": 2},
            {"id": 20, "name": "Moon Stone", "category": "Evolution Stones", "qty": 1},
            {"id": 21, "name": "Sun Stone", "category": "Evolution Stones", "qty": 2},
            {"id": 38, "name": "Shiny Stone", "category": "Evolution Stones", "qty": 1},
            {"id": 39, "name": "Dusk Stone", "category": "Evolution Stones", "qty": 2},
            {"id": 40, "name": "Dawn Stone", "category": "Evolution Stones", "qty": 1},
            {"id": 22, "name": "Sitrus Berry", "category": "Berries", "qty": 15},
            {"id": 23, "name": "Oran Berry", "category": "Berries", "qty": 25},
            {"id": 41, "name": "Pecha Berry", "category": "Berries", "qty": 20},
            {"id": 42, "name": "Cheri Berry", "category": "Berries", "qty": 20},
            {"id": 43, "name": "Lum Berry", "category": "Berries", "qty": 8},
            {"id": 24, "name": "Leftovers", "category": "Held Items", "qty": 2},
            {"id": 25, "name": "Choice Band", "category": "Held Items", "qty": 1},
            {"id": 44, "name": "Choice Specs", "category": "Held Items", "qty": 1},
            {"id": 45, "name": "Choice Scarf", "category": "Held Items", "qty": 2},
            {"id": 46, "name": "Life Orb", "category": "Held Items", "qty": 1},
            {"id": 47, "name": "Focus Sash", "category": "Held Items", "qty": 2},
            {"id": 26, "name": "Bicycle", "category": "Key Items", "qty": 1}
        ]

        for item in default_inventory:
            max_stk = 1 if item["category"] == "Key Items" else 99
            TrainerInventory.objects.get_or_create(
                trainer=instance,
                item_name=item["name"],
                defaults={
                    "item_id": item["id"],
                    "category": item["category"],
                    "quantity": item["qty"],
                    "max_stack": max_stk
                }
            )

        # Create default Regions
        default_regions = [
            {"region_id": "kanto", "name": "Kanto", "status": "unlocked", "progress": 65, "gyms": 8, "legendary_count": 5},
            {"region_id": "johto", "name": "Johto", "status": "unlocked", "progress": 40, "gyms": 8, "legendary_count": 6},
            {"region_id": "hoenn", "name": "Hoenn", "status": "locked", "progress": 0, "gyms": 8, "legendary_count": 10},
            {"region_id": "sinnoh", "name": "Sinnoh", "status": "locked", "progress": 0, "gyms": 8, "legendary_count": 13},
            {"region_id": "unova", "name": "Unova", "status": "locked", "progress": 0, "gyms": 8, "legendary_count": 9},
            {"region_id": "kalos", "name": "Kalos", "status": "locked", "progress": 0, "gyms": 8, "legendary_count": 6},
            {"region_id": "alola", "name": "Alola", "status": "locked", "progress": 0, "gyms": 4, "legendary_count": 11},
            {"region_id": "galar", "name": "Galar", "status": "locked", "progress": 0, "gyms": 10, "legendary_count": 10},
            {"region_id": "paldea", "name": "Paldea", "status": "locked", "progress": 0, "gyms": 8, "legendary_count": 8}
        ]

        for reg in default_regions:
            KingdomMap.objects.get_or_create(
                trainer=instance,
                region_id=reg["region_id"],
                defaults={
                    "name": reg["name"],
                    "status": reg["status"],
                    "progress": reg["progress"],
                    "gyms": reg["gyms"],
                    "legendary_count": reg["legendary_count"]
                }
            )
