---
id: lGHrHQz_7Fk
title: generating color palettes with matugen
description: Automatically generating color palettes from wallpapers using matugen + awww
author: Darius
visibility: public
created: 2026-03-27T11:31:30+00:00
---

When browsing forums related to Linux ricing, there is always one common denominator: a color palette which perfectly matches the background image.

![A screenshot depicting a Linux desktop rice](https://preview.redd.it/hyprland-finally-switched-to-matugen-v0-uz0v23ehf1jg1.jpg?width=1080&crop=smart&auto=webp&s=023aae9c598dd11a0e458a293355f8e2f0b733a7)

[Image Source](https://www.reddit.com/r/unixporn/comments/1r2plzm/hyprland_finally_switched_to_matugen/)

Traditionally, the tool to achieve this was [pywal](https://github.com/dylanaraps/pywal), but it is now discontinued and replaced by several alternatives such as [Wallust](https://codeberg.org/explosion-mental/wallust) or [Matugen](https://github.com/InioX/matugen). Personally I use Matugen because I prefer its outputs over other tools.

## Basics of color palette generation

All color palette tools work similarly: your background image (or set of colors/a static color) is your input, and as an output you receive a color palette which can be used for various programs. This is usually paired with templates for each software, where placeholders get replaced by the colors of your generated palette.

For matugen, this can be done using following command:

```
matugen image /path/to/img
```

Assuming you have templates set up in your config, this should output them to their respective paths. While this works, the main caveat is that every time you switch your wallpaper, you have to run this command again.

One integration which I found particularly nice was the template for the application launcher I use, [Vicinae](https://github.com/vicinaehq/vicinae). It has a whole [section in the docs](https://docs.vicinae.com/theming/matugen) explaining how to integrate Matugen, which is quite nice.

## Automating color generation

So the next step in your perfect color-matched setup is automating the process, i.e. switching your wallpaper automatically updates your generated color palette for all apps.

In my case, I am using [Waypaper](https://github.com/anufrievroman/waypaper) to switch wallpapers in combination with [awww](https://codeberg.org/LGFae/awww) as my wallpaper daemon.

To execute something after changing the wallpaper in Waypaper, you can add a command to the `post_command` option in the `config.ini`:

```bash
matugen image $(awww query | sed 's/.*image: //') \
  -m dark --source-color-index 0
```

Because this command is composed of quite a few pieces, lets dissect it:

- As explained above, matugen image generates the color palette
- The next part is a nested call to awww, my wallpaper daemon. The query command returns some info about the currently set wallpaper, and using sed I filter just for the file path, which we can then pass to matugen.
- Lastly, we specify that we want a dark color scheme and pick the most dominant color (index 0) from our image for generating the color palette.

And that's it! Now when switching the background image in Waypaper, all programs that have templates configured automatically update their colors. In some cases, they don't have hot reload so you have to restart them (but there are workarounds for certain applications).
