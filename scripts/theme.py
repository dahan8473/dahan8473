"""Shared window-frame spec so every panel reads as one terminal OS."""

RADIUS = 12

FRAME = {
    "dark": dict(
        bg="#0a0e14",        # panel background
        border="#22406a",    # blue-tinted window border
        bar="#111826",       # title-bar tint
        user="#58a6ff",      # prompt user@host
        dim="#6e7f95",       # punctuation / right label
        cmd="#e6edf3",       # command text
        accent="#58a6ff",
    ),
    "light": dict(
        bg="#ffffff",
        border="#d0d7de",
        bar="#f6f8fa",
        user="#0969da",
        dim="#57606a",
        cmd="#1f2328",
        accent="#0969da",
    ),
}
DOTS = ["#ff5f56", "#ffbd2e", "#27c93f"]
