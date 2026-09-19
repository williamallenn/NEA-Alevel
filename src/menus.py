import pygame
from ui import Button, TextButton, InputBox, play_music, set_sfx_volume
from settings import (
	HUD_PADDING, UPGRADE_BODY_FONT_SIZE, WEAPON_DATA, WEAPON_ICON_SIZE,
	LOGIN_TITLE_FONT_SIZE, LOGIN_BODY_FONT_SIZE, LOGIN_BOX_WIDTH, LOGIN_BOX_HEIGHT, LOGIN_FIELD_SPACING,
	ADMIN_USERNAME, ADMIN_PASSWORD,
	SETTINGS_TOP_MARGIN, SETTINGS_ROW_SPACING, SETTINGS_SLIDER_WIDTH, SETTINGS_SLIDER_HEIGHT, SETTINGS_SLIDER_HANDLE_SIZE,
	LEADERBOARD_TITLE_FONT_SIZE, LEADERBOARD_HEADER_FONT_SIZE, LEADERBOARD_ROW_FONT_SIZE, LEADERBOARD_TOP_MARGIN,
	LEADERBOARD_ROW_SPACING, LEADERBOARD_COLUMN_WIDTHS, LEADERBOARD_MAX_ROWS, LEADERBOARD_SORT_OPTIONS,
	SHOP_TOP_MARGIN, SHOP_ROW_SPACING, MENU_MUSIC_PATH,
	ADMIN_TITLE_FONT_SIZE, ADMIN_HEADER_FONT_SIZE, ADMIN_ROW_FONT_SIZE, ADMIN_TOP_MARGIN, ADMIN_ROW_SPACING,
	ADMIN_MAX_ROWS, ADMIN_COLUMN_WIDTHS, ADMIN_DELETE_BUTTON_SIZE,
	GAME_OVER_TITLE_FONT_SIZE, GAME_OVER_BODY_FONT_SIZE, GAME_OVER_LINE_SPACING, GAME_OVER_TOP_MARGIN,
)


def load_font(size):
	return pygame.font.SysFont("SimSun", size)


class Menu:
	"""Base for every menu screen: runs the shared event/draw loop until something changes the game state."""
	STATE = None
	BACKGROUND = "#1E1E2A" ###############  ADD DRAWN BACKGROUND HERE ######################################

	def __init__(self, game):
		self.game = game
		self.screen = game.screen
		self.w, self.h = game.screen.get_size()
		self.back_button = None

	# opens the menu and keeps handling input and redrawing until the game state changes
	def run(self):
		self.setup()
		while self.game.state == self.STATE and self.game.running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.game.running = False
					self.game.state = None
				else:
					self.handle_event(event)

			mouse_pos = pygame.mouse.get_pos()
			self.screen.fill(self.BACKGROUND)
			self.draw(mouse_pos)
			if self.back_button:
				self.back_button.update(mouse_pos)
				self.back_button.draw(self.screen)
			pygame.display.update()
			self.game.clock.tick(60)

	# resets the menu's buttons and state each time it's opened - overridden by menus that need it
	def setup(self):
		pass

	# ESC or the back button returns to the main menu - subclasses add their own buttons and keys
	def handle_event(self, event):
		if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
			self.game.state = "menu"
		elif self.back_button and self.back_button.clicked(event):
			self.game.state = "menu"

	# draws the menu's contents (the background and back button are drawn by run)
	def draw(self, mouse_pos):
		pass


class MainMenu(Menu):
	"""The start screen: play, settings and exit, plus links to the account, leaderboard, stats and shop screens."""
	STATE = "menu"
	BACKGROUND = "#73D8E7"

	def __init__(self, game):
		super().__init__(game)
		w, h = self.w, self.h
		self.play_button = Button("images/buttons/play.png", w // 2, h // 2 + 20, scale=2.5)
		self.settings_button = Button("images/buttons/settings.png", w // 2, h // 2 + 160, scale=2.5)
		self.exit_button = Button("images/buttons/exit.png", w // 2, h // 2 + 300, scale=2.5)
		self.leaderboard_link_button = Button("images/buttons/leaderboard.png", w - 170, 60, scale=1.5)
		self.stats_link_button = Button("images/buttons/stats.png", w - 170, 160, scale=1.5)
		self.shop_link_button = Button("images/buttons/shop.png", w - 170, 270, scale=1.5)
		self.account_link_button = Button("images/buttons/account.png", 116, 68, scale=1.5)
		self.body_font = load_font(UPGRADE_BODY_FONT_SIZE)

	# starts the looping menu music whenever the start screen is opened
	def setup(self):
		play_music(MENU_MUSIC_PATH)

	# each button switches to its screen; stats and shop only work when signed in, and ESC does nothing here
	def handle_event(self, event):
		if self.play_button.clicked(event):
			self.game.state = "playing"
		elif self.settings_button.clicked(event):
			self.game.state = "settings"
		elif self.exit_button.clicked(event):
			self.game.running = False
			self.game.state = None
		elif self.leaderboard_link_button.clicked(event):
			self.game.state = "leaderboard"
		elif self.account_link_button.clicked(event):
			self.game.state = "login"
		elif self.game.current_user and self.stats_link_button.clicked(event):
			self.game.state = "stats"
		elif self.game.current_user and self.shop_link_button.clicked(event):
			self.game.state = "shop"

	def draw(self, mouse_pos):
		buttons = [self.play_button, self.settings_button, self.exit_button, self.leaderboard_link_button, self.account_link_button]
		if self.game.current_user:
			buttons += [self.stats_link_button, self.shop_link_button]
		for button in buttons:
			button.update(mouse_pos)
			button.draw(self.screen)
		if self.game.current_user:
			user_surf = self.body_font.render(f"Signed in as {self.game.current_user}", True, "black")
			self.screen.blit(user_surf, (HUD_PADDING, self.account_link_button.rect.bottom + 10))


class SettingsMenu(Menu):
	"""Keybind rebinding and the music/SFX volume sliders - also opened from the pause menu."""
	STATE = "settings"
	ROWS = [("up", "Move Up"), ("down", "Move Down"), ("left", "Move Left"), ("right", "Move Right")]
	SLIDERS = [("volume", "Music"), ("sfx_volume", "SFX")]

	def __init__(self, game):
		super().__init__(game)
		self.title_font = load_font(LOGIN_TITLE_FONT_SIZE)
		self.body_font = load_font(LOGIN_BODY_FONT_SIZE)
		self.label_x = self.w // 2 - 180
		self.control_x = self.w // 2 + 60
		# one slider row per entry in SLIDERS, stacked below the keybind rows
		self.slider_rects = {}
		for i, (key, label) in enumerate(self.SLIDERS):
			row_y = SETTINGS_TOP_MARGIN + (len(self.ROWS) + i) * SETTINGS_ROW_SPACING
			self.slider_rects[key] = pygame.Rect(self.control_x - 60, row_y - SETTINGS_SLIDER_HEIGHT // 2, SETTINGS_SLIDER_WIDTH, SETTINGS_SLIDER_HEIGHT)
		self.last_row_y = SETTINGS_TOP_MARGIN + (len(self.ROWS) + len(self.SLIDERS) - 1) * SETTINGS_ROW_SPACING

	# rebuilds the keybind buttons from the current keybinds each time settings is opened
	def setup(self):
		self.keybind_buttons = {
			action: TextButton(pygame.key.name(self.game.keybinds[action]).upper(), self.control_x, SETTINGS_TOP_MARGIN + i * SETTINGS_ROW_SPACING, 120, 40, self.body_font)
			for i, (action, label) in enumerate(self.ROWS)
		}
		self.back_button = Button("images/buttons/back.png", self.w // 2, self.last_row_y + SETTINGS_ROW_SPACING, scale=1.5)
		self.rebinding = None
		self.dragging_slider = None

	# sets one slider's volume from how far along it the mouse is, clamped between 0 and 1
	def set_volume_from_mouse(self, key, mouse_x):
		slider_rect = self.slider_rects[key]
		ratio = (mouse_x - slider_rect.x) / slider_rect.width
		volume = max(0.0, min(1.0, ratio))
		setattr(self.game, key, volume)
		if key == "volume":
			pygame.mixer.music.set_volume(volume)
		else:
			set_sfx_volume(volume)

	# the slider under the given position, or None if the click missed them all
	def slider_at(self, pos):
		for key, slider_rect in self.slider_rects.items():
			if slider_rect.inflate(0, 20).collidepoint(pos):
				return key
		return None

	# while rebinding, the next key press becomes the keybind (ESC cancels); otherwise handles the slider and buttons
	def handle_event(self, event):
		if self.rebinding is not None and event.type == pygame.KEYDOWN:
			if event.key != pygame.K_ESCAPE:
				self.game.keybinds[self.rebinding] = event.key
				self.keybind_buttons[self.rebinding].text = pygame.key.name(event.key).upper()
			self.rebinding = None
		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.slider_at(event.pos):
			self.dragging_slider = self.slider_at(event.pos)
			self.set_volume_from_mouse(self.dragging_slider, event.pos[0])
		elif event.type == pygame.MOUSEBUTTONUP:
			self.dragging_slider = None
		elif event.type == pygame.MOUSEMOTION and self.dragging_slider:
			self.set_volume_from_mouse(self.dragging_slider, event.pos[0])
		else:
			super().handle_event(event)
			for action, button in self.keybind_buttons.items():
				if button.clicked(event):
					self.rebinding = action
					button.text = "Press a key"

	def draw(self, mouse_pos):
		title_surf = self.title_font.render("Settings", True, "white")
		self.screen.blit(title_surf, title_surf.get_rect(midtop=(self.w // 2, 60)))

		for i, (action, label) in enumerate(self.ROWS):
			row_y = SETTINGS_TOP_MARGIN + i * SETTINGS_ROW_SPACING
			label_surf = self.body_font.render(label, True, "white")
			self.screen.blit(label_surf, label_surf.get_rect(midleft=(self.label_x, row_y)))
			self.keybind_buttons[action].update(mouse_pos)
			self.keybind_buttons[action].draw(self.screen)

		for key, label in self.SLIDERS:
			self.draw_volume_slider(key, label)

	# draws one slider's label, the filled bar, its handle and the percentage
	def draw_volume_slider(self, key, label):
		volume = getattr(self.game, key)
		slider_rect = self.slider_rects[key]
		volume_label_surf = self.body_font.render(label, True, "white")
		self.screen.blit(volume_label_surf, volume_label_surf.get_rect(midleft=(self.label_x, slider_rect.centery)))
		pygame.draw.rect(self.screen, "#2B2B3A", slider_rect, border_radius=4)
		fill_rect = pygame.Rect(slider_rect.x, slider_rect.y, int(slider_rect.width * volume), slider_rect.height)
		pygame.draw.rect(self.screen, "#63A375", fill_rect, border_radius=4)
		pygame.draw.rect(self.screen, "white", slider_rect, width=2, border_radius=4)
		handle_x = slider_rect.x + int(slider_rect.width * volume)
		handle_rect = pygame.Rect(0, 0, SETTINGS_SLIDER_HANDLE_SIZE, SETTINGS_SLIDER_HANDLE_SIZE)
		handle_rect.center = (handle_x, slider_rect.centery)
		pygame.draw.rect(self.screen, "white", handle_rect, border_radius=3)
		percent_surf = self.body_font.render(f"{int(volume * 100)}%", True, "white")
		self.screen.blit(percent_surf, percent_surf.get_rect(midleft=(slider_rect.right + 16, slider_rect.centery)))


class LoginMenu(Menu):
	"""Sign in, register or continue as a guest (the admin login is checked before the database)."""
	STATE = "login"
	BACKGROUND = "#73D8E7"

	def __init__(self, game):
		super().__init__(game)
		self.title_font = load_font(LOGIN_TITLE_FONT_SIZE)
		self.body_font = load_font(LOGIN_BODY_FONT_SIZE)

	# builds empty input boxes and the buttons each time the screen is opened
	def setup(self):
		w, h = self.w, self.h
		self.username_box = InputBox(w // 2, h // 2 - 100, LOGIN_BOX_WIDTH, LOGIN_BOX_HEIGHT, self.body_font, placeholder="Username")
		self.password_box = InputBox(w // 2, h // 2 - 100 + LOGIN_FIELD_SPACING, LOGIN_BOX_WIDTH, LOGIN_BOX_HEIGHT, self.body_font, placeholder="Password", is_password=True)
		button_y = h // 2 - 100 + LOGIN_FIELD_SPACING * 2 + 20
		self.login_button = Button("images/buttons/login.png", w // 2 - 130, button_y, scale=1.5)
		self.register_button = Button("images/buttons/register.png", w // 2 + 130, button_y, scale=1.5)
		row_gap = self.login_button.rect.height + 20
		self.guest_button = Button("images/buttons/guest.png", w // 2, button_y + row_gap, scale=1.5)
		self.back_button = Button("images/buttons/back.png", w // 2, button_y + row_gap * 2, scale=1.5)
		self.message = ""
		self.message_colour = "white"

	# passes typing to the input boxes, then handles the login/register/guest buttons
	def handle_event(self, event):
		self.username_box.handle_event(event)
		self.password_box.handle_event(event)
		super().handle_event(event)
		username = self.username_box.text.strip()
		password = self.password_box.text
		if self.login_button.clicked(event):
			if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
				self.game.current_user = None
				self.game.state = "admin"
			else:
				self.show_result(username, *self.game.db.verify_user(username, password))
		elif self.register_button.clicked(event):
			if username == ADMIN_USERNAME:
				self.message, self.message_colour = "That username is reserved", "#E85C5C"
			else:
				self.show_result(username, *self.game.db.register_user(username, password))
		elif self.guest_button.clicked(event):
			self.game.current_user = None
			self.game.state = "menu"

	# shows the login/register result in green or red, and signs the user in if it worked
	def show_result(self, username, ok, message):
		self.message, self.message_colour = message, ("#63A375" if ok else "#E85C5C")
		if ok:
			self.game.current_user = username
			self.game.state = "menu"

	def draw(self, mouse_pos):
		title_surf = self.title_font.render("Sign In", True, "black")
		self.screen.blit(title_surf, title_surf.get_rect(midtop=(self.w // 2, 60)))
		self.username_box.draw(self.screen)
		self.password_box.draw(self.screen)
		for button in (self.login_button, self.register_button, self.guest_button):
			button.update(mouse_pos)
			button.draw(self.screen)
		if self.message:
			msg_surf = self.body_font.render(self.message, True, self.message_colour)
			self.screen.blit(msg_surf, msg_surf.get_rect(midtop=(self.w // 2, self.back_button.rect.bottom + 20)))


class LeaderboardMenu(Menu):
	"""Top scores table, sorted by whichever column TAB currently selects."""
	STATE = "leaderboard"
	BACKGROUND = "#005763"

	def __init__(self, game):
		super().__init__(game)
		self.title_font = load_font(LEADERBOARD_TITLE_FONT_SIZE)
		self.header_font = load_font(LEADERBOARD_HEADER_FONT_SIZE)
		self.row_font = load_font(LEADERBOARD_ROW_FONT_SIZE)

	def setup(self):
		self.sort_index = 0
		self.back_button = Button("images/buttons/back.png", self.w // 2, self.h - 60, scale=1.5)

	# TAB cycles which column the table is sorted by
	def handle_event(self, event):
		super().handle_event(event)
		if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
			self.sort_index = (self.sort_index + 1) % len(LEADERBOARD_SORT_OPTIONS)

	def draw(self, mouse_pos):
		w = self.w
		order_by, label = LEADERBOARD_SORT_OPTIONS[self.sort_index]
		rows = self.game.db.top_scores(order_by=order_by, limit=LEADERBOARD_MAX_ROWS)

		title_surf = self.title_font.render("Leaderboard", True, "white")
		self.screen.blit(title_surf, title_surf.get_rect(midtop=(w // 2, 40)))
		sub_surf = self.header_font.render(f"Sorted by {label}  (TAB to change)", True, "#AAAAAA")
		self.screen.blit(sub_surf, sub_surf.get_rect(midtop=(w // 2, 40 + title_surf.get_height() + 10)))

		header_y = LEADERBOARD_TOP_MARGIN + title_surf.get_height()
		headers = ["#", "Player", "Rounds", "Kills", "Time Alive"]
		col_x = (w - sum(LEADERBOARD_COLUMN_WIDTHS)) // 2
		x = col_x
		for header, width in zip(headers, LEADERBOARD_COLUMN_WIDTHS):
			h_surf = self.header_font.render(header, True, "#63A375")
			self.screen.blit(h_surf, (x, header_y))
			x += width

		row_y = header_y + LEADERBOARD_ROW_SPACING
		if rows:
			for i, (username, time_alive, rounds_passed, kills, date_played) in enumerate(rows, start=1):
				values = [str(i), username, str(rounds_passed), str(kills), f"{time_alive:.1f}s"]
				x = col_x
				for value, width in zip(values, LEADERBOARD_COLUMN_WIDTHS):
					v_surf = self.row_font.render(value, True, "white")
					self.screen.blit(v_surf, (x, row_y))
					x += width
				row_y += LEADERBOARD_ROW_SPACING
		else:
			empty_surf = self.row_font.render("No scores yet - be the first!", True, "white")
			self.screen.blit(empty_surf, empty_surf.get_rect(midtop=(w // 2, row_y)))


class StatsMenu(Menu):
	"""Per-user stats screen, filled from one aggregate SQL query (Database.user_stats)."""
	STATE = "stats"

	def __init__(self, game):
		super().__init__(game)
		self.title_font = load_font(LEADERBOARD_TITLE_FONT_SIZE)
		self.header_font = load_font(LEADERBOARD_HEADER_FONT_SIZE)
		self.row_font = load_font(LEADERBOARD_ROW_FONT_SIZE)

	def setup(self):
		self.back_button = Button("images/buttons/back.png", self.w // 2, self.h - 60, scale=1.5)

	def draw(self, mouse_pos):
		w = self.w
		stats = self.game.db.user_stats(self.game.current_user)

		title_surf = self.title_font.render("My Stats", True, "white")
		self.screen.blit(title_surf, title_surf.get_rect(midtop=(w // 2, 40)))
		sub_surf = self.header_font.render(self.game.current_user, True, "#AAAAAA")
		self.screen.blit(sub_surf, sub_surf.get_rect(midtop=(w // 2, 40 + title_surf.get_height() + 10)))

		rows = [
			("Games Played", str(stats["games_played"])),
			("Total Kills", str(stats["total_kills"])),
			("Best Round", str(stats["best_round"])),
			("Average Time Alive", f"{stats['avg_time_alive']:.1f}s"),
		]
		row_y = LEADERBOARD_TOP_MARGIN + title_surf.get_height()
		for label, value in rows:
			label_surf = self.row_font.render(label, True, "#63A375")
			self.screen.blit(label_surf, label_surf.get_rect(midright=(w // 2 - 20, row_y)))
			value_surf = self.row_font.render(value, True, "white")
			self.screen.blit(value_surf, value_surf.get_rect(midleft=(w // 2 + 20, row_y)))
			row_y += LEADERBOARD_ROW_SPACING


class ShopMenu(Menu):
	"""Weapon shop: buy weapons with saved money and pick which owned ones to take into a game."""
	STATE = "shop"
	BACKGROUND = "#73D8E7"

	def __init__(self, game):
		super().__init__(game)
		self.title_font = load_font(LEADERBOARD_TITLE_FONT_SIZE)
		self.header_font = load_font(LEADERBOARD_HEADER_FONT_SIZE)
		self.row_font = load_font(LEADERBOARD_ROW_FONT_SIZE)
		self.message_font = load_font(LOGIN_BODY_FONT_SIZE)

	# each weapon row has a buy, equipped and unequipped button in the same spot; only one is shown at a time
	def setup(self):
		self.back_button = Button("images/buttons/back.png", self.w // 2, self.h - 60, scale=1.5)
		self.weapon_buttons = {}
		for i, key in enumerate(WEAPON_DATA):
			row_y = SHOP_TOP_MARGIN + i * SHOP_ROW_SPACING
			self.weapon_buttons[key] = {
				"buy": Button("images/buttons/buy.png", self.w // 2 + 180, row_y, scale=1.5),
				"equipped": Button("images/buttons/equipped.png", self.w // 2 + 180, row_y, scale=1.5),
				"unequipped": Button("images/buttons/unequipped.png", self.w // 2 + 180, row_y, scale=1.5),
			}
		self.message = ""
		self.message_colour = "black"
		self.owned = self.game.get_owned_weapons()

	# picks which of a weapon's buttons to show: buy if not owned, otherwise its equipped state
	def current_button(self, key):
		if key not in self.owned:
			return self.weapon_buttons[key]["buy"]
		return self.weapon_buttons[key]["equipped" if self.owned[key] else "unequipped"]

	# buys, equips or unequips the clicked weapon (the last equipped weapon can't be unequipped)
	def handle_event(self, event):
		super().handle_event(event)
		for key in self.weapon_buttons:
			if not self.current_button(key).clicked(event):
				continue
			weapon = WEAPON_DATA[key]
			if key not in self.owned:
				if self.game.db.buy_weapon(self.game.current_user, key, weapon["price"]):
					self.message, self.message_colour = f"Bought {weapon['name']}", "#63A375"
				else:
					self.message, self.message_colour = "Not enough money", "#E85C5C"
			elif self.owned[key] and sum(self.owned.values()) == 1:
				self.message, self.message_colour = "Keep at least one weapon equipped", "#E85C5C"
			else:
				self.game.db.set_equipped(self.game.current_user, key, not self.owned[key])
				self.message = ""
			self.owned = self.game.get_owned_weapons()
			break

	def draw(self, mouse_pos):
		w = self.w
		self.owned = self.game.get_owned_weapons()
		title_surf = self.title_font.render("Weapons", True, "black")
		self.screen.blit(title_surf, title_surf.get_rect(midtop=(w // 2, 40)))
		money_surf = self.header_font.render(f"${self.game.db.get_money(self.game.current_user)}", True, "black")
		self.screen.blit(money_surf, money_surf.get_rect(midtop=(w // 2, 40 + title_surf.get_height() + 10)))

		for key in self.weapon_buttons:
			button = self.current_button(key)
			button.update(mouse_pos)
			row_y = button.rect.centery
			self.game.hud.draw_weapon_icon(key, pygame.Rect(w // 2 - 300, row_y - WEAPON_ICON_SIZE // 2, WEAPON_ICON_SIZE, WEAPON_ICON_SIZE))
			name_surf = self.row_font.render(WEAPON_DATA[key]["name"], True, "black")
			self.screen.blit(name_surf, name_surf.get_rect(midleft=(w // 2 - 210, row_y)))
			if key not in self.owned:
				price_surf = self.row_font.render(f"${WEAPON_DATA[key]['price']}", True, "black")
				self.screen.blit(price_surf, price_surf.get_rect(midright=(button.rect.left - 16, row_y)))
			button.draw(self.screen)

		if self.message:
			msg_surf = self.message_font.render(self.message, True, self.message_colour)
			self.screen.blit(msg_surf, msg_surf.get_rect(midtop=(w // 2, SHOP_TOP_MARGIN + len(WEAPON_DATA) * SHOP_ROW_SPACING - 20)))


class AdminMenu(Menu):
	"""Admin screen: delete individual scores, or clear them all (needs a second click to confirm)."""
	STATE = "admin"

	def __init__(self, game):
		super().__init__(game)
		self.title_font = load_font(ADMIN_TITLE_FONT_SIZE)
		self.header_font = load_font(ADMIN_HEADER_FONT_SIZE)
		self.row_font = load_font(ADMIN_ROW_FONT_SIZE)
		self.col_x = (self.w - sum(ADMIN_COLUMN_WIDTHS)) // 2

	def setup(self):
		self.back_button = Button("images/buttons/back.png", 110, self.h - 50, scale=1.5)
		self.clear_button = TextButton("Clear All Scores", self.w - 170, self.h - 50, 260, 44, self.header_font, base_colour="#7A2E2E", hover_colour="#B23B3B")
		self.confirm_clear = False
		self.build_row_buttons()

	# reloads the scores and builds a (row, delete_button) pair for each one, positioned top to bottom
	def build_row_buttons(self):
		self.row_buttons = []
		row_y = ADMIN_TOP_MARGIN + ADMIN_ROW_SPACING
		delete_x = self.col_x + sum(ADMIN_COLUMN_WIDTHS) + 20 + ADMIN_DELETE_BUTTON_SIZE // 2
		for row in self.game.db.all_scores(limit=ADMIN_MAX_ROWS):
			delete_button = TextButton("X", delete_x, row_y + ADMIN_ROW_SPACING // 2, ADMIN_DELETE_BUTTON_SIZE, ADMIN_DELETE_BUTTON_SIZE, self.row_font, base_colour="#7A2E2E", hover_colour="#B23B3B")
			self.row_buttons.append((row, delete_button))
			row_y += ADMIN_ROW_SPACING

	# clear all needs two clicks in a row; a delete button removes just its own score
	def handle_event(self, event):
		super().handle_event(event)
		if self.clear_button.clicked(event):
			if self.confirm_clear:
				self.game.db.clear_scores()
				self.confirm_clear = False
				self.build_row_buttons()
			else:
				self.confirm_clear = True
		else:
			for row, delete_button in self.row_buttons:
				if delete_button.clicked(event):
					self.game.db.delete_score(row[0])
					self.confirm_clear = False
					self.build_row_buttons()
					break

	def draw(self, mouse_pos):
		w, h = self.w, self.h
		title_surf = self.title_font.render("Admin - Leaderboard Management", True, "white")
		self.screen.blit(title_surf, title_surf.get_rect(midtop=(w // 2, 30)))

		headers = ["ID", "Player", "Rounds", "Kills", "Time", "Date Played"]
		x = self.col_x
		for header, width in zip(headers, ADMIN_COLUMN_WIDTHS):
			h_surf = self.header_font.render(header, True, "#63A375")
			self.screen.blit(h_surf, (x, ADMIN_TOP_MARGIN))
			x += width

		row_y = ADMIN_TOP_MARGIN + ADMIN_ROW_SPACING
		if self.row_buttons:
			for (score_id, username, time_alive, rounds_passed, kills, date_played), delete_button in self.row_buttons:
				values = [str(score_id), username, str(rounds_passed), str(kills), f"{time_alive:.1f}s", date_played]
				x = self.col_x
				for value, width in zip(values, ADMIN_COLUMN_WIDTHS):
					v_surf = self.row_font.render(value, True, "white")
					self.screen.blit(v_surf, (x, row_y))
					x += width
				delete_button.update(mouse_pos)
				delete_button.draw(self.screen)
				row_y += ADMIN_ROW_SPACING
		else:
			empty_surf = self.row_font.render("No scores in the database", True, "white")
			self.screen.blit(empty_surf, empty_surf.get_rect(midtop=(w // 2, row_y)))

		if self.confirm_clear:
			warn_surf = self.header_font.render("Click Clear All Scores again to confirm", True, "#E8D44D")
			self.screen.blit(warn_surf, warn_surf.get_rect(midbottom=(w // 2, h - 100)))

		self.clear_button.update(mouse_pos)
		self.clear_button.draw(self.screen)


class GameOverScreen(Menu):
	"""Shown when the player dies: the run's stats, whether it was saved, and the upgrades collected."""
	STATE = "gameover"
	BACKGROUND = "black"

	def __init__(self, game):
		super().__init__(game)
		self.title_font = load_font(GAME_OVER_TITLE_FONT_SIZE)
		self.body_font = load_font(GAME_OVER_BODY_FONT_SIZE)

	# SPACE returns to the menu and L opens the leaderboard (ESC does nothing here)
	def handle_event(self, event):
		if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
			self.game.state = "menu"
		elif event.type == pygame.KEYDOWN and event.key == pygame.K_l:
			self.game.state = "leaderboard"

	def draw(self, mouse_pos):
		w, h = self.w, self.h
		stats = self.game.last_run_stats

		title_surf = self.title_font.render("Game Over", True, "white")
		self.screen.blit(title_surf, title_surf.get_rect(midtop=(w // 2, GAME_OVER_TOP_MARGIN)))

		round_surf = self.body_font.render(f"You reached round {stats['rounds_passed']}", True, "white")
		self.screen.blit(round_surf, round_surf.get_rect(midtop=(w // 2, GAME_OVER_TOP_MARGIN + title_surf.get_height() + GAME_OVER_LINE_SPACING)))

		stats_surf = self.body_font.render(f"Kills: {stats['kills']}   Time alive: {stats['time_alive']:.1f}s", True, "white")
		stats_y = GAME_OVER_TOP_MARGIN + title_surf.get_height() + GAME_OVER_LINE_SPACING + round_surf.get_height()
		self.screen.blit(stats_surf, stats_surf.get_rect(midtop=(w // 2, stats_y)))

		if self.game.current_user:
			saved_surf = self.body_font.render(f"Score and ${stats['money']} saved for {self.game.current_user}", True, "#63A375")
		else:
			saved_surf = self.body_font.render("Playing as guest - sign in next time to save your score", True, "#E8D44D")
		saved_y = stats_y + stats_surf.get_height() + GAME_OVER_LINE_SPACING // 2
		self.screen.blit(saved_surf, saved_surf.get_rect(midtop=(w // 2, saved_y)))

		list_top = saved_y + saved_surf.get_height() + GAME_OVER_LINE_SPACING
		if stats["upgrades"]:
			heading_surf = self.body_font.render("Upgrades collected:", True, "white")
			self.screen.blit(heading_surf, heading_surf.get_rect(midtop=(w // 2, list_top)))
			for i, name in enumerate(stats["upgrades"]):
				line_surf = self.body_font.render(name, True, "#63A375")
				line_y = list_top + heading_surf.get_height() + GAME_OVER_LINE_SPACING + i * GAME_OVER_LINE_SPACING
				self.screen.blit(line_surf, line_surf.get_rect(midtop=(w // 2, line_y)))
		else:
			none_surf = self.body_font.render("No upgrades collected", True, "white")
			self.screen.blit(none_surf, none_surf.get_rect(midtop=(w // 2, list_top)))

		prompt_surf = self.body_font.render("Press SPACE for menu, L for leaderboard", True, "white")
		self.screen.blit(prompt_surf, prompt_surf.get_rect(midbottom=(w // 2, h - GAME_OVER_TOP_MARGIN // 2)))
