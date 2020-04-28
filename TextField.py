import pygame


class TextField:
    def __init__(self, location, screen, size=(80, 20)):
        self.screen = screen
        self.size = size
        self.font = pygame.font.Font('freesansbold.ttf', 16)
        self.txt = ''
        self.txt_surf = self.font.render(self.txt, 1, (150, 150, 150))
        self.txt_rect = self.txt_surf.get_rect(center=([s // 2 for s in self.size]))
        self.surface = pygame.surface.Surface(size)
        self.location = location
        self.rect = self.surface.get_rect(center=self.location)
        self.is_active = False

    def is_clicked(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def click_action(self):
        self.is_active = not self.is_active


    def get_value(self):
        if self.txt == '':
            return 0
        return int(self.txt)


    def draw(self):
        if self.is_active:
            self.bg = (255, 255, 255)
        else:
            self.bg = (150, 150, 150)

        self.surface.fill(self.bg)
        self.surface.blit(self.txt_surf, self.txt_rect)
        self.screen.blit(self.surface, self.rect)


    def update(self, button):
        if not self.is_active:
            return
        if button == pygame.K_0:
            self.txt += '0'
        elif button == pygame.K_1:
            self.txt += '1'
        elif button == pygame.K_2:
            self.txt += '2'
        elif button == pygame.K_3:
            self.txt += '3'
        elif button == pygame.K_4:
            self.txt += '4'
        elif button == pygame.K_5:
            self.txt += '5'
        elif button == pygame.K_6:
            self.txt += '6'
        elif button == pygame.K_7:
            self.txt += '7'
        elif button == pygame.K_8:
            self.txt += '8'
        elif button == pygame.K_9:
            self.txt += '9'
        elif button == pygame.K_BACKSPACE:
            self.txt = self.txt[:-1]

        self.txt_surf = self.font.render(self.txt, 1, (150, 150, 150))
        self.txt_rect = self.txt_surf.get_rect(center=([s // 2 for s in self.size]))
