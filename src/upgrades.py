import pygame
from settings import *

class Upgrade:
	def __init__(self, name, description, apply_effect):
		self.name = name
		self.description = description
		self.apply_effect = apply_effect


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

def apply_overclock(player):
	player.attack_cooldown_multiplier *= OVERCLOCK_COOLDOWN_MULTIPLIER
	player.damage *= OVERCLOCK_DAMAGE_MULTIPLIER

def apply_glass_cannon(player):
	player.damage *= GLASS_CANNON_DAMAGE_MULTIPLIER
	player.max_health = max(1, player.max_health - GLASS_CANNON_HEALTH_REDUCTION)
	player.health = min(player.health, player.max_health)

def apply_iron_skin(player):
	player.hit_invulnerability_ms += IRON_SKIN_INVULNERABILITY_BONUS_MS


def create_upgrade_pool():
	return [
		Upgrade("Twin Shot", "Fire an additional bullet in a spread", apply_twin_shot),
		Upgrade("Piercing Rounds", "Bullets pass through an extra enemy", apply_piercing_rounds),
		Upgrade("Explosive Rounds", "Bullets detonate, damaging nearby enemies", apply_explosive_rounds),
		Upgrade("Vampiric Rounds", "Killing an enemy restores health", apply_vampiric_rounds),
		Upgrade("Adrenaline Rush", "Move faster", apply_adrenaline_rush),
		Upgrade("Second Wind", "Gain a shield that blocks the next hit", apply_second_wind),
		Upgrade("Overclock", "Fire much faster but each shot is weaker", apply_overclock),
		Upgrade("Glass Cannon", "Deal far more damage but lose health", apply_glass_cannon),
		Upgrade("Iron Skin", "Take hits less often", apply_iron_skin),
	]


class UpgradeCard:
	def __init__(self, upgrade, x, y, accent_colour):
		self.upgrade = upgrade
		self.rect = pygame.Rect(x, y, UPGRADE_CARD_WIDTH, UPGRADE_CARD_HEIGHT)
		self.accent_colour = accent_colour
		self.hovered = False

	def update(self, mouse_pos):
		self.hovered = self.rect.collidepoint(mouse_pos)

	def clicked(self, event):
		return (
			event.type == pygame.MOUSEBUTTONDOWN
			and event.button == 1
			and self.rect.collidepoint(event.pos)
		)

	def wrap_text(self, text, font, max_width):
		words = text.split(" ")
		lines = []
		current_line = ""
		for word in words:
			test_line = f"{current_line} {word}".strip()
			if font.size(test_line)[0] <= max_width:
				current_line = test_line
			else:
				lines.append(current_line)
				current_line = word
		if current_line:
			lines.append(current_line)
		return lines

	def draw(self, surface, title_font, body_font):
		background_colour = self.accent_colour if self.hovered else "#2B2B3A"
		pygame.draw.rect(surface, background_colour, self.rect, border_radius=UPGRADE_CARD_CORNER_RADIUS)
		pygame.draw.rect(surface, self.accent_colour, self.rect, width=3, border_radius=UPGRADE_CARD_CORNER_RADIUS)

		title_surf = title_font.render(self.upgrade.name, True, "white")
		surface.blit(title_surf, title_surf.get_rect(midtop=(self.rect.centerx, self.rect.top + 20)))

		line_y = self.rect.top + 80
		for line in self.wrap_text(self.upgrade.description, body_font, self.rect.width - 40):
			line_surf = body_font.render(line, True, "white")
			surface.blit(line_surf, line_surf.get_rect(midtop=(self.rect.centerx, line_y)))
			line_y += body_font.get_height()
