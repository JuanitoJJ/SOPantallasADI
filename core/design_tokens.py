from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeTokens:
    id: str
    name: str
    description: str

    surface_base: str
    surface_raised: str
    surface_overlay: str
    surface_inverse: str

    text_primary: str
    text_secondary: str
    text_muted: str
    text_on_accent: str

    border_subtle: str
    border_strong: str
    border_focus: str

    accent: str
    accent_hover: str
    accent_pressed: str
    success: str
    warning: str
    danger: str
    info: str
    meeting: str

    room_free: str
    room_imminent: str
    room_occupied: str

    control_radius: int
    card_radius: int
    dialog_radius: int
    button_min_height: int
    input_min_height: int

    font_family_display: str
    font_family_body: str
    font_family_mono: str

    type_display: int
    type_3xl: int
    type_2xl: int
    type_xl: int
    type_lg: int
    type_md: int
    type_sm: int
    type_xs: int

    weight_regular: int
    weight_semibold: int
    weight_bold: int

    space_1: int
    space_2: int
    space_3: int
    space_4: int
    space_5: int
    space_6: int
    space_7: int

    motion_fast_ms: int
    motion_medium_ms: int
    motion_slow_ms: int


THEME_DARK = "dark"
THEME_LIGHT = "light"
THEME_HIGH_CONTRAST = "high_contrast"


DARK = ThemeTokens(
    id=THEME_DARK,
    name="Oscuro",
    description="Slate cálido con acento ámbar — sala nocturna",
    surface_base="#161A22",
    surface_raised="#1F2530",
    surface_overlay="#2A3140",
    surface_inverse="#EDE7DC",
    text_primary="#EDE7DC",
    text_secondary="#A7AEB9",
    text_muted="#6C7585",
    text_on_accent="#161A22",
    border_subtle="rgba(255, 255, 255, 0.08)",
    border_strong="rgba(255, 255, 255, 0.18)",
    border_focus="#D9A55D",
    accent="#D9A55D",
    accent_hover="#E5B36E",
    accent_pressed="#BE8D44",
    success="#7FB069",
    warning="#E2B04A",
    danger="#D96C5B",
    info="#7A9CC6",
    meeting="#8E7CC3",
    room_free="#7FB069",
    room_imminent="#E2B04A",
    room_occupied="#8E7CC3",
    control_radius=8,
    card_radius=12,
    dialog_radius=16,
    button_min_height=56,
    input_min_height=48,
    font_family_display="Segoe UI Variable Display",
    font_family_body="Segoe UI Variable Text",
    font_family_mono="Cascadia Mono",
    type_display=120,
    type_3xl=64,
    type_2xl=40,
    type_xl=28,
    type_lg=20,
    type_md=16,
    type_sm=14,
    type_xs=12,
    weight_regular=400,
    weight_semibold=600,
    weight_bold=700,
    space_1=4,
    space_2=8,
    space_3=12,
    space_4=16,
    space_5=24,
    space_6=32,
    space_7=48,
    motion_fast_ms=150,
    motion_medium_ms=280,
    motion_slow_ms=500,
)


LIGHT = ThemeTokens(
    id=THEME_LIGHT,
    name="Claro",
    description="Warm-paper con acento ámbar profundo — sala diurna",
    surface_base="#F4EFE6",
    surface_raised="#FBF7F0",
    surface_overlay="#FFFFFF",
    surface_inverse="#1F2530",
    text_primary="#1F2530",
    text_secondary="#4A5260",
    text_muted="#8A8E97",
    text_on_accent="#FBF7F0",
    border_subtle="rgba(31, 37, 48, 0.10)",
    border_strong="rgba(31, 37, 48, 0.22)",
    border_focus="#B07A2E",
    accent="#B07A2E",
    accent_hover="#C68B3D",
    accent_pressed="#956321",
    success="#5C8A4A",
    warning="#B88A2A",
    danger="#B55344",
    info="#4F6E91",
    meeting="#6F5FA0",
    room_free="#5C8A4A",
    room_imminent="#B88A2A",
    room_occupied="#6F5FA0",
    control_radius=8,
    card_radius=12,
    dialog_radius=16,
    button_min_height=56,
    input_min_height=48,
    font_family_display="Segoe UI Variable Display",
    font_family_body="Segoe UI Variable Text",
    font_family_mono="Cascadia Mono",
    type_display=120,
    type_3xl=64,
    type_2xl=40,
    type_xl=28,
    type_lg=20,
    type_md=16,
    type_sm=14,
    type_xs=12,
    weight_regular=400,
    weight_semibold=600,
    weight_bold=700,
    space_1=4,
    space_2=8,
    space_3=12,
    space_4=16,
    space_5=24,
    space_6=32,
    space_7=48,
    motion_fast_ms=150,
    motion_medium_ms=280,
    motion_slow_ms=500,
)


HIGH_CONTRAST = ThemeTokens(
    id=THEME_HIGH_CONTRAST,
    name="Alto Contraste",
    description="Negro absoluto con amarillo WCAG AAA — accesibilidad",
    surface_base="#000000",
    surface_raised="#0A0A0A",
    surface_overlay="#141414",
    surface_inverse="#FFFFFF",
    text_primary="#FFFFFF",
    text_secondary="#FFFFFF",
    text_muted="#FFD400",
    text_on_accent="#000000",
    border_subtle="#FFFFFF",
    border_strong="#FFFFFF",
    border_focus="#FFD400",
    accent="#FFD400",
    accent_hover="#FFE340",
    accent_pressed="#CCAA00",
    success="#00FF66",
    warning="#FFD400",
    danger="#FF4040",
    info="#00CCFF",
    meeting="#FF66CC",
    room_free="#00FF66",
    room_imminent="#FFD400",
    room_occupied="#FF66CC",
    control_radius=2,
    card_radius=4,
    dialog_radius=4,
    button_min_height=56,
    input_min_height=48,
    font_family_display="Segoe UI",
    font_family_body="Segoe UI",
    font_family_mono="Consolas",
    type_display=130,
    type_3xl=64,
    type_2xl=40,
    type_xl=30,
    type_lg=20,
    type_md=16,
    type_sm=14,
    type_xs=12,
    weight_regular=400,
    weight_semibold=600,
    weight_bold=700,
    space_1=4,
    space_2=8,
    space_3=12,
    space_4=16,
    space_5=24,
    space_6=32,
    space_7=48,
    motion_fast_ms=150,
    motion_medium_ms=280,
    motion_slow_ms=500,
)


THEMES: dict = {
    THEME_DARK: DARK,
    THEME_LIGHT: LIGHT,
    THEME_HIGH_CONTRAST: HIGH_CONTRAST,
}


DEFAULT_THEME = THEME_DARK


def get_tokens(theme_id: str) -> ThemeTokens:
    return THEMES.get(theme_id, DARK)


def get_default_tokens() -> ThemeTokens:
    return DARK
