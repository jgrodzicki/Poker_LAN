import pygame

class Button:

    def __init__(self, txt, location, screen, bg=(255, 50, 50), fg=(0, 0, 0), size=(80, 30)):
        self.color = bg
        self.bg = bg
        self.fg = fg
        self.screen = screen
        self.size = size
        self.font = pygame.font.Font('freesansbold.ttf', 16)
        self.txt = txt
        self.txt_surf = self.font.render(self.txt, 1, self.fg)
        self.txt_rect = self.txt_surf.get_rect(center=([s//2 for s in self.size]))
        self.surface = pygame.surface.Surface(size)
        self.rect = self.surface.get_rect(center=location)


    def to_check(self):
        self.change_txt('check')


    def to_call(self, value):
        self.change_txt(f'call {value}')


    def change_txt(self, txt):
        self.txt = txt
        self.txt_surf = self.font.render(self.txt, 1, self.fg)


    def draw(self):
        self.mouseover()

        self.surface.fill(self.bg)
        self.surface.blit(self.txt_surf, self.txt_rect)
        self.screen.blit(self.surface, self.rect)

    def mouseover(self):
        self.bg = self.color
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos):
            self.bg = (200, 0, 0)

    def is_clicked(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())
