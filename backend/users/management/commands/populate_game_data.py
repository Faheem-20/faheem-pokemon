from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import (
    TrainerProfile, CapturedPokemon, TrainerInventory,
    Mission, ShopItem, Achievement, KingdomMap
)

class Command(BaseCommand):
    help = 'Populates default Pokémon Nexus database game data (admin, shop items, missions, achievements, sample trainers)'

    def handle(self, *args, **options):
        self.stdout.write('Populating default Pokémon Nexus database data...')

        # 1. DEFAULT ADMIN USER
        admin_email = 'admin@pokemonnexus.com'
        admin_user, created = User.objects.get_or_create(
            username=admin_email,
            defaults={
                'email': admin_email,
                'first_name': 'Nexus Admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('adminpassword123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created Admin User: {admin_email} / adminpassword123'))
            
        admin_profile, created = TrainerProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                'trainer_name': 'Nexus Admin',
                'role': 'admin',
                'level': 99,
                'xp': 0,
                'coins': 99999,
                'region': 'Kanto',
                'current_rank': 'Master'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Admin Trainer Profile'))

        # 2. DEFAULT SHOP ITEMS
        shop_items = [
            {"item_id": 1, "name": "Master Ball", "category": "Poké Balls", "price": 50000, "stock": 1, "rarity": "Legendary", "image": "https://archives.bulbagarden.net/media/upload/9/95/Dream_Master_Ball_Sprite.png", "desc": "The ultimate Ball that catches any wild Pokémon without fail."},
            {"item_id": 2, "name": "Ultra Ball", "category": "Poké Balls", "price": 800, "stock": -1, "rarity": "Rare", "image": "https://archives.bulbagarden.net/media/upload/a/a8/Dream_Ultra_Ball_Sprite.png", "desc": "An ultra-performance Ball that provides a high catch rate."},
            {"item_id": 3, "name": "Great Ball", "category": "Poké Balls", "price": 600, "stock": -1, "rarity": "Uncommon", "image": "https://archives.bulbagarden.net/media/upload/b/bf/Dream_Great_Ball_Sprite.png", "desc": "A high-performance Ball that provides a higher catch rate."},
            {"item_id": 4, "name": "Poke Ball", "category": "Poké Balls", "price": 200, "stock": -1, "rarity": "Common", "image": "https://archives.bulbagarden.net/media/upload/7/79/Dream_Pok%C3%A9_Ball_Sprite.png", "desc": "A device for catching wild Pokémon. It is thrown like a ball."},
            {"item_id": 7, "name": "Max Potion", "category": "Potions", "price": 2500, "stock": -1, "rarity": "Epic", "image": "https://archives.bulbagarden.net/media/upload/a/a2/Dream_Max_Potion_Sprite.png", "desc": "Fully restores HP. Spray type liquid medicine."},
            {"item_id": 8, "name": "Hyper Potion", "category": "Potions", "price": 1500, "stock": -1, "rarity": "Rare", "image": "https://archives.bulbagarden.net/media/upload/c/c8/Dream_Hyper_Potion_Sprite.png", "desc": "Restores HP by 120 points. Spray type liquid medicine."},
            {"item_id": 9, "name": "Super Potion", "category": "Potions", "price": 700, "stock": -1, "rarity": "Uncommon", "image": "https://archives.bulbagarden.net/media/upload/5/57/Dream_Super_Potion_Sprite.png", "desc": "Restores HP by 60 points. Spray type liquid medicine."},
            {"item_id": 10, "name": "Potion", "category": "Potions", "price": 300, "stock": -1, "rarity": "Common", "image": "https://archives.bulbagarden.net/media/upload/d/df/Dream_Potion_Sprite.png", "desc": "Restores HP by 20 points. Spray type liquid medicine."},
            {"item_id": 12, "name": "Revive", "category": "Battle Items", "price": 1500, "stock": -1, "rarity": "Rare", "image": "https://archives.bulbagarden.net/media/upload/8/8c/Dream_Revive_Sprite.png", "desc": "Revives a fainted Pokémon, restoring 50% of its max HP."},
            {"item_id": 13, "name": "Max Revive", "category": "Battle Items", "price": 4000, "stock": -1, "rarity": "Epic", "image": "https://archives.bulbagarden.net/media/upload/4/45/Dream_Max_Revive_Sprite.png", "desc": "Revives a fainted Pokémon, fully restoring its HP."},
            {"item_id": 14, "name": "Rare Candy", "category": "Battle Items", "price": 10000, "stock": -1, "rarity": "Legendary", "image": "https://archives.bulbagarden.net/media/upload/0/02/Dream_Rare_Candy_Sprite.png", "desc": "A candy that raises the level of a single Pokémon by one."},
            {"item_id": 16, "name": "Fire Stone", "category": "Evolution Stones", "price": 3000, "stock": -1, "rarity": "Rare", "image": "https://archives.bulbagarden.net/media/upload/9/92/Dream_Fire_Stone_Sprite.png", "desc": "A peculiar stone that can make certain Pokémon evolve."},
            {"item_id": 17, "name": "Water Stone", "category": "Evolution Stones", "price": 3000, "stock": -1, "rarity": "Rare", "image": "https://archives.bulbagarden.net/media/upload/2/29/Dream_Water_Stone_Sprite.png", "desc": "A peculiar stone that can make certain Pokémon evolve."},
            {"item_id": 18, "name": "Thunder Stone", "category": "Evolution Stones", "price": 3000, "stock": -1, "rarity": "Rare", "image": "https://archives.bulbagarden.net/media/upload/a/a5/Dream_Thunder_Stone_Sprite.png", "desc": "A peculiar stone that can make certain Pokémon evolve."},
            {"item_id": 22, "name": "Sitrus Berry", "category": "Berries", "price": 200, "stock": -1, "rarity": "Uncommon", "image": "https://archives.bulbagarden.net/media/upload/a/aa/Dream_Sitrus_Berry_Sprite.png", "desc": "A Berry that restores 25% of maximum HP when consumed."},
            {"item_id": 23, "name": "Oran Berry", "category": "Berries", "price": 80, "stock": -1, "rarity": "Common", "image": "https://archives.bulbagarden.net/media/upload/0/0c/Dream_Oran_Berry_Sprite.png", "desc": "A Berry that restores HP by 10 points when consumed."}
        ]

        for item in shop_items:
            ShopItem.objects.get_or_create(
                item_id=item["item_id"],
                defaults={
                    "name": item["name"],
                    "description": item["desc"],
                    "category": item["category"],
                    "price": item["price"],
                    "stock": item["stock"],
                    "rarity": item["rarity"],
                    "image": item["image"]
                }
            )
        self.stdout.write(self.style.SUCCESS(f'Populated {len(shop_items)} Shop Items'))

        # 3. DEFAULT MISSIONS
        missions = [
            {"title": "Catch 5 Pokémon", "desc": "Capture wild Pokémon in the arena or map to expand your roster.", "type": "daily", "xp": 500, "coins": 200, "items": {"Poke Ball": 5}},
            {"title": "Win 3 Battles", "desc": "Challenge and defeat opponents in the battle arena.", "type": "daily", "xp": 800, "coins": 400, "items": {"Super Potion": 2}},
            {"title": "Elite Conqueror", "desc": "Win 15 battles to show your trainer dominance.", "type": "weekly", "xp": 2500, "coins": 1500, "items": {"Ultra Ball": 10}},
            {"title": "Unlock Johto Region", "desc": "Complete Kanto and proceed to unlock Johto on the Kingdom Map.", "type": "story", "xp": 5000, "coins": 3000, "pokemon": {"pokedex_number": 150, "name": "Mewtwo", "level": 70, "type1": "Psychic", "rarity": "Legendary"}}
        ]

        for m in missions:
            Mission.objects.get_or_create(
                title=m["title"],
                defaults={
                    "description": m["desc"],
                    "type": m["type"],
                    "reward_xp": m["xp"],
                    "reward_coins": m["coins"],
                    "reward_items": m.get("items", {}),
                    "reward_pokemon": m.get("pokemon", {})
                }
            )
        self.stdout.write(self.style.SUCCESS(f'Populated {len(missions)} Missions'))

        # 4. DEFAULT ACHIEVEMENTS
        Achievement.objects.all().delete()
        achievements = [
            {"title": "First Victory", "desc": "Win your first battle in any mode.", "category": "Battle", "points": 10, "target_value": 1, "xp_reward": 50, "coins_reward": 100, "crystal_reward": 10, "rarity": "Common", "badge_image": "first_victory"},
            {"title": "Pokémon Collector", "desc": "Catch 100 Pokémon.", "category": "Collection", "points": 50, "target_value": 100, "xp_reward": 200, "coins_reward": 500, "crystal_reward": 20, "rarity": "Rare", "badge_image": "pokemon_collector"},
            {"title": "Gym Challenger", "desc": "Defeat 10 Gym Leaders.", "category": "Gym", "points": 100, "target_value": 10, "xp_reward": 150, "coins_reward": 300, "crystal_reward": 15, "rarity": "Rare", "badge_image": "gym_challenger"},
            {"title": "Explorer", "desc": "Visit 50 unique locations.", "category": "Exploration", "points": 50, "target_value": 50, "xp_reward": 120, "coins_reward": 250, "crystal_reward": 12, "rarity": "Epic", "badge_image": "explorer"},
            {"title": "Battle Master", "desc": "Win 100 battles.", "category": "Battle", "points": 200, "target_value": 100, "xp_reward": 300, "coins_reward": 600, "crystal_reward": 25, "rarity": "Epic", "badge_image": "battle_master"},
            {"title": "Legendary Hunter", "desc": "Catch a Legendary Pokémon.", "category": "Legendary", "points": 300, "target_value": 1, "xp_reward": 500, "coins_reward": 1000, "crystal_reward": 50, "rarity": "Legendary", "badge_image": "legendary_hunter"},
            {"title": "Daily Login Streak", "desc": "Login for 30 consecutive days.", "category": "Login", "points": 150, "target_value": 30, "xp_reward": 300, "coins_reward": 400, "crystal_reward": 20, "rarity": "Legendary", "badge_image": "daily_login_streak"},
            {"title": "Ultimate Champion", "desc": "Defeat the Elite Four.", "category": "Battle", "points": 500, "target_value": 1, "xp_reward": 1000, "coins_reward": 2000, "crystal_reward": 100, "rarity": "Mythic", "badge_image": "ultimate_champion"},
        ]

        for ach in achievements:
            Achievement.objects.create(
                title=ach["title"],
                description=ach["desc"],
                category=ach["category"],
                points=ach["points"],
                target_value=ach["target_value"],
                xp_reward=ach["xp_reward"],
                coins_reward=ach["coins_reward"],
                crystal_reward=ach["crystal_reward"],
                rarity=ach["rarity"],
                badge_image=ach["badge_image"]
            )
        self.stdout.write(self.style.SUCCESS(f'Populated {len(achievements)} Achievements'))

        # 5. SAMPLE TRAINERS & STARTER POKÉMON
        trainers = [
            {"email": "red@pokemonnexus.com", "name": "Red", "role": "trainer", "lvl": 100, "xp": 0, "coins": 50000, "wins": 250, "losses": 5, "rank": "Master", "region": "Kanto"},
            {"email": "ash@pokemonnexus.com", "name": "Ash Ketchum", "role": "trainer", "lvl": 80, "xp": 400, "coins": 1500, "wins": 120, "losses": 50, "rank": "Diamond", "region": "Kanto"},
            {"email": "misty@pokemonnexus.com", "name": "Misty", "role": "player", "lvl": 45, "xp": 300, "coins": 2000, "wins": 45, "losses": 30, "rank": "Gold", "region": "Kanto"},
            {"email": "brock@pokemonnexus.com", "name": "Brock", "role": "trainer", "lvl": 42, "xp": 100, "coins": 1800, "wins": 35, "losses": 40, "rank": "Silver", "region": "Kanto"}
        ]

        for t in trainers:
            u, u_created = User.objects.get_or_create(
                username=t["email"],
                defaults={
                    'email': t["email"],
                    'first_name': t["name"]
                }
            )
            if u_created:
                u.set_password('trainerpass123')
                u.save()
                
            p, p_created = TrainerProfile.objects.get_or_create(
                user=u,
                defaults={
                    "trainer_name": t["name"],
                    "role": t["role"],
                    "level": t["lvl"],
                    "xp": t["xp"],
                    "coins": t["coins"],
                    "wins": t["wins"],
                    "losses": t["losses"],
                    "battles_played": t["wins"] + t["losses"],
                    "current_rank": t["rank"],
                    "region": t["region"]
                }
            )
            if u_created:
                self.stdout.write(self.style.SUCCESS(f"Created Sample Trainer: {t['name']} ({t['email']})"))

                # Assign starting team to Ash (to match battle.html hardcoded party!)
                if t["name"] == "Ash Ketchum":
                    ash_team = [
                        {"name": "Pikachu", "lvl": 80, "id": 25, "type1": "Electric", "hp": 230, "max_hp": 230, "moves": [
                            {"name": "Thunderbolt", "type": "Electric", "pp": "15/15"},
                            {"name": "Quick Attack", "type": "Normal", "pp": "30/30"},
                            {"name": "Iron Tail", "type": "Steel", "pp": "15/15"},
                            {"name": "Electro Ball", "type": "Electric", "pp": "10/10"}
                        ], "rarity": "Common"},
                        {"name": "Charizard", "lvl": 82, "id": 6, "type1": "Fire", "hp": 240, "max_hp": 240, "moves": [
                            {"name": "Flamethrower", "type": "Fire", "pp": "15/15"},
                            {"name": "Air Slash", "type": "Flying", "pp": "20/20"},
                            {"name": "Dragon Claw", "type": "Dragon", "pp": "15/15"},
                            {"name": "Fire Blast", "type": "Fire", "pp": "5/5"}
                        ], "rarity": "Rare"},
                        {"name": "Garchomp", "lvl": 80, "id": 445, "type1": "Dragon", "hp": 280, "max_hp": 280, "moves": [
                            {"name": "Earthquake", "type": "Ground", "pp": "10/10"},
                            {"name": "Dragon Rush", "type": "Dragon", "pp": "10/10"},
                            {"name": "Slash", "type": "Normal", "pp": "20/20"},
                            {"name": "Stone Edge", "type": "Ground", "pp": "5/5"}
                        ], "rarity": "Epic"},
                        {"name": "Lucario", "lvl": 80, "id": 448, "type1": "Fighting", "hp": 210, "max_hp": 210, "moves": [
                            {"name": "Aura Sphere", "type": "Fighting", "pp": "20/20"},
                            {"name": "Close Combat", "type": "Fighting", "pp": "5/5"},
                            {"name": "Extreme Speed", "type": "Normal", "pp": "5/5"},
                            {"name": "Metal Claw", "type": "Steel", "pp": "35/35"}
                        ], "rarity": "Rare"},
                        {"name": "Gardevoir", "lvl": 79, "id": 282, "type1": "Psychic", "hp": 220, "max_hp": 220, "moves": [
                            {"name": "Psychic", "type": "Psychic", "pp": "10/10"},
                            {"name": "Moonblast", "type": "Fairy", "pp": "15/15"},
                            {"name": "Shadow Ball", "type": "Dark", "pp": "15/15"},
                            {"name": "Calm Mind", "type": "Normal", "pp": "20/20"}
                        ], "rarity": "Rare"},
                        {"name": "Zeraora", "lvl": 79, "id": 807, "type1": "Electric", "hp": 200, "max_hp": 200, "moves": [
                            {"name": "Plasma Fists", "type": "Electric", "pp": "15/15"},
                            {"name": "Close Combat", "type": "Fighting", "pp": "5/5"},
                            {"name": "Thunder Punch", "type": "Electric", "pp": "15/15"},
                            {"name": "Volt Switch", "type": "Electric", "pp": "20/20"}
                        ], "rarity": "Legendary"}
                    ]

                    for pkmn in ash_team:
                        CapturedPokemon.objects.create(
                            trainer=p,
                            pokemon_id=str(pkmn["id"]),
                            pokedex_number=pkmn["id"],
                            name=pkmn["name"],
                            type1=pkmn["type1"],
                            rarity=pkmn["rarity"],
                            level=pkmn["lvl"],
                            hp=pkmn["hp"],
                            max_hp=pkmn["max_hp"],
                            attack=80, defense=80, speed=80, special_attack=80, special_defense=80,
                            moves=pkmn["moves"],
                            image=f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pkmn['id']}.png",
                            is_in_party=True
                        )
                    self.stdout.write(self.style.SUCCESS("Assigned Starter Pokémon party to Ash Ketchum."))

        self.stdout.write(self.style.SUCCESS('Successfully populated game data!'))
