import random
import pygame
from sprites import SpriteSheet, CameraGroup, Player, WeaponSprite, Zombie, Runner, Brute, Boss
from ui import Button, play_music, set_sfx_volume
from upgrades import create_upgrade_pool, UpgradeCard
from database import Database
from level import Level
from hud import HUD
from menus import MainMenu, SettingsMenu, LoginMenu, LeaderboardMenu, StatsMenu, ShopMenu, AdminMenu, GameOverScreen
from settings import (
	ROUND_DURATION_SECONDS, ROUND_COMPLETION_REWARD, UPGRADE_CARDS_PER_ROUND,
	UPGRADE_CARD_WIDTH, UPGRADE_CARD_HEIGHT, UPGRADE_CARD_SPACING, UPGRADE_CARD_ACCENT_COLOURS,
	WEAPON_DATA, WEAPON_SPRITE_SHEET_PATH, WEAPON_ICON_SPRITE_COORDS, WEAPON_ICON_SIZE,
	DEFAULT_KEYBINDS, DEFAULT_VOLUME, DEFAULT_SFX_VOLUME, PAUSE_MUSIC_PATH,
)

ENEMY_CLASSES = [Zombie, Runner, Brute, Boss]


class Game:
	"""Owns the window and game state: runs gameplay (levels, rounds, upgrades) and switches between the menu screens."""
	# sets up the window, pause buttons, HUD, database connection and menu screens
	def __init__(self):
		pygame.init()
		info = pygame.display.Info()
		self.screen = pygame.display.set_mode((info.current_w,(info.current_h)), pygame.NOFRAME)
		self.clock = pygame.time.Clock()
		self.dt = 0
		self.sprite_sheets = {}
		self.ground_sprite_sheet = SpriteSheet("images/tiles/floor.png")
		self.map = "src/Maps/Map1.txt"
		self.running = True
		self.state = "menu"
		pygame.mouse.set_cursor(*pygame.cursors.broken_x)

		w, h = self.screen.get_size()
		self.resume_button = Button("images/buttons/resume.png", w // 2, h // 2 + 20, scale=2.5)
		self.settings_button = Button("images/buttons/settings.png", w // 2, h // 2 + 160, scale=2.5)
		self.exit_button = Button("images/buttons/exit.png", w // 2, h // 2 + 300, scale=2.5)
		self.upgrade_menu_open = False
		self.paused = False
		self.weapon_icons = self.load_weapon_icons()
		self.hud = HUD(self.screen, self.weapon_icons)
		self.db = Database()
		self.current_user = None
		self.kill_count = 0
		self.game_start_ticks = 0
		self.last_run_stats = {"time_alive": 0, "rounds_passed": 0, "kills": 0, "money": 0, "upgrades": []}
		self.mouse_held = False
		self.keybinds = dict(DEFAULT_KEYBINDS)
		self.volume = DEFAULT_VOLUME
		pygame.mixer.music.set_volume(self.volume)
		self.sfx_volume = DEFAULT_SFX_VOLUME
		set_sfx_volume(self.sfx_volume)
		menus = [MainMenu(self), SettingsMenu(self), LoginMenu(self), LeaderboardMenu(self), StatsMenu(self), ShopMenu(self), AdminMenu(self), GameOverScreen(self)]
		self.menus = {menu.STATE: menu for menu in menus}

	# slices each weapon's icon from the sprite sheet (empty dict if the sheet is missing)
	def load_weapon_icons(self):
		icons = {}
		try:
			sheet = SpriteSheet(WEAPON_SPRITE_SHEET_PATH, alpha=True)
		except (pygame.error, FileNotFoundError):
			return icons
		for key, (sprite_x, sprite_y) in WEAPON_ICON_SPRITE_COORDS.items():
			icons[key] = sheet.get_sprite(sprite_x, sprite_y, WEAPON_ICON_SIZE, WEAPON_ICON_SIZE)
		return icons

	# free weapons are always owned; signed-in users also get the ones they've bought
	def get_owned_weapons(self):
		owned = {key: True for key, weapon in WEAPON_DATA.items() if weapon["price"] == 0}
		if self.current_user:
			owned.update(self.db.get_weapons(self.current_user))
		return owned

	# the equipped weapons the player starts a run with, kept in WEAPON_DATA order
	def get_loadout(self):
		owned = self.get_owned_weapons()
		return [key for key in WEAPON_DATA if owned.get(key)]

	# loads and caches character sprite sheets so each one is only read from disk once
	def get_sprite_sheet(self, path):
		if path not in self.sprite_sheets:
			self.sprite_sheets[path] = SpriteSheet(path, alpha=True)
		return self.sprite_sheets[path]

	# switches to a different map file and restarts the level on it
	def change_map(self, new_map):
		self.map = new_map
		self.new()

	# builds the level from the map file, then places the player and the first round's enemies
	def create_level(self):
		self.level = Level(self, self.map)
		self.player = Player(self, *self.level.spawn)
		self.weapon_sprite = WeaponSprite(self, self.player)
		self.spawn_enemies()

	# spawns each enemy type's round-appropriate count at random reachable tiles.
	# when the round asks for more than 100 enemies every type is scaled down by the same
	# fraction, so the mix stays the same and a type that's due still gets at least one
	##### GROUP A - Dynamic generation of objects (enemy types and counts chosen at run time) #####
	def spawn_enemies(self):
		spawn_pool = list(self.level.reachable_tiles) if self.level.reachable_tiles else self.level.valid_tiles
		counts = [enemy_class.count_for_round(self.round_number) for enemy_class in ENEMY_CLASSES]
		total = sum(counts)
		if total > 100:
			counts = [max(1, count * 100 // total) if count else 0 for count in counts]
		for enemy_class, count in zip(ENEMY_CLASSES, counts):
			for i in range(count):
				x, y = random.choice(spawn_pool)
				enemy_class(self, x, y)

	# resets all game state for a fresh run (sprite groups, round counter, etc.) and builds the level
	def new(self):
		self.playing = True
		self.all_sprites = CameraGroup(self)
		self.ground_sprites = pygame.sprite.Group()
		self.enemies = pygame.sprite.Group()
		self.blocks = pygame.sprite.Group()
		self.bullets = pygame.sprite.Group()
		self.available_upgrade_pool = create_upgrade_pool()
		self.round_number = 1
		self.round_time_remaining = ROUND_DURATION_SECONDS
		self.upgrade_menu_open = False
		self.upgrade_cards = []
		self.paused = False
		self.kill_count = 0
		self.game_start_ticks = pygame.time.get_ticks()
		self.mouse_held = False
		self.create_level()

	##### GROUP B - Records (one run stored as a set of named fields) #####
	# records the run's stats when the player dies, and saves the score and money if they're logged in
	def finalize_run(self):
		time_alive = (pygame.time.get_ticks() - self.game_start_ticks) / 1000
		self.last_run_stats = {
			"time_alive": time_alive,
			"rounds_passed": self.round_number,
			"kills": self.kill_count,
			"money": self.player.money,
			"upgrades": list(self.player.chosen_upgrades),
		}
		if self.current_user:
			self.db.submit_score(self.current_user, time_alive, self.round_number, self.kill_count)
			self.db.add_money(self.current_user, self.player.money)

	# advances all sprites and ends the run if the player has died
	def update(self):
		self.all_sprites.update(self.dt)
		if self.player.health <= 0:
			self.playing = False
			self.state = "gameover"
			self.finalize_run()

	# handles gameplay input: pause, weapon switching, firing and upgrade card clicks
	def events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.playing = False
				self.running = False
			elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				if not self.upgrade_menu_open:
					self.paused = not self.paused
			elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
				self.mouse_held = False
			elif self.paused:
				if self.resume_button.clicked(event):
					self.paused = False
				elif self.settings_button.clicked(event):
					self.state = "settings"
					self.menus["settings"].run()
					# closing the window from settings quits the game instead of returning to it
					if self.running:
						self.state = "playing"
					else:
						self.playing = False
				elif self.exit_button.clicked(event):
					self.playing = False
					self.running = True
					self.state = "menu"
				continue
			elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
				if not self.upgrade_menu_open:
					self.player.switch_weapon()
			elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				if self.upgrade_menu_open:
					for card in self.upgrade_cards:
						if card.clicked(event):
							self.choose_upgrade(card)
							break
				else:
					self.mouse_held = True

	# draws the world, the HUD, and whichever overlay (upgrade menu / pause) is currently active
	def draw(self):
		self.all_sprites.custom_draw(self.player)
		self.hud.draw_damage_tint(self.player)
		self.hud.draw_stats(self.player, self.round_number, self.round_time_remaining)
		self.hud.draw_weapon_bar(self.player)
		if self.upgrade_menu_open:
			self.hud.draw_upgrade_menu(self.upgrade_cards)
		elif self.paused:
			self.hud.draw_pause_menu(self.player, self.round_number, (self.resume_button, self.settings_button, self.exit_button))
		pygame.display.update()

	# picks a random set of upgrade choices for the round, refilling the pool if it's run low
	def draw_upgrade_cards(self):
		if len(self.available_upgrade_pool) < UPGRADE_CARDS_PER_ROUND:
			self.available_upgrade_pool = create_upgrade_pool()
		return random.sample(self.available_upgrade_pool, UPGRADE_CARDS_PER_ROUND)

	# positions the upgrade cards evenly spaced and centred on screen
	def layout_upgrade_cards(self, cards):
		w, h = self.screen.get_size()
		card_count = len(cards)
		total_width = card_count * UPGRADE_CARD_WIDTH + (card_count - 1) * UPGRADE_CARD_SPACING
		start_x = (w - total_width) // 2
		y = (h - UPGRADE_CARD_HEIGHT) // 2
		self.upgrade_cards = [
			UpgradeCard(upgrade, start_x + i * (UPGRADE_CARD_WIDTH + UPGRADE_CARD_SPACING), y, UPGRADE_CARD_ACCENT_COLOURS[i % len(UPGRADE_CARD_ACCENT_COLOURS)])
			for i, upgrade in enumerate(cards)
		]

	# clears remaining enemies, pays the round reward and opens the upgrade menu when a round's timer runs out
	def start_round_end(self):
		for enemy in list(self.enemies):
			enemy.kill()
		self.player.money += ROUND_COMPLETION_REWARD * self.round_number
		self.upgrade_menu_open = True
		self.layout_upgrade_cards(self.draw_upgrade_cards())

	# applies the chosen upgrade, removes it from the pool, and starts the next round
	def choose_upgrade(self, card):
		card.upgrade.apply_effect(self.player)
		self.player.chosen_upgrades.append(card.upgrade.name)
		if card.upgrade in self.available_upgrade_pool:
			self.available_upgrade_pool.remove(card.upgrade)
		self.upgrade_menu_open = False
		self.round_number += 1
		self.round_time_remaining = ROUND_DURATION_SECONDS
		self.spawn_enemies()

	# core gameplay loop: input, update, draw, and the round timer
	def main(self):
		while self.playing:
			self.dt = self.clock.tick(120) / 1000
			self.events()
			play_music(PAUSE_MUSIC_PATH if self.paused else None)
			if not self.paused and not self.upgrade_menu_open:
				self.update()
				if self.mouse_held:
					self.player.shoot()
				self.round_time_remaining -= self.dt
				if self.round_time_remaining <= 0:
					self.start_round_end()
			self.draw()

	# switches between gameplay and whichever menu screen the current state names
	def run(self):
		while self.running:
			if self.state == "playing":
				self.new()
				self.main()
			elif self.state in self.menus:
				self.menus[self.state].run()
