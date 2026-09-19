import pygame
from settings import (
	HUD_PADDING, UPGRADE_BODY_FONT_SIZE, UPGRADE_OVERLAY_ALPHA,
	PAUSE_TITLE_FONT_SIZE, PAUSE_BODY_FONT_SIZE, PAUSE_TOP_MARGIN, PAUSE_LINE_SPACING,
	LOW_HEALTH_TINT_MAX_ALPHA, LOW_HEALTH_TINT_THRESHOLD,
	WEAPON_DATA, WEAPON_ICON_SIZE, WEAPON_ICON_SPACING, WEAPON_ICON_CORNER_RADIUS,
)


class HUD:
	"""Draws everything shown over the game world: stats, the weapon bar, the low-health tint and the pause/upgrade overlays."""
	def __init__(self, screen, weapon_icons):
		self.screen = screen
		self.weapon_icons = weapon_icons
		self.body_font = pygame.font.SysFont("SimSun", UPGRADE_BODY_FONT_SIZE)
		self.pause_title_font = pygame.font.SysFont("SimSun", PAUSE_TITLE_FONT_SIZE)
		self.pause_body_font = pygame.font.SysFont("SimSun", PAUSE_BODY_FONT_SIZE)
		self.damage_tint = pygame.Surface(screen.get_size())
		self.damage_tint.fill("#B00000")

	# tints the screen red below the health threshold, getting stronger the closer the player is to dying
	def draw_damage_tint(self, player):
		health_ratio = max(player.health, 0) / player.max_health
		strength = 1 - health_ratio / LOW_HEALTH_TINT_THRESHOLD
		if strength > 0:
			self.damage_tint.set_alpha(int(LOW_HEALTH_TINT_MAX_ALPHA * strength))
			self.screen.blit(self.damage_tint, (0, 0))

	# draws money, health and round/timer text in the top-left corner
	def draw_stats(self, player, round_number, time_left):
		money_surf = self.body_font.render(f"${player.money}", True, "white")
		self.screen.blit(money_surf, (HUD_PADDING, HUD_PADDING))
		health_surf = self.body_font.render(f"HP {player.health}/{player.max_health}", True, "white")
		self.screen.blit(health_surf, (HUD_PADDING, HUD_PADDING + money_surf.get_height() + 4))
		round_surf = self.body_font.render(f"Round {round_number} - {int(time_left)}s", True, "white")
		self.screen.blit(round_surf, (HUD_PADDING, HUD_PADDING + (money_surf.get_height() + 4) * 2))

	# draws the row of weapon icons in the top-right, highlighting the currently equipped one
	def draw_weapon_bar(self, player):
		weapon_keys = player.weapon_keys
		total_width = len(weapon_keys) * WEAPON_ICON_SIZE + (len(weapon_keys) - 1) * WEAPON_ICON_SPACING
		start_x = self.screen.get_width() - total_width - HUD_PADDING
		for i, key in enumerate(weapon_keys):
			rect = pygame.Rect(start_x + i * (WEAPON_ICON_SIZE + WEAPON_ICON_SPACING), HUD_PADDING, WEAPON_ICON_SIZE, WEAPON_ICON_SIZE)
			self.draw_weapon_icon(key, rect)
			border_colour = "white" if i == player.weapon_index else "#444444"
			pygame.draw.rect(self.screen, border_colour, rect, width=3, border_radius=WEAPON_ICON_CORNER_RADIUS)

	# draws a weapon's icon, or a coloured square with its first letter if it has no icon
	def draw_weapon_icon(self, key, rect):
		icon = self.weapon_icons.get(key)
		if icon is not None:
			self.screen.blit(icon, rect)
		else:
			pygame.draw.rect(self.screen, WEAPON_DATA[key]["colour"], rect, border_radius=WEAPON_ICON_CORNER_RADIUS)
			label_surf = self.body_font.render(key[:1].upper(), True, "black")
			self.screen.blit(label_surf, label_surf.get_rect(center=rect.center))

	# darkens the whole screen so an overlay stands out
	def draw_dark_overlay(self):
		overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
		overlay.fill((0, 0, 0, UPGRADE_OVERLAY_ALPHA))
		self.screen.blit(overlay, (0, 0))

	# darkens the screen and draws/updates the current round's upgrade cards
	def draw_upgrade_menu(self, cards):
		self.draw_dark_overlay()
		mouse_pos = pygame.mouse.get_pos()
		for card in cards:
			card.update(mouse_pos)
			card.draw(self.screen)

	# draws the paused-game overlay: title, current round, the upgrades collected so far and the pause buttons
	def draw_pause_menu(self, player, round_number, buttons):
		self.draw_dark_overlay()
		w = self.screen.get_width()

		title_surf = self.pause_title_font.render("Paused", True, "white")
		self.screen.blit(title_surf, title_surf.get_rect(midtop=(w // 2, PAUSE_TOP_MARGIN)))

		round_surf = self.pause_body_font.render(f"Round {round_number}", True, "white")
		round_y = PAUSE_TOP_MARGIN + title_surf.get_height() + PAUSE_LINE_SPACING
		self.screen.blit(round_surf, round_surf.get_rect(midtop=(w // 2, round_y)))

		list_top = round_y + round_surf.get_height() + PAUSE_LINE_SPACING
		if player.chosen_upgrades:
			heading_surf = self.pause_body_font.render("Upgrades collected:", True, "white")
			self.screen.blit(heading_surf, heading_surf.get_rect(midtop=(w // 2, list_top)))
			for i, name in enumerate(player.chosen_upgrades):
				line_surf = self.pause_body_font.render(name, True, "#63A375")
				line_y = list_top + heading_surf.get_height() + PAUSE_LINE_SPACING + i * PAUSE_LINE_SPACING
				self.screen.blit(line_surf, line_surf.get_rect(midtop=(w // 2, line_y)))
		else:
			none_surf = self.pause_body_font.render("No upgrades collected yet", True, "white")
			self.screen.blit(none_surf, none_surf.get_rect(midtop=(w // 2, list_top)))

		mouse_pos = pygame.mouse.get_pos()
		for button in buttons:
			button.update(mouse_pos)
			button.draw(self.screen)
