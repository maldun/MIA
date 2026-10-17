# Backgrounds for the character

Put pictures (`.png`, `.jpg`, `.jpeg`, `.webp`) into this folder. MIA shows one of them behind the 3D character.

- The first picture (alphabetical) is shown at the start. To choose another one, set `"background_image":"room.jpg"` in `setup_cfg.json`.
- The picture is scaled to cover the whole view and cropped, not stretched. Landscape pictures of about 1920x1080 work well
  (pictures larger than 2048 pixels are scaled down by the character).
- In the character's menu (open it with `/character/?menu`) the row "Background" switches between the pictures; "none" shows the plain colour.
- Another folder: `"background_dir":"/path/to/pictures"` in `setup_cfg.json`.
- To reuse the picture of the chat page, set `"background_dir":"templates/static"` and `"background_image":"background.jpg"`
  (note: every picture in that folder is then offered).
- Changes in the folder are picked up when the page is reloaded.
