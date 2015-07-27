import pygame
from PIL import Image
from PIL import ImageChops

BLACK = 0, 0, 0

class projector:
    ###########################################################################
    ##
    #   Initializes the projector
    ##
    ###########################################################################
    def __init__(self):
        pygame.init()
        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        self.screen = pygame.display.set_mode(size)

        # Hide the mouse cursor
        pygame.mouse.set_visible(False)

        # Get the vignette image
        self.vignette = Image.open('vignette.png')

    ###########################################################################
    ##
    #   Displays a black screen
    ##
    ###########################################################################
    def black(self):
        self.screen.fill(BLACK)
        pygame.display.flip()

    ###########################################################################
    ##
    #   Displays a white screen
    ##
    ###########################################################################
    def value(self,gray_value):
        color = (gray_value,gray_value,gray_value)
        self.screen.fill(color)
        pygame.display.flip()

    ###########################################################################
    ##
    #   Displays an image on the projector with an applied vignette inverse
    #
    #   @param  image       Path to image
    ##
    ###########################################################################
    def display(self, image_path):

        slice_pil_image = Image.open(image_path)
        slice_vig_image = ImageChops.darker(slice_pil_image,self.vignette)

        #slice_image = pygame.image.load(image_path)
        slice_image = pygame.image.fromstring(slice_vig_image.tostring(),slice_vig_image.size,slice_vig_image.mode)
        slice_rect = slice_image.get_rect()

        self.screen.fill(BLACK)
        self.screen.blit(slice_image, slice_rect)
        pygame.display.flip()


    ###########################################################################
    ##
    #   Displays an image on the projector
    #
    #   @param  image       Path to image
    ##
    ###########################################################################
    def image(self, image_path):
        slice_image = pygame.image.load(image_path)
        slice_rect = slice_image.get_rect()

        self.screen.fill(BLACK)
        self.screen.blit(slice_image, slice_rect)
        pygame.display.flip()

    ###########################################################################
    ##
    #   Shutsdown the projector
    ##
    ###########################################################################
    def shutdown(self):
        pygame.quit()
