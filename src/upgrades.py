import pygame
from settings import *

class Upgrade:
	"""A single choosable upgrade: its display name/description and the effect function to apply."""
	def __init__(self, name, description, apply_effect, image_path=None):
		self.name = name
		self.description = description
		self.apply_effect = apply_effect
		self.image_path = image_path


def apply_twin_shot(player):
	player.extra_bullets += 1

def apply_piercing_rounds(player):
	player.bullet_pierce += PIERCE_ROUNDS_EXTRA_PIERCE

def apply_explosive_rounds(player):
	player.explosive_rounds = True

def apply_vampiric_rounds(player):
	player.lifesteal_amount += VAMPIRIC_HEAL_AMOUNT

def apply_adrenaline_rush(player):
	player.speed += ADRENALINE_SPEED_BOOST

def apply_second_wind(player):
	player.shield_charges += SECOND_WIND_SHIELD_CHARGES

# shoots faster but each shot deals less damage
def apply_overclock(player):
	player.attack_cooldown_multiplier *= OVERCLOCK_COOLDOWN_MULTIPLIER
	player.damage *= OVERCLOCK_DAMAGE_MULTIPLIER

# big damage boost in exchange for lower max health, clamped so max health can't drop below 1
def apply_glass_cannon(player):
	player.damage *= GLASS_CANNON_DAMAGE_MULTIPLIER
	player.max_health = max(1, player.max_health - GLASS_CANNON_HEALTH_REDUCTION)
	player.health = min(player.health, player.max_health)

def apply_iron_skin(player):
	player.hit_invulnerability_ms += IRON_SKIN_INVULNERABILITY_BONUS_MS


# builds a fresh list of every available upgrade, ready to be sampled from
def create_upgrade_pool():
	return [
		Upgrade("Twin Shot", "Fire an additional bullet in a spread", apply_twin_shot, "images/Twin_card.png"),
		Upgrade("Piercing Rounds", "Bullets pass through an extra enemy", apply_piercing_rounds, "images/Pierce_card.png"),
		Upgrade("Explosive Rounds", "Bullets detonate, damaging nearby enemies", apply_explosive_rounds, "images/Explode_card.png"),
		Upgrade("Vampiric Rounds", "Killing an enemy restores health", apply_vampiric_rounds, "images/vamp_card.png"),
		Upgrade("Adrenaline Rush", "Move faster", apply_adrenaline_rush),
		Upgrade("Second Wind", "Gain a shield that blocks the next hit", apply_second_wind),
		Upgrade("Overclock", "Fire much faster but each shot is weaker", apply_overclock),
		Upgrade("Glass Cannon", "Deal far more damage but lose health", apply_glass_cannon),
		Upgrade("Iron Skin", "Take hits less often", apply_iron_skin),
	]


class UpgradeCard:
	"""A clickable card shown in the upgrade menu, displaying one upgrade's name and description."""
	def __init__(self, upgrade, x, y, accent_colour):
		self.upgrade = upgrade
		self.rect = pygame.Rect(x, y, UPGRADE_CARD_WIDTH, UPGRADE_CARD_HEIGHT)
		self.accent_colour = accent_colour
		self.hovered = False
		self.image = None
		self.hover_image = None
		if upgrade.image_path:
			image = pygame.image.load(upgrade.image_path).convert_alpha()
			self.image = pygame.transform.scale(image, (self.rect.width, self.rect.height))
			hover_size = (int(self.rect.width * 1.05), int(self.rect.height * 1.05))
			self.hover_image = pygame.transform.scale(image, hover_size)

	def update(self, mouse_pos):
		self.hovered = self.rect.collidepoint(mouse_pos)

	def clicked(self, event):
		return (
			event.type == pygame.MOUSEBUTTONDOWN
			and event.button == 1
			and self.rect.collidepoint(event.pos)
		)

	# draws the card art if this upgrade has one, otherwise a solid placeholder block
	def draw(self, surface):
		if self.image:
			img = self.hover_image if self.hovered else self.image
			surface.blit(img, img.get_rect(center=self.rect.center))
		else:
			background_colour = self.accent_colour if self.hovered else "#2B2B3A"
			pygame.draw.rect(surface, background_colour, self.rect, border_radius=UPGRADE_CARD_CORNER_RADIUS)
