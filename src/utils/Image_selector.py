import random


class ImageSelector:
    def __init__(self, images):
        self.images = images
        self.remaining_images = []

    def get_random_image(self):
        if not self.remaining_images:
            self.remaining_images = self.images.copy()
            random.shuffle(self.remaining_images)
        return self.remaining_images.pop()
