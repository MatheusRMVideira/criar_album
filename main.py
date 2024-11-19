import math
import os
from typing import Tuple, List

import browser_cookie3
import pandas as pd
import requests
from PIL import Image, ImageStat, ImageFilter, ExifTags
from PIL import ImageDraw
from PIL.ImageFont import ImageFont, truetype, FreeTypeFont
import numpy as np

BACKGROUND_IMAGE = 'Modelo_Album_InterREP_A_Festa SEM NADA VERDADEIRO.png'
REP_FONT = 'TechnoRaceItalic-eZRWe.otf'
REP_FONT_SIZE = 75


def brightness(image):
    img_data = np.array(image)
    # Split the RGBA channels
    r, g, b, alpha = img_data[..., 0], img_data[..., 1], img_data[..., 2], img_data[..., 3]

    # Calculate brightness for each pixel (ignoring transparency for now)
    img_brightness = 0.299 * r + 0.587 * g + 0.114 * b

    visible_pixels = alpha > 0

    # Incorporate the alpha channel into brightness (scale brightness by alpha)
    img_brightness = img_brightness * (alpha / 255.0)

    img_brightness = img_brightness[visible_pixels]

    if img_brightness.size == 0:
        return 0

    # Calculate average brightness
    avg_brightness = np.mean(img_brightness)
    return avg_brightness


def create_shadow(image: Image, color: Tuple):
    img_data = np.array(image)
    shadow_data = np.zeros_like(img_data)
    shadow_data[..., 0] = color[0]
    shadow_data[..., 1] = color[1]
    shadow_data[..., 2] = color[2]
    shadow_data[..., 3] = img_data[..., 3]
    shadow_img = Image.fromarray(shadow_data, 'RGBA')
    return shadow_img


def draw_rep_name(background: Image, republic_name: str):
    area = (266, 27, 934, 142)
    background.paste((17, 17, 17), area)
    font = truetype(font=REP_FONT, size=REP_FONT_SIZE)
    text = (republic_name.
            replace('República', '').
            replace('Republica', '').
            replace('republica', '').
            strip())
    text_width = ImageDraw.Draw(background).textlength(text=text, font=font)
    text_height = REP_FONT_SIZE
    x = (area[0] + area[2] - text_width) / 2  # Centralizar em x
    y = (area[1] + area[3] - text_height) / 2  # Centralizar em y
    ImageDraw.Draw(background).text(xy=(x, y), text=text, fill=(255, 255, 255), font=font)
    return background


def draw_rep_logo(background: Image, republic_logo: Image):
    area = (2199, 117, 2199 + 609, 117 + 609)
    aspect_ratio = republic_logo.width / republic_logo.height
    new_height = area[3] - area[1]
    new_width = new_height * aspect_ratio
    republic_logo = republic_logo.resize(size=(int(new_width), int(new_height)), resample=Image.Resampling.LANCZOS)

    if republic_logo.mode != 'RGBA':
        republic_logo = republic_logo.convert('RGBA')

    background_to_effect = Image.new('RGBA', size=(background.width, background.height), color=(0, 0, 0, 0))

    x = area[0] + (area[2] - area[0] - republic_logo.width) // 2
    y = area[1] + (area[3] - area[1] - republic_logo.height) // 2

    if republic_logo.mode == 'RGBA':
        logo_brightness = brightness(republic_logo)
        if logo_brightness > 35:
            shadow_color = (0, 0, 0)
        else:
            shadow_color = (255, 255, 255)
        logo_shadow = create_shadow(republic_logo, shadow_color)
        background_to_effect.paste(logo_shadow,
                                   box=(x, y, x + republic_logo.width, y + republic_logo.height),
                                   mask=republic_logo.split()[3])
        background_to_effect = background_to_effect.filter(ImageFilter.GaussianBlur(radius=2))

        background_to_effect.paste(republic_logo,
                                   box=(x, y, x + republic_logo.width, y + republic_logo.height),
                                   mask=republic_logo.split()[3])
    else:
        background_to_effect.paste(republic_logo, box=(x, y, x + republic_logo.width, y + republic_logo.height))

    background.paste(background_to_effect, box=(0, 0, background.width, background.height),
                     mask=background_to_effect.split()[3])
    return background


def draw_player_image(background: Image, player_image: Image, image_shape: Tuple):
    frame_aspect_ratio = (image_shape[2] - image_shape[0]) / (image_shape[3] - image_shape[1])
    player_aspect_ratio = player_image.width / player_image.height

    if player_aspect_ratio < frame_aspect_ratio:
        new_width = image_shape[2] - image_shape[0]
        new_height = new_width / player_aspect_ratio
    else:
        new_height = image_shape[3] - image_shape[1]
        new_width = new_height * player_aspect_ratio

    resized_image = player_image.resize(size=(int(new_width), int(new_height)),
                                        resample=Image.Resampling.LANCZOS)

    if new_width > image_shape[2] - image_shape[0]:
        excess_width = new_width - (image_shape[2] - image_shape[0])
        resized_image = resized_image.crop((excess_width / 2, 0, new_width - excess_width / 2, new_height))
    if new_height > image_shape[3] - image_shape[1]:
        excess_height = new_height - (image_shape[3] - image_shape[1])
        resized_image = resized_image.crop((0, excess_height / 2, new_width, new_height - excess_height / 2))

    background.paste(resized_image, (image_shape[0], image_shape[1]))
    return background


def draw_player_name(background: Image, player_name: str, player_shape: Tuple):
    background.paste((17, 17, 17), player_shape)
    player_name = player_name.replace("\"", "(", 1).replace("\"", ")", 1)


def draw_players(background: Image, player_list: List):
    image_shape_list = [
        (260 + (575 * 0), 1011 + (656 * 0), 260 + (575 * 0) + 412, 1011 + (656 * 0) + 530),
        (260 + (575 * 1), 1011 + (656 * 0), 260 + (575 * 1) + 412, 1011 + (656 * 0) + 530),
        (260 + (575 * 2), 1011 + (656 * 0), 260 + (575 * 2) + 412, 1011 + (656 * 0) + 530),
        (260 + (575 * 3), 1011 + (656 * 0), 260 + (575 * 3) + 412, 1011 + (656 * 0) + 530),
        (260 + (575 * 4), 1011 + (656 * 0), 260 + (575 * 4) + 412, 1011 + (656 * 0) + 530),
        (260 + (575 * 5), 1011 + (656 * 0), 260 + (575 * 5) + 412, 1011 + (656 * 0) + 530),
        (260 + (575 * 6), 1011 + (656 * 0), 260 + (575 * 6) + 412, 1011 + (656 * 0) + 530),
        (260 + (575 * 7), 1011 + (656 * 0), 260 + (575 * 7) + 412, 1011 + (656 * 0) + 530),

        (260 + (575 * 0), 1011 + (656 * 1), 260 + (575 * 0) + 412, 1011 + (656 * 1) + 530),
        (260 + (575 * 1), 1011 + (656 * 1), 260 + (575 * 1) + 412, 1011 + (656 * 1) + 530),
        (260 + (575 * 2), 1011 + (656 * 1), 260 + (575 * 2) + 412, 1011 + (656 * 1) + 530),
        (260 + (575 * 3), 1011 + (656 * 1), 260 + (575 * 3) + 412, 1011 + (656 * 1) + 530),
        (260 + (575 * 4), 1011 + (656 * 1), 260 + (575 * 4) + 412, 1011 + (656 * 1) + 530),
        (260 + (575 * 5), 1011 + (656 * 1), 260 + (575 * 5) + 412, 1011 + (656 * 1) + 530),
        (260 + (575 * 6), 1011 + (656 * 1), 260 + (575 * 6) + 412, 1011 + (656 * 1) + 530),
        (260 + (575 * 7), 1011 + (656 * 1), 260 + (575 * 7) + 412, 1011 + (656 * 1) + 530),

        (260 + (575 * 2), 1011 + (656 * 2), 260 + (575 * 2) + 412, 1011 + (656 * 2) + 530),
        (260 + (575 * 3), 1011 + (656 * 2), 260 + (575 * 3) + 412, 1011 + (656 * 2) + 530),
        (260 + (575 * 4), 1011 + (656 * 2), 260 + (575 * 4) + 412, 1011 + (656 * 2) + 530),
        (260 + (575 * 5), 1011 + (656 * 2), 260 + (575 * 5) + 412, 1011 + (656 * 2) + 530),
    ]
    for i, player in enumerate(player_list):
        player_image = player['image']
        player_image_pos = image_shape_list[i]

        background = draw_player_image(background, player_image, image_shape=player_image_pos)

    return background

def main():
    original_background = Image.open(BACKGROUND_IMAGE)
    if not os.path.isdir('forms'):
        os.mkdir('forms')
    if not os.path.isdir('photos'):
        os.mkdir('photos')
    if not os.path.isdir('output'):
        os.mkdir('output')
    forms = os.listdir('forms')
    for form in forms:
        df = pd.read_excel(f'forms/{form}')
        for i, row in df.iterrows():
            rep_name = row['Nome da República']
            # if f'{rep_name}.png' in os.listdir('output'):
            #     continue
            background = original_background.copy()
            # background_with_rep = draw_rep_logo(background=background,
            #                                     republic_logo=Image.open('Logo Open Beach.png'))
            cookiejar = browser_cookie3.firefox(domain_name='jotform.com')
            player_list = []
            for col in df.columns:
                if not pd.isna(row[col]) and 'http' in row[col]:
                    file_name = f'photos/{rep_name}+{col}.png'
                    if f'{rep_name}+{col}.png' not in os.listdir('photos'):
                        print(f'baixando foto {file_name}', flush=True)
                        response = requests.get(row[col], cookies=cookiejar)
                        with open(file_name, 'wb') as f:
                            f.write(response.content)
                    image = Image.open(file_name)
                    exif = image._getexif()
                    if exif:
                        exif_dict = {
                            ExifTags.TAGS[k]: v
                            for k, v in exif.items()
                            if k in ExifTags.TAGS
                        }

                        orientation = exif_dict.get("Orientation")
                        if orientation:
                            orientation_actions = {
                                3: 180,
                                6: 270,
                                8: 90
                            }
                            if orientation in orientation_actions:
                                image = image.rotate(orientation_actions[orientation], expand=True)
                    player_list.append({'image': image})

            background_with_player = draw_players(background, player_list=player_list)
            background_with_player.save(f'output/{rep_name}.png')
            print('a')


if __name__ == '__main__':
    main()
