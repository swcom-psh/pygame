from game.config import TILE_SIZE

item_types = {
    "it1" : {
        "name" : "heart",
        "hp" : 10,
        "max_hp" : 10,
        "speed" : 0,
        "attack_speed" : None,
        "attack_range" : 0,
        "damage" : 0,
        "max_damage" : 0,
        "min_damage" : 0,
        "size" : 0,
        "attack_type" : None,
        "texture" : "assets/item/heart.png"
    },
    "it2" : {
        "name" : "+1",
        "hp" : 0,
        "max_hp" : 0,
        "speed" : 0,
        "attack_speed" : 0.9,
        "attack_range" : 0,
        "damage" : 0,
        "max_damage" : 1,
        "min_damage" : 1,
        "size" : 0,
        "attack_type" : None,
        "texture" : "assets/item/+1.png"
    },
    "it3" : {
        "name" : "Ruler",
        "hp" : None,
        "max_hp" : None,
        "speed" : 0.125*(TILE_SIZE/50),
        "attack_speed" : None,
        "attack_range" : 0.5,
        "damage" : None,
        "max_damage" : 0,
        "min_damage" : 0,
        "size" : None,
        "attack_type" : None,
        "texture" : "assets/item/ruler.png"
    },
    "it4" : {
        "name" : "s",
        "hp" : None,
        "max_hp" : None,
        "speed" : TILE_SIZE*0.5,
        "attack_speed" : 0.9,
        "attack_range" : None,
        "damage" : None,
        "max_damage" : 0,
        "min_damage" : 0,
        "size" : None,
        "attack_type" : None,
        "texture" : "assets/item/hand_clock.png"
    },
    "it4" : {
        "name" : "x^2",
        "hp" : None,
        "max_hp" : None,
        "speed" : None,
        "attack_speed" : None,
        "attack_range" : None,
        "damage" : 0,
        "max_damage" : 0,
        "min_damage" : 0,
        "size" : None,
        "attack_type" : None,
        "sqauare_min_max_damage" : 1,
        "texture" : "assets/item/x^2.png"
    },
}

coin_types = {
    "+1" : {
        "value" : 1,
        "texture" : "assets/loot/coin.png" 
    }
}