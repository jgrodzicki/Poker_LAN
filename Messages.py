import pygame


class Messages:

    def __init__(self, location, screen, size=(275, 60)):
        self.screen = screen
        self.size = size
        self.font = pygame.font.SysFont('Arial', 12)
        self.txt = []
        self.txt_surf = []
        self.surface = pygame.surface.Surface(size)
        self.location = location
        self.rect = self.surface.get_rect(center=(self.location[0]+size[0]//2, self.location[1]+size[1]//2))

    def clear(self):
        self.txt, self.txt_surf = [], []

    def add_text(self, text):
        self.txt.append(text)
        self.txt_surf.append(self.font.render(text, True, (0, 0, 0), None))
        self.size = (250, 15*len(self.txt))
        self.surface = pygame.surface.Surface(self.size)
        self.rect = self.surface.get_rect(center=(self.location[0] + self.size[0] // 2, self.location[1] + self.size[1] // 2))

    def draw(self):
        self.surface.fill((220, 220, 220))
        for i in range(len(self.txt)):
            self.surface.blit(self.txt_surf[i], (0, 15*i))
            self.screen.blit(self.surface, self.location)
