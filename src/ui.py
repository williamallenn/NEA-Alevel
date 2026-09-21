import pygame
from settings import BUTTON_PRESS_SOUND_PATH

_sounds = {}
_current_music = None
_sfx_volume = 1.0


# plays a one-off sound effect loading it the first time and reusing it after.
# no_overlap skips the play if that sound is still going, so a long sound fired on a
# short cooldown (the flamethrower) doesn't stack copies of itself into a roar.
def play_sound(path, no_overlap=False):
	if path not in _sounds:
		_sounds[path] = pygame.mixer.Sound(path)
	sound = _sounds[path]
	if no_overlap and sound.get_num_channels() > 0:
		return
	sound.set_volume(_sfx_volume)
	sound.play()


# sets how loud sound effects play.
def set_sfx_volume(value):
	global _sfx_volume
	_sfx_volume = value


# loops a music track, or stops the music when path is None.
def play_music(path):
	global _current_music
	if path == _current_music:
		return
	_current_music = path
	if path is None:
		pygame.mixer.music.stop()
	else:
		pygame.mixer.music.load(path)
		pygame.mixer.music.play(-1)


class Button:
	"""A clickable image-based button with a slightly enlarged hover state."""
	def __init__(self, image_path, x, y, scale=1.0):
		image = pygame.image.load(image_path).convert_alpha()
		width = int(image.get_width() * scale)
		height = int(image.get_height() * scale)
		self.image = pygame.transform.scale(image, (width, height))
		self.hover_image = pygame.transform.scale(self.image, (int(width * 1.08), int(height * 1.08)))
		self.rect = self.image.get_rect(center=(x, y))
		self.hovered = False

	# grows the button slightly while the mouse is over it
	def update(self, mouse_pos):
		self.hovered = self.rect.collidepoint(mouse_pos)

	# draws the hover-sized image when hovered, otherwise the normal image
	def draw(self, surface):
		if self.hovered:
			img = self.hover_image
			rect = img.get_rect(center=self.rect.center)
		else:
			img = self.image
			rect = self.rect
		surface.blit(img, rect)

	# true when left-clicked, and plays the button press sound as it reports the hit
	def clicked(self, event):
		hit = (
			event.type == pygame.MOUSEBUTTONDOWN
			and event.button == 1
			and self.rect.collidepoint(event.pos)
		)
		if hit:
			play_sound(BUTTON_PRESS_SOUND_PATH)
		return hit


class TextButton:
	"""A clickable rectangular button drawn from text rather than an image."""
	def __init__(self, text, x, y, width, height, font, base_colour="#2B2B3A", hover_colour="#63A375"):
		self.text = text
		self.rect = pygame.Rect(0, 0, width, height)
		self.rect.center = (x, y)
		self.font = font
		self.base_colour = base_colour
		self.hover_colour = hover_colour
		self.hovered = False

	# grows the button slightly while the mouse is over it
	def update(self, mouse_pos):
		self.hovered = self.rect.collidepoint(mouse_pos)

	# draws the button box in the hover/base colour with its centred label text
	def draw(self, surface):
		colour = self.hover_colour if self.hovered else self.base_colour
		pygame.draw.rect(surface, colour, self.rect, border_radius=8)
		pygame.draw.rect(surface, "white", self.rect, width=2, border_radius=8)
		text_surf = self.font.render(self.text, True, "white")
		surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

	# true when left-clicked, and plays the button press sound as it reports the hit
	def clicked(self, event):
		hit = (
			event.type == pygame.MOUSEBUTTONDOWN
			and event.button == 1
			and self.rect.collidepoint(event.pos)
		)
		if hit:
			play_sound(BUTTON_PRESS_SOUND_PATH)
		return hit


class InputBox:
	"""A clickable text field that becomes active on click and accepts typed input (optionally masked as a password)."""
	def __init__(self, x, y, width, height, font, placeholder="", is_password=False, max_length=24):
		self.rect = pygame.Rect(0, 0, width, height)
		self.rect.center = (x, y)
		self.font = font
		self.text = ""
		self.placeholder = placeholder
		self.is_password = is_password
		self.max_length = max_length
		self.active = False

	# toggles active state on click, and appends/removes typed characters while active
	def handle_event(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			self.active = self.rect.collidepoint(event.pos)
		elif event.type == pygame.KEYDOWN and self.active:
			if event.key == pygame.K_BACKSPACE:
				self.text = self.text[:-1]
			elif event.key in (pygame.K_RETURN, pygame.K_TAB):
				pass
			elif len(self.text) < self.max_length and event.unicode.isprintable():
				self.text += event.unicode

	# draws the box and text (asterisks for passwords, placeholder when empty)
	def draw(self, surface):
		background_colour = "white" if self.active else "#D8D8D8"
		pygame.draw.rect(surface, background_colour, self.rect, border_radius=6)
		pygame.draw.rect(surface, "black", self.rect, width=2, border_radius=6)
		display_text = ("*" * len(self.text)) if self.is_password else self.text
		if display_text:
			text_surf = self.font.render(display_text, True, "black")
		else:
			text_surf = self.font.render(self.placeholder, True, "#777777")
		surface.blit(text_surf, (self.rect.x + 12, self.rect.centery - text_surf.get_height() // 2))
