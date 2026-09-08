import pygame
import sys
import random
from sprites import *
from upgrades import *
from settings import *
from database import Database

TILE_LEGEND = {
	"#": {"blocking": True},
	"D": {"ground": "dirt"},
	"W": {"ground": "water"},
}

def is_water_tile(grid, x, y):
	if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
		return grid[y][x] == "W"
	return False

def get_water_variant(grid, x, y):
	up = is_water_tile(grid, x, y - 1)
	down = is_water_tile(grid, x, y + 1)
	left = is_water_tile(grid, x - 1, y)
	right = is_water_tile(grid, x + 1, y)

	if not up and not left:
		return "water_top_left"
	if not up and not right:
		return "water_top_right"
	if not up:
		return "water_top"
	if not left:
		return "water_left"
	if not right:
		return "water_right"
	return "water"

class Queue:
	def __init__(self):
		self.items = []

	def enqueue(self, item):
		self.items.append(item)

	def dequeue(self):
		return self.items.pop(0)

	def is_empty(self):
		return len(self.items) == 0


def get_reachable_tiles(valid_tiles, start):
	valid_set = set(valid_tiles)
	visited = {start}
	queue = Queue()
	queue.enqueue(start)
	while not queue.is_empty():
		x, y = queue.dequeue()
		for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
			neighbour = (x + dx, y + dy)
			if neighbour in valid_set and neighbour not in visited:
				visited.add(neighbour)
				queue.enqueue(neighbour)
	return visited

class Game:
	def __init__(self):
		pygame.init()
		info = pygame.display.Info()
		self.screen = pygame.display.set_mode((info.current_w,(info.current_h - 60)), pygame.SCALED, pygame.RESIZABLE)
		self.clock = pygame.time.Clock()
		self.dt = 0
		#self.player_sprite_sheet = SpriteSheet(r"path for the spritesheet")
		self.zombie_sprite_sheet = SpriteSheet("images/zombie-sheet.png",alpha=True)
		self.ground_sprite_sheet = SpriteSheet("images/Floor.png")
		self.map = "src/Maps/Map1.txt"
		self.running = True
		self.state = "menu"
		pygame.mouse.set_cursor(*pygame.cursors.broken_x)

		w, h = self.screen.get_size()
		self.play_button = Button("images/Play_button.png", w // 2, h // 2 + 20, scale=2.5)
		self.settings_button = Button("images/Settings_button.png", w // 2, h // 2 + 160, scale=2.5)
		self.exit_button = Button("images/Exit_button.png", w // 2, h // 2 + 300, scale=2.5)
		self.upgrade_title_font = pygame.font.SysFont(None, UPGRADE_TITLE_FONT_SIZE)
		self.upgrade_body_font = pygame.font.SysFont(None, UPGRADE_BODY_FONT_SIZE)
		self.game_over_title_font = pygame.font.SysFont(None, GAME_OVER_TITLE_FONT_SIZE)
		self.game_over_body_font = pygame.font.SysFont(None, GAME_OVER_BODY_FONT_SIZE)
		self.pause_title_font = pygame.font.SysFont(None, PAUSE_TITLE_FONT_SIZE)
		self.pause_body_font = pygame.font.SysFont(None, PAUSE_BODY_FONT_SIZE)
		self.login_title_font = pygame.font.SysFont(None, LOGIN_TITLE_FONT_SIZE)
		self.login_body_font = pygame.font.SysFont(None, LOGIN_BODY_FONT_SIZE)
		self.leaderboard_title_font = pygame.font.SysFont(None, LEADERBOARD_TITLE_FONT_SIZE)
		self.leaderboard_header_font = pygame.font.SysFont(None, LEADERBOARD_HEADER_FONT_SIZE)
		self.leaderboard_row_font = pygame.font.SysFont(None, LEADERBOARD_ROW_FONT_SIZE)
		self.admin_title_font = pygame.font.SysFont(None, ADMIN_TITLE_FONT_SIZE)
		self.admin_header_font = pygame.font.SysFont(None, ADMIN_HEADER_FONT_SIZE)
		self.admin_row_font = pygame.font.SysFont(None, ADMIN_ROW_FONT_SIZE)
		self.menu_link_font = pygame.font.SysFont(None, MENU_LINK_FONT_SIZE)
		self.leaderboard_link_button = TextButton("Leaderboard", w - 110, 40, 180, 44, self.menu_link_font)
		self.upgrade_menu_open = False
		self.paused = False
		self.weapon_icons = self.load_weapon_icons()
		self.db = Database()
		self.current_user = None
		self.kill_count = 0
		self.game_start_ticks = 0
		self.last_run_stats = {"time_alive": 0, "rounds_passed": 0, "kills": 0}

	def load_weapon_icons(self):
		icons = {}
		try:
			sheet = SpriteSheet(WEAPON_SPRITE_SHEET_PATH, alpha=True)
		except (pygame.error, FileNotFoundError):
			return icons
		for key, (sprite_x, sprite_y) in WEAPON_ICON_SPRITE_COORDS.items():
			icons[key] = sheet.get_sprite(sprite_x, sprite_y, WEAPON_ICON_SIZE, WEAPON_ICON_SIZE)
		return icons

	def change_map(self, new_map):
		self.map = new_map
		self.new()

	def load_level(self, path):
		try:
			with open(path, "r") as f:
				return [line.rstrip("\n") for line in f]
		except FileNotFoundError:
			print(f"Level file not found: ({path})")
			return []

	def create_level(self):
		level = self.load_level(self.map)
		self.valid_tiles = []
		for i, row in enumerate(level):
			for j, tile in enumerate(row):
				info = TILE_LEGEND.get(tile)
				if info and info.get("ground") == "water":
					ground_key = get_water_variant(level, j, i)
				elif info and "ground" in info:
					ground_key = info["ground"]
				else:
					ground_key = "ground"
				Ground(self, j, i, ground_key)
				if info and info.get("blocking"):
					Block(self, j, i)
				if tile == ".":
					self.valid_tiles.append((j, i))

		height = len(level)
		width = max((len(row) for row in level), default=0)
		spawn = (width // 2, height // 2)
		self.player = Player(self, *spawn)
		self.weapon_sprite = WeaponSprite(self, self.player)

		self.reachable_tiles = get_reachable_tiles(self.valid_tiles, spawn)
		unreachable = set(self.valid_tiles) - self.reachable_tiles
		if unreachable:
			print(f"Warning: {len(unreachable)} unreachable tile(s) in {self.map}: {sorted(unreachable)}")

		self.spawn_enemies(self.spawn_count_for_round())

	def spawn_count_for_round(self):
		return STARTING_ENEMY_COUNT + (self.round_number - 1) * ENEMY_COUNT_PER_ROUND_GROWTH

	def spawn_enemies(self, count):
		spawn_pool = list(self.reachable_tiles) if self.reachable_tiles else self.valid_tiles
		for i in range(count):
			x, y = random.choice(spawn_pool)
			Enemy(self, x, y)

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
		self.create_level()

	def finalize_run(self):
		time_alive = (pygame.time.get_ticks() - self.game_start_ticks) / 1000
		self.last_run_stats = {"time_alive": time_alive, "rounds_passed": self.round_number, "kills": self.kill_count}
		if self.current_user:
			self.db.submit_score(self.current_user, time_alive, self.round_number, self.kill_count)

	def update(self):
		self.all_sprites.update(self.dt)
		if self.player.health <= 0:
			self.playing = False
			self.state = "gameover"
			self.finalize_run()

	def events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.playing = False
				self.running = False
			elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				if not self.upgrade_menu_open:
					self.paused = not self.paused
			elif self.paused:
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
					self.player.shoot()

	def draw(self):
		self.all_sprites.custom_draw(self.player)
		self.draw_hud()
		self.draw_weapon_hud()
		if self.upgrade_menu_open:
			self.draw_upgrade_menu_overlay()
		elif self.paused:
			self.draw_pause_menu_overlay()
		pygame.display.update()

	def draw_pause_menu_overlay(self):
		overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
		overlay.fill((0, 0, 0, UPGRADE_OVERLAY_ALPHA))
		self.screen.blit(overlay, (0, 0))
		w, h = self.screen.get_size()

		title_surf = self.pause_title_font.render("Paused", True, "white")
		self.screen.blit(title_surf, title_surf.get_rect(midtop=(w // 2, PAUSE_TOP_MARGIN)))

		round_surf = self.pause_body_font.render(f"Round {self.round_number}", True, "white")
		round_y = PAUSE_TOP_MARGIN + title_surf.get_height() + PAUSE_LINE_SPACING
		self.screen.blit(round_surf, round_surf.get_rect(midtop=(w // 2, round_y)))

		list_top = round_y + round_surf.get_height() + PAUSE_LINE_SPACING
		if self.player.chosen_upgrades:
			heading_surf = self.pause_body_font.render("Upgrades collected:", True, "white")
			self.screen.blit(heading_surf, heading_surf.get_rect(midtop=(w // 2, list_top)))
			for i, name in enumerate(self.player.chosen_upgrades):
				line_surf = self.pause_body_font.render(name, True, "#63A375")
				line_y = list_top + heading_surf.get_height() + PAUSE_LINE_SPACING + i * PAUSE_LINE_SPACING
				self.screen.blit(line_surf, line_surf.get_rect(midtop=(w // 2, line_y)))
		else:
			none_surf = self.pause_body_font.render("No upgrades collected yet", True, "white")
			self.screen.blit(none_surf, none_surf.get_rect(midtop=(w // 2, list_top)))

		prompt_surf = self.pause_body_font.render("Press ESC to resume", True, "white")
		self.screen.blit(prompt_surf, prompt_surf.get_rect(midbottom=(w // 2, h - PAUSE_TOP_MARGIN // 2)))

	def draw_hud(self):
		money_surf = self.upgrade_body_font.render(f"${self.player.money}", True, "white")
		self.screen.blit(money_surf, (HUD_PADDING, HUD_PADDING))
		health_surf = self.upgrade_body_font.render(f"HP {self.player.health}/{self.player.max_health}", True, "white")
		self.screen.blit(health_surf, (HUD_PADDING, HUD_PADDING + money_surf.get_height() + 4))
		round_surf = self.upgrade_body_font.render(f"Round {self.round_number} - {int(self.round_time_remaining)}s", True, "white")
		self.screen.blit(round_surf, (HUD_PADDING, HUD_PADDING + (money_surf.get_height() + 4) * 2))

	def draw_weapon_hud(self):
		weapon_keys = self.player.weapon_keys
		total_width = len(weapon_keys) * WEAPON_ICON_SIZE + (len(weapon_keys) - 1) * WEAPON_ICON_SPACING
		w, h = self.screen.get_size()
		start_x = w - total_width - HUD_PADDING
		for i, key in enumerate(weapon_keys):
			weapon = WEAPON_DATA[key]
			rect = pygame.Rect(start_x + i * (WEAPON_ICON_SIZE + WEAPON_ICON_SPACING), HUD_PADDING, WEAPON_ICON_SIZE, WEAPON_ICON_SIZE)
			icon = self.weapon_icons.get(key)
			if icon is not None:
				self.screen.blit(icon, rect)
			else:
				pygame.draw.rect(self.screen, weapon["colour"], rect, border_radius=WEAPON_ICON_CORNER_RADIUS)
				label_surf = self.upgrade_body_font.render(key[:1].upper(), True, "black")
				self.screen.blit(label_surf, label_surf.get_rect(center=rect.center))
			border_colour = "white" if i == self.player.weapon_index else "#444444"
			pygame.draw.rect(self.screen, border_colour, rect, width=3, border_radius=WEAPON_ICON_CORNER_RADIUS)

	def draw_upgrade_menu_overlay(self):
		overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
		overlay.fill((0, 0, 0, UPGRADE_OVERLAY_ALPHA))
		self.screen.blit(overlay, (0, 0))
		mouse_pos = pygame.mouse.get_pos()
		for card in self.upgrade_cards:
			card.update(mouse_pos)
			card.draw(self.screen, self.upgrade_title_font, self.upgrade_body_font)

	def draw_upgrade_cards(self):
		if len(self.available_upgrade_pool) < UPGRADE_CARDS_PER_ROUND:
			self.available_upgrade_pool = create_upgrade_pool()
		return random.sample(self.available_upgrade_pool, UPGRADE_CARDS_PER_ROUND)

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

	def start_round_end(self):
		for enemy in list(self.enemies):
			enemy.kill()
		self.upgrade_menu_open = True
		self.layout_upgrade_cards(self.draw_upgrade_cards())

	def choose_upgrade(self, card):
		card.upgrade.apply_effect(self.player)
		self.player.chosen_upgrades.append(card.upgrade.name)
		if card.upgrade in self.available_upgrade_pool:
			self.available_upgrade_pool.remove(card.upgrade)
		self.upgrade_menu_open = False
		self.round_number += 1
		self.round_time_remaining = ROUND_DURATION_SECONDS
		self.spawn_enemies(self.spawn_count_for_round())

	def main(self):
		while self.playing:
			self.dt = self.clock.tick(120) / 1000
			self.events()
			if not self.paused and not self.upgrade_menu_open:
				self.update()
				self.round_time_remaining -= self.dt
				if self.round_time_remaining <= 0:
					self.start_round_end()
			self.draw()

	def menu(self):
		while self.state == "menu" and self.running:
			mouse_pos = pygame.mouse.get_pos()

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = False
					self.state = None

				if self.play_button.clicked(event):
					self.state = "login"
				elif self.settings_button.clicked(event):
					self.state = "settings"
				elif self.exit_button.clicked(event):
					self.running = False
					self.state = None
				elif self.leaderboard_link_button.clicked(event):
					self.state = "leaderboard"

			self.play_button.update(mouse_pos)
			self.settings_button.update(mouse_pos)
			self.exit_button.update(mouse_pos)
			self.leaderboard_link_button.update(mouse_pos)

			self.screen.fill("#73D8E7")
			self.play_button.draw(self.screen)
			self.settings_button.draw(self.screen)
			self.exit_button.draw(self.screen)
			self.leaderboard_link_button.draw(self.screen)
			if self.current_user:
				user_surf = self.upgrade_body_font.render(f"Signed in as {self.current_user}", True, "black")
				self.screen.blit(user_surf, (HUD_PADDING, HUD_PADDING))

			pygame.display.update()
			self.clock.tick(60)

	def settings_menu(self):
		font = pygame.font.SysFont(None, 48)
		while self.state == "settings" and self.running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = False
					self.state = None
				if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
					self.state = "menu"

			self.screen.fill("black")
			text = font.render("(placeholder) press ESC to go back", True, "white")
			self.screen.blit(text, text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2)))
			pygame.display.update()
			self.clock.tick(60)

	def login_menu(self):
		w, h = self.screen.get_size()
		username_box = InputBox(w // 2, h // 2 - 100, LOGIN_BOX_WIDTH, LOGIN_BOX_HEIGHT, self.login_body_font, placeholder="Username")
		password_box = InputBox(w // 2, h // 2 - 100 + LOGIN_FIELD_SPACING, LOGIN_BOX_WIDTH, LOGIN_BOX_HEIGHT, self.login_body_font, placeholder="Password", is_password=True)
		button_y = h // 2 - 100 + LOGIN_FIELD_SPACING * 2 + 20
		login_button = TextButton("Login", w // 2 - 130, button_y, LOGIN_BUTTON_WIDTH, LOGIN_BUTTON_HEIGHT, self.login_body_font)
		register_button = TextButton("Register", w // 2 + 130, button_y, LOGIN_BUTTON_WIDTH, LOGIN_BUTTON_HEIGHT, self.login_body_font)
		guest_button = TextButton("Continue as Guest", w // 2, button_y + LOGIN_BUTTON_SPACING, LOGIN_BUTTON_WIDTH + 60, LOGIN_BUTTON_HEIGHT, self.login_body_font)
		back_button = TextButton("Back", w // 2, button_y + LOGIN_BUTTON_SPACING * 2, LOGIN_BUTTON_WIDTH, LOGIN_BUTTON_HEIGHT, self.login_body_font)

		message = ""
		message_colour = "white"

		while self.state == "login" and self.running:
			mouse_pos = pygame.mouse.get_pos()

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = False
					self.state = None
				username_box.handle_event(event)
				password_box.handle_event(event)
				if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
					self.state = "menu"
				elif login_button.clicked(event):
					if username_box.text.strip() == ADMIN_USERNAME and password_box.text == ADMIN_PASSWORD:
						self.current_user = ADMIN_USERNAME
						self.state = "admin"
					else:
						ok, msg = self.db.verify_user(username_box.text, password_box.text)
						message, message_colour = msg, ("#63A375" if ok else "#E85C5C")
						if ok:
							self.current_user = username_box.text.strip()
							self.state = "playing"
				elif register_button.clicked(event):
					if username_box.text.strip() == ADMIN_USERNAME:
						message, message_colour = "That username is reserved", "#E85C5C"
					else:
						ok, msg = self.db.register_user(username_box.text, password_box.text)
						message, message_colour = msg, ("#63A375" if ok else "#E85C5C")
						if ok:
							self.current_user = username_box.text.strip()
							self.state = "playing"
				elif guest_button.clicked(event):
					self.current_user = None
					self.state = "playing"
				elif back_button.clicked(event):
					self.state = "menu"

			login_button.update(mouse_pos)
			register_button.update(mouse_pos)
			guest_button.update(mouse_pos)
			back_button.update(mouse_pos)

			self.screen.fill("#1E1E2A")
			title_surf = self.login_title_font.render("Sign In", True, "white")
			self.screen.blit(title_surf, title_surf.get_rect(midtop=(w // 2, 60)))

			username_box.draw(self.screen)
			password_box.draw(self.screen)
			login_button.draw(self.screen)
			register_button.draw(self.screen)
			guest_button.draw(self.screen)
			back_button.draw(self.screen)

			if message:
				msg_surf = self.login_body_font.render(message, True, message_colour)
				self.screen.blit(msg_surf, msg_surf.get_rect(midtop=(w // 2, back_button.rect.bottom + 20)))

			pygame.display.update()
			self.clock.tick(60)

	def leaderboard_menu(self):
		w, h = self.screen.get_size()
		sort_index = 0
		back_button = TextButton("Back", w // 2, h - 60, LOGIN_BUTTON_WIDTH, LOGIN_BUTTON_HEIGHT, self.leaderboard_header_font)

		while self.state == "leaderboard" and self.running:
			mouse_pos = pygame.mouse.get_pos()

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = False
					self.state = None
				if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
					self.state = "menu"
				elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
					sort_index = (sort_index + 1) % len(LEADERBOARD_SORT_OPTIONS)
				elif back_button.clicked(event):
					self.state = "menu"

			back_button.update(mouse_pos)

			order_by, label = LEADERBOARD_SORT_OPTIONS[sort_index]
			rows = self.db.top_scores(order_by=order_by, limit=LEADERBOARD_MAX_ROWS)

			self.screen.fill("#1E1E2A")
			title_surf = self.leaderboard_title_font.render("Leaderboard", True, "white")
			self.screen.blit(title_surf, title_surf.get_rect(midtop=(w // 2, 40)))
			sub_surf = self.leaderboard_header_font.render(f"Sorted by {label}  (TAB to change)", True, "#AAAAAA")
			self.screen.blit(sub_surf, sub_surf.get_rect(midtop=(w // 2, 40 + title_surf.get_height() + 10)))

			header_y = LEADERBOARD_TOP_MARGIN + title_surf.get_height()
			headers = ["#", "Player", "Rounds", "Kills", "Time Alive"]
			col_x = (w - sum(LEADERBOARD_COLUMN_WIDTHS)) // 2
			x = col_x
			for header, width in zip(headers, LEADERBOARD_COLUMN_WIDTHS):
				h_surf = self.leaderboard_header_font.render(header, True, "#63A375")
				self.screen.blit(h_surf, (x, header_y))
				x += width

			row_y = header_y + LEADERBOARD_ROW_SPACING
			if rows:
				for i, (username, time_alive, rounds_passed, kills, date_played) in enumerate(rows, start=1):
					values = [str(i), username, str(rounds_passed), str(kills), f"{time_alive:.1f}s"]
					x = col_x
					for value, width in zip(values, LEADERBOARD_COLUMN_WIDTHS):
						v_surf = self.leaderboard_row_font.render(value, True, "white")
						self.screen.blit(v_surf, (x, row_y))
						x += width
					row_y += LEADERBOARD_ROW_SPACING
			else:
				empty_surf = self.leaderboard_row_font.render("No scores yet - be the first!", True, "white")
				self.screen.blit(empty_surf, empty_surf.get_rect(midtop=(w // 2, row_y)))

			back_button.draw(self.screen)
			pygame.display.update()
			self.clock.tick(60)

	def admin_menu(self):
		w, h = self.screen.get_size()
		col_x = (w - sum(ADMIN_COLUMN_WIDTHS)) // 2
		header_y = ADMIN_TOP_MARGIN
		back_button = TextButton("Back", 110, h - 50, 160, 44, self.admin_header_font)
		clear_button = TextButton("Clear All Scores", w - 170, h - 50, 260, 44, self.admin_header_font, base_colour="#7A2E2E", hover_colour="#B23B3B")
		confirm_clear = False

		def build_row_buttons(rows):
			buttons = []
			row_y = header_y + ADMIN_ROW_SPACING
			delete_x = col_x + sum(ADMIN_COLUMN_WIDTHS) + 20 + ADMIN_DELETE_BUTTON_SIZE // 2
			for row in rows:
				delete_button = TextButton("X", delete_x, row_y + ADMIN_ROW_SPACING // 2, ADMIN_DELETE_BUTTON_SIZE, ADMIN_DELETE_BUTTON_SIZE, self.admin_row_font, base_colour="#7A2E2E", hover_colour="#B23B3B")
				buttons.append((row, delete_button))
				row_y += ADMIN_ROW_SPACING
			return buttons

		row_buttons = build_row_buttons(self.db.all_scores(limit=ADMIN_MAX_ROWS))

		while self.state == "admin" and self.running:
			mouse_pos = pygame.mouse.get_pos()

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = False
					self.state = None
				if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
					self.state = "menu"
				elif back_button.clicked(event):
					self.state = "menu"
				elif clear_button.clicked(event):
					if confirm_clear:
						self.db.clear_scores()
						confirm_clear = False
						row_buttons = build_row_buttons(self.db.all_scores(limit=ADMIN_MAX_ROWS))
					else:
						confirm_clear = True
				else:
					for row, delete_button in row_buttons:
						if delete_button.clicked(event):
							self.db.delete_score(row[0])
							confirm_clear = False
							row_buttons = build_row_buttons(self.db.all_scores(limit=ADMIN_MAX_ROWS))
							break

			back_button.update(mouse_pos)
			clear_button.update(mouse_pos)
			for _, delete_button in row_buttons:
				delete_button.update(mouse_pos)

			self.screen.fill("#1E1E2A")
			title_surf = self.admin_title_font.render("Admin - Leaderboard Management", True, "white")
			self.screen.blit(title_surf, title_surf.get_rect(midtop=(w // 2, 30)))

			headers = ["ID", "Player", "Rounds", "Kills", "Time", "Date Played"]
			x = col_x
			for header, width in zip(headers, ADMIN_COLUMN_WIDTHS):
				h_surf = self.admin_header_font.render(header, True, "#63A375")
				self.screen.blit(h_surf, (x, header_y))
				x += width

			row_y = header_y + ADMIN_ROW_SPACING
			if row_buttons:
				for (score_id, username, time_alive, rounds_passed, kills, date_played), delete_button in row_buttons:
					values = [str(score_id), username, str(rounds_passed), str(kills), f"{time_alive:.1f}s", date_played]
					x = col_x
					for value, width in zip(values, ADMIN_COLUMN_WIDTHS):
						v_surf = self.admin_row_font.render(value, True, "white")
						self.screen.blit(v_surf, (x, row_y))
						x += width
					delete_button.draw(self.screen)
					row_y += ADMIN_ROW_SPACING
			else:
				empty_surf = self.admin_row_font.render("No scores in the database", True, "white")
				self.screen.blit(empty_surf, empty_surf.get_rect(midtop=(w // 2, row_y)))

			if confirm_clear:
				warn_surf = self.admin_header_font.render("Click Clear All Scores again to confirm", True, "#E8D44D")
				self.screen.blit(warn_surf, warn_surf.get_rect(midbottom=(w // 2, h - 100)))

			back_button.draw(self.screen)
			clear_button.draw(self.screen)
			pygame.display.update()
			self.clock.tick(60)

	def draw_game_over_screen(self):
		self.screen.fill("black")
		w, h = self.screen.get_size()

		title_surf = self.game_over_title_font.render("Game Over", True, "white")
		self.screen.blit(title_surf, title_surf.get_rect(midtop=(w // 2, GAME_OVER_TOP_MARGIN)))

		round_surf = self.game_over_body_font.render(f"You reached round {self.round_number}", True, "white")
		self.screen.blit(round_surf, round_surf.get_rect(midtop=(w // 2, GAME_OVER_TOP_MARGIN + title_surf.get_height() + GAME_OVER_LINE_SPACING)))

		stats_surf = self.game_over_body_font.render(
			f"Kills: {self.last_run_stats['kills']}   Time alive: {self.last_run_stats['time_alive']:.1f}s", True, "white")
		stats_y = GAME_OVER_TOP_MARGIN + title_surf.get_height() + GAME_OVER_LINE_SPACING + round_surf.get_height()
		self.screen.blit(stats_surf, stats_surf.get_rect(midtop=(w // 2, stats_y)))

		if self.current_user:
			saved_surf = self.game_over_body_font.render(f"Score saved for {self.current_user}", True, "#63A375")
		else:
			saved_surf = self.game_over_body_font.render("Playing as guest - sign in next time to save your score", True, "#E8D44D")
		saved_y = stats_y + stats_surf.get_height() + GAME_OVER_LINE_SPACING // 2
		self.screen.blit(saved_surf, saved_surf.get_rect(midtop=(w // 2, saved_y)))

		list_top = saved_y + saved_surf.get_height() + GAME_OVER_LINE_SPACING
		if self.player.chosen_upgrades:
			heading_surf = self.game_over_body_font.render("Upgrades collected:", True, "white")
			self.screen.blit(heading_surf, heading_surf.get_rect(midtop=(w // 2, list_top)))
			for i, name in enumerate(self.player.chosen_upgrades):
				line_surf = self.game_over_body_font.render(name, True, "#63A375")
				line_y = list_top + heading_surf.get_height() + GAME_OVER_LINE_SPACING + i * GAME_OVER_LINE_SPACING
				self.screen.blit(line_surf, line_surf.get_rect(midtop=(w // 2, line_y)))
		else:
			none_surf = self.game_over_body_font.render("No upgrades collected", True, "white")
			self.screen.blit(none_surf, none_surf.get_rect(midtop=(w // 2, list_top)))

		prompt_surf = self.game_over_body_font.render("Press SPACE for menu, L for leaderboard", True, "white")
		self.screen.blit(prompt_surf, prompt_surf.get_rect(midbottom=(w // 2, h - GAME_OVER_TOP_MARGIN // 2)))

	def game_over(self):
		while self.state == "gameover" and self.running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = False
					self.state = None
				if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
					self.state = "menu"
				elif event.type == pygame.KEYDOWN and event.key == pygame.K_l:
					self.state = "leaderboard"

			self.draw_game_over_screen()
			pygame.display.update()
			self.clock.tick(60)

	def run(self):
		while self.running:
			if self.state == "menu":
				self.menu()
			elif self.state == "settings":
				self.settings_menu()
			elif self.state == "login":
				self.login_menu()
			elif self.state == "leaderboard":
				self.leaderboard_menu()
			elif self.state == "admin":
				self.admin_menu()
			elif self.state == "gameover":
				self.game_over()
			elif self.state == "playing":
				self.new()
				self.main()

g = Game()
g.run()

pygame.quit()
sys.exit()
